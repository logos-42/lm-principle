"""E12 判定实验: 反向传播 vs 无梯度方法的每 FLOP 失真下降 (L7, CPU)

动机 (2026-10-20):
  L7: 标量失真目标 + 巨大参数数 ⟹ 逆模式自动微分是渐近最优的梯度计算
  （Griewank 界: 逆模式 ≤ 4× 前向 vs 顺模式 ~ n× 前向）。E12 是这条的
  实验面孔: 同一目标、同一 wall-clock 预算下, 比较
    ① Adam（逆模式）——每步 1 前向 + 1 反向 ≈ 3 前向 FLOP 当量
    ② 进化策略 ES（antithetic, K=16）——每步 16 前向 FLOP, 零反向
    ③ 随机爬山（保留 K 个扰动中最好的）——每步 K 前向 FLOP
  预测: 单位 FLOP 的失真下降, 逆模式领先 1-2 个数量级。

E12 设计:
  - 模型: 极小 CharLM (dim=24, 2 层), 同数据同步数
  - 预算: 每方法 20 秒 wall-clock, 探针批次逐点记录 loss
  - 公平性: ES/爬山先做 4 秒超参扫描取最优, 再跑完整预算
  - FLOP 记账: 前向当量 (Adam 每步记 3: 1 前向 + 反向 ≈ 2 前向)

输出: scripts/experiments_e12_results.txt + experiments/results/e12_backprop.json
"""
import os, re, glob, json, time
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

class TinyCharLM(nn.Module):
    def __init__(self, vocab, dim=24, heads=4, n_layers=2):
        super().__init__()
        self.embed = nn.Embedding(vocab, dim)
        self.layers = nn.ModuleList()
        self.ffs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, heads, batch_first=True))
            self.ffs.append(nn.Sequential(nn.Linear(dim, 4*dim), nn.ReLU(), nn.Linear(4*dim, dim)))
            self.norms.append(nn.LayerNorm(dim))
        self.exit = nn.Linear(dim, vocab)

    def forward(self, x):
        h = self.embed(x)
        for l, ff, nm in zip(self.layers, self.ffs, self.norms):
            a, _ = l(h, h, h)
            h = nm(h + a)
            h = h + ff(h)
        return self.exit(h)

def make_batch_fn(data, split, seq=64, bs=16):
    X = torch.from_numpy(data)
    def make():
        ix = torch.randint(0, split - seq, (bs,))
        xb = torch.stack([X[i:i+seq] for i in ix])
        yb = torch.stack([X[i+1:i+seq+1] for i in ix])
        return xb, yb
    return make

def eval_loss(model, xb, yb, vocab):
    with torch.no_grad():
        return nn.functional.cross_entropy(
            model(xb).reshape(-1, vocab), yb.reshape(-1)).item()

def run_adam(model, make, xb0, yb0, vocab, budget):
    """逆模式: 返回 (loss 轨迹, 前向次数)。"""
    opt = optim.Adam(model.parameters(), lr=3e-3)
    crit = nn.CrossEntropyLoss()
    trace, t0 = [], time.time()
    fwd = 0
    while time.time() - t0 < budget:
        xb, yb = make()
        opt.zero_grad()
        loss = crit(model(xb).reshape(-1, vocab), yb.reshape(-1))
        loss.backward()
        opt.step()
        fwd += 1
        trace.append(eval_loss(model, xb0, yb0, vocab))
    return trace, fwd

def _set_flat(params, flat):
    idx = 0
    for p in params:
        m = p.numel()
        p.data.copy_(flat[idx:idx+m].reshape(p.shape))
        idx += m

def run_es(model, make, xb0, yb0, vocab, budget, lr, sigma, K=16):
    """进化策略 (antithetic): θ ← θ − lr·ĝ, ĝ = (1/(Kσ²))Σ[L(θ+σε)−L(θ−σε)]ε。"""
    params = [p for p in model.parameters()]
    flat = torch.cat([p.data.reshape(-1) for p in params]).clone()
    n = flat.numel()
    trace, t0 = [], time.time()
    fwd = 0
    while time.time() - t0 < budget:
        eps = torch.randn(K // 2, n)
        g = torch.zeros(n)
        for k in range(K // 2):
            for sgn in (1, -1):
                _set_flat(params, flat + sgn * sigma * eps[k])
                xb, yb = make()
                L = eval_loss(model, xb, yb, vocab)
                g += sgn * L * eps[k]
                fwd += 1
        g = g / (K * sigma)
        flat = flat - lr * g
        _set_flat(params, flat)
        trace.append(eval_loss(model, xb0, yb0, vocab))
    return trace, fwd

def run_hillclimb(model, make, xb0, yb0, vocab, budget, sigma, K=16):
    """随机爬山: K 个高斯扰动中保留 loss 最低者 (不退则保持)。"""
    params = [p for p in model.parameters()]
    flat = torch.cat([p.data.reshape(-1) for p in params]).clone()
    n = flat.numel()
    best = eval_loss(model, xb0, yb0, vocab)
    trace, t0 = [], time.time()
    fwd = 0
    while time.time() - t0 < budget:
        cands = []
        for _ in range(K):
            delta = torch.randn(n) * sigma
            _set_flat(params, flat + delta)
            xb, yb = make()
            cands.append((eval_loss(model, xb, yb, vocab), delta))
            fwd += 1
        cands.sort(key=lambda t: t[0])
        if cands[0][0] < best:
            best = cands[0][0]
            flat = flat + cands[0][1]
        _set_flat(params, flat)
        trace.append(best)
    return trace, fwd

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
    make = make_batch_fn(data, split)
    X = torch.from_numpy(data)
    xb0 = X[split:split+64].unsqueeze(0)
    yb0 = X[split+1:split+1+64].unsqueeze(0)

    p("=" * 74)
    p(f"E12: 逆模式 vs 无梯度 (vocab={vocab}, dim=24, 2 层, 每方法 20s 预算)")
    p("=" * 74)

    torch.manual_seed(0)
    m0 = TinyCharLM(vocab)
    n_params = sum(q.numel() for q in m0.parameters())
    p(f"  参数数 N = {n_params}")

    BUDGET = 20.0

    # ① Adam (逆模式)
    torch.manual_seed(0)
    m = TinyCharLM(vocab)
    l0 = eval_loss(m, xb0, yb0, vocab)
    trace_a, fwd_a = run_adam(m, make, xb0, yb0, vocab, BUDGET)
    p(f"  ① Adam(逆模式): 起始 {l0:.4f} → 末 {trace_a[-1]:.4f} "
      f"(降 {l0-trace_a[-1]:.4f}), 前向 {fwd_a} 次, 步数 {len(trace_a)}")

    # ② ES: 4 秒 lr 扫描后跑完整预算
    best_cfg, best_final = None, 1e9
    for lr in [1e-3, 1e-2, 1e-1]:
        torch.manual_seed(0)
        m = TinyCharLM(vocab)
        tr, _ = run_es(m, make, xb0, yb0, vocab, 4.0, lr, sigma=1e-2)
        p(f"    ES lr={lr:g}: 4s 后 loss = {tr[-1]:.4f}")
        if tr[-1] < best_final:
            best_final, best_cfg = tr[-1], lr
    p(f"    ES 最优 lr = {best_cfg:g}")
    torch.manual_seed(0)
    m = TinyCharLM(vocab)
    l0 = eval_loss(m, xb0, yb0, vocab)
    trace_e, fwd_e = run_es(m, make, xb0, yb0, vocab, BUDGET, best_cfg, sigma=1e-2)
    p(f"  ② ES(K=16): 起始 {l0:.4f} → 末 {trace_e[-1]:.4f} "
      f"(降 {l0-trace_e[-1]:.4f}), 前向 {fwd_e} 次, 代数 {len(trace_e)}")

    # ③ 爬山: σ 扫描后跑完整预算
    best_sig, best_final = None, 1e9
    for sig in [1e-3, 1e-2]:
        torch.manual_seed(0)
        m = TinyCharLM(vocab)
        tr, _ = run_hillclimb(m, make, xb0, yb0, vocab, 4.0, sig)
        p(f"    爬山 σ={sig:g}: 4s 后 loss = {tr[-1]:.4f}")
        if tr[-1] < best_final:
            best_final, best_sig = tr[-1], sig
    torch.manual_seed(0)
    m = TinyCharLM(vocab)
    l0 = eval_loss(m, xb0, yb0, vocab)
    trace_h, fwd_h = run_hillclimb(m, make, xb0, yb0, vocab, BUDGET, best_sig)
    p(f"  ③ 爬山(K=16): 起始 {l0:.4f} → 末 {trace_h[-1]:.4f} "
      f"(降 {l0-trace_h[-1]:.4f}), 前向 {fwd_h} 次, 代数 {len(trace_h)}")

    p("")
    p("--- 每前向当量的失真下降 ---")
    drop_a = trace_a[-1] - trace_a[0]
    drop_e = trace_e[-1] - trace_e[0]
    drop_h = trace_h[-1] - trace_h[0]
    eff_a = drop_a / (fwd_a * 3)   # Adam 每步记 3 前向当量
    eff_e = drop_e / fwd_e
    eff_h = drop_h / fwd_h
    p(f"  Adam : Δloss={drop_a:+.4f} / {fwd_a*3} 当量 = {eff_a:+.3e}")
    p(f"  ES   : Δloss={drop_e:+.4f} / {fwd_e} 当量 = {eff_e:+.3e}")
    p(f"  爬山 : Δloss={drop_h:+.4f} / {fwd_h} 当量 = {eff_h:+.3e}")
    ratio = eff_a / eff_e if eff_e != 0 else float("inf")
    p(f"  逆模式 / ES 的每 FLOP 效率比 = {ratio:.1f}×")

    if ratio > 10:
        verdict = "支持 L7: 逆模式每 FLOP 失真下降领先无梯度方法一个数量级以上"
    elif ratio > 3:
        verdict = "方向支持: 逆模式明显更优但差距不到一个数量级"
    else:
        verdict = "差距不显著 (极小模型 + 短预算下记录中性结果)"
    p(f"  判定: {verdict}")

    p("")
    p("诚实边界: 极小模型 (N~8 万) 上 ES 本应有竞争力——观测差距应视为下界;")
    p("  wall-clock 预算含 Python 开销, 前向当量是粗估; Griewank 界的渐近陈述")
    p("  (n→∞) 无法在小模型上直接检验, 本实验只测方向与量级。")

    R["n_params"] = n_params
    R["adam"] = {"final": trace_a[-1], "drop": drop_a, "fwd": fwd_a,
                 "steps": len(trace_a), "trace": trace_a[::max(1, len(trace_a)//20)]}
    R["es"] = {"final": trace_e[-1], "drop": drop_e, "fwd": fwd_e,
               "steps": len(trace_e), "trace": trace_e[::max(1, len(trace_e)//20)],
               "best_lr": best_cfg}
    R["hillclimb"] = {"final": trace_h[-1], "drop": drop_h, "fwd": fwd_h,
                      "steps": len(trace_h), "trace": trace_h[::max(1, len(trace_h)//20)],
                      "best_sigma": best_sig}
    R["efficiency"] = {"adam": eff_a, "es": eff_e, "hillclimb": eff_h, "ratio": ratio}
    R["verdict"] = verdict

    with open(os.path.join(OUT, "experiments_e12_results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    os.makedirs(os.path.join(ROOT, "experiments", "results"), exist_ok=True)
    with open(os.path.join(ROOT, "experiments", "results", "e12_backprop.json"), "w") as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    p("\n结果已写入 scripts/experiments_e12_results.txt + experiments/results/e12_backprop.json")

if __name__ == "__main__":
    main()
