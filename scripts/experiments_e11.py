"""E11 判定实验: 残差消融——恒等路径 = 惯性/平行移动 (认知动力学 L8, CPU)

动机 (2026-10-20):
  L8: 迭代压缩动力学中, 恒等/门控回馈是防坍缩 + 跨层可比较性的充要结构。
  已证内核: residual_no_collapse (距离 ≥ (1−c)^n), FFN 无恒等路径可坍缩。
  E11 做实验对照: 三种跳连 × 四个深度, 测
    ① loss 随深度的退化速度 (预测: 无跳连灾难性退化)
    ② 表征分离度 ||h(x1)−h(x2)||/(||h(x1)||+||h(x2)||) (预测: 无跳连随深度
       坍缩, plain/gated 保持——no-collapse 的实验面孔)
    ③ 门控居中 (可控惯性)

E11 设计:
  - 模型: CharLM 6→{2,4,6,8} 层, skip ∈ {none, plain, gated}
  - 3 变体 × 4 深度 × 2 seeds = 24 模型, 200 步
  - 探针: 两个固定批次的最终层隐态分离度 + test loss

输出: scripts/experiments_e11_results.txt + experiments/results/e11_residual.json
"""
import os, re, glob, json
import numpy as np
import torch, torch.nn as nn, torch.optim as optim

torch.set_num_threads(4)
OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, ".."))

def load_corpus():
    parts = []
    for pat in ["docs/wiki/*.md", "README.md", "README.zh.md", "AGENTS.md", "CLAUDE.md",
                "LmPrinciple/*.lean", "paper/*.tex"]:
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            try:
                t = open(f, encoding="utf-8", errors="ignore").read()
                t = re.sub(r"%.*", "", t)
                t = re.sub(r"\s+", " ", t)
                parts.append(t)
            except Exception:
                pass
    return " ".join(parts)[:200_000]

class ResCharLM(nn.Module):
    """skip ∈ {none: h←b (无回馈), plain: h←h+b (恒等), gated: h←h+α⊙b (门控)}"""
    def __init__(self, vocab, dim=64, heads=4, n_layers=6, skip="plain"):
        super().__init__()
        self.skip = skip
        self.embed = nn.Embedding(vocab, dim)
        self.layers = nn.ModuleList()
        self.ffs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, heads, batch_first=True))
            self.ffs.append(nn.Sequential(nn.Linear(dim, 4*dim), nn.ReLU(), nn.Linear(4*dim, dim)))
            self.norms.append(nn.LayerNorm(dim))
        if skip == "gated":
            self.alpha = nn.ParameterList(
                [nn.Parameter(torch.full((dim,), 0.5)) for _ in range(n_layers)])
        self.exit = nn.Linear(dim, vocab)

    def forward(self, x):
        h = self.embed(x)
        for i, (l, ff, nm) in enumerate(zip(self.layers, self.ffs, self.norms)):
            a, _ = l(h, h, h)
            b = ff(nm(h + a))
            if self.skip == "none":
                h = b
            elif self.skip == "plain":
                h = h + b
            else:
                h = h + torch.sigmoid(self.alpha[i]) * b
        return self.exit(h)

def train(data, split, vocab, seed, n_layers, skip, steps=200, seq=64, bs=16, lr=3e-3):
    torch.manual_seed(seed)
    model = ResCharLM(vocab, n_layers=n_layers, skip=skip)
    opt = optim.Adam(model.parameters(), lr=lr)
    crit = nn.CrossEntropyLoss()
    X = torch.from_numpy(data)
    for _ in range(steps):
        opt.zero_grad()
        ix = torch.randint(0, split - seq, (bs,))
        xb = torch.stack([X[i:i+seq] for i in ix])
        yb = torch.stack([X[i+1:i+seq+1] for i in ix])
        loss = crit(model(xb).reshape(-1, vocab), yb.reshape(-1))
        loss.backward()
        opt.step()
    with torch.no_grad():
        xb = torch.from_numpy(data[split:split+seq]).unsqueeze(0)
        yb = torch.from_numpy(data[split+1:split+seq+1]).unsqueeze(0)
        test_loss = crit(model(xb).reshape(-1, vocab), yb.reshape(-1)).item()
        # 表征分离度: 两个不同批次的最终隐态
        x1 = torch.from_numpy(data[split:split+seq]).unsqueeze(0)
        x2 = torch.from_numpy(data[split+500:split+500+seq]).unsqueeze(0)
        h1 = model.embed(x1); h2 = model.embed(x2)
        for i, (l, ff, nm) in enumerate(zip(model.layers, model.ffs, model.norms)):
            a1, _ = l(h1, h1, h1); b1 = ff(nm(h1 + a1))
            a2, _ = l(h2, h2, h2); b2 = ff(nm(h2 + a2))
            if model.skip == "none":
                h1, h2 = b1, b2
            elif model.skip == "plain":
                h1, h2 = h1 + b1, h2 + b2
            else:
                g = torch.sigmoid(model.alpha[i])
                h1, h2 = h1 + g * b1, h2 + g * b2
        sep = ((h1 - h2).norm() / (h1.norm() + h2.norm())).item()
    return test_loss, sep

def main():
    lines = []
    def p(s=""):
        print(s); lines.append(s)
    R = {}

    text = load_corpus()
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    vocab = len(chars)
    data = np.array([stoi[c] for c in text], dtype=np.int64)
    split = int(len(data) * 0.9)
    p("=" * 74)
    p(f"E11: 残差消融 (vocab={vocab}, 3 变体 × 深度 {{2,4,6,8}} × 2 seeds, 200 步)")
    p("=" * 74)

    depths = [2, 4, 6, 8]
    skips = ["none", "plain", "gated"]
    res = {}
    for skip in skips:
        for d in depths:
            for seed in range(2):
                loss, sep = train(data, split, vocab, seed, d, skip)
                res[(skip, d, seed)] = (loss, sep)
                p(f"  [{skip:5s} L={d} seed{seed}] loss={loss:.4f}  分离度={sep:.4f}")

    p("")
    p("--- 汇总 (2 seeds 平均) ---")
    p("  变体   | 深度 | loss   | 分离度 | loss 随深度退化斜率")
    slopes = {}
    for skip in skips:
        for d in depths:
            l = np.mean([res[(skip, d, s)][0] for s in range(2)])
            s_ = np.mean([res[(skip, d, s)][1] for s in range(2)])
            res[(skip, d, "avg")] = (l, s_)
            p(f"  {skip:5s}  | {d:4d} | {l:.4f} | {s_:.4f} |")
        xs = np.array(depths, dtype=float)
        for tag, idx in [("loss", 0), ("sep", 1)]:
            ys = np.array([res[(skip, d, "avg")][idx] for d in depths])
            sl, _ = np.polyfit(xs, ys, 1)
            slopes[(skip, tag)] = sl
        p(f"  {skip:5s} 斜率: loss {slopes[(skip,'loss')]:+.4f}/层, 分离度 {slopes[(skip,'sep')]:+.5f}/层")
        p("")

    p("--- 判定 ---")
    v_none = slopes[("none", "loss")]
    v_plain = slopes[("plain", "loss")]
    p(f"  无跳连 loss 斜率 = {v_none:+.4f}/层; plain = {v_plain:+.4f}/层")
    p(f"  无跳连分离度斜率 = {slopes[('none','sep')]:+.5f}/层; plain = {slopes[('plain','sep')]:+.5f}/层")
    if v_none > 0.05 and v_none > 3 * v_plain:
        verdict = "支持 L8: 无恒等路径随深度灾难退化, 有回馈则稳 (防坍缩的实验面孔)"
    elif v_none > v_plain:
        verdict = "方向支持: 无跳连退化更快, 但差距不显著"
    else:
        verdict = "未观测到差异 (弱训练小模型下记录中性/负面)"
    p(f"  判定: {verdict}")
    p(f"  门控居中检查: gated loss 斜率 = {slopes[('gated','loss')]:+.4f}/层 "
      f"(应介于 none 与 plain 之间或更优)")

    p("")
    p("诚实边界: 2 seeds + 200 步弱训练; 分离度是单对批次的代理; 'none' 变体")
    p("  仍有 LayerNorm, 坍缩度量是软性的。冒烟测试, 非验证/证伪。")

    R["slopes"] = {f"{k[0]}_{k[1]}": v for k, v in slopes.items()}
    R["grid"] = {f"{k[0]}_L{k[1]}_s{k[2]}": v for k, v in res.items()}
    R["verdict"] = verdict

    with open(os.path.join(OUT, "experiments_e11_results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    os.makedirs(os.path.join(ROOT, "experiments", "results"), exist_ok=True)
    with open(os.path.join(ROOT, "experiments", "results", "e11_residual.json"), "w") as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    p("\n结果已写入 scripts/experiments_e11_results.txt + experiments/results/e11_residual.json")

if __name__ == "__main__":
    main()
