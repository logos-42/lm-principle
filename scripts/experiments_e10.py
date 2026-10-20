"""E10 判定实验: 注意力温度-深度退火 (认知动力学 L6, CPU)

动机 (2026-10-20):
  L6: softmax 是率受限下每比特期望分值最大的选择算子; 温度 = 比特旋钮
  (花多少比特换多少期望分值)。预测: 训练后的网络中, **温度随深度退火**——
  浅层高熵 (探索, 广候选), 深层低熵 (利用, 集中选择), 且 β_eff 峰值层与
  能量/loss 下降层重合 (Hopfield E5 的弱观察)。

E10 设计:
  - 模型: 深度监督 CharLM 12 层 (dim=64, heads=4), 3 seeds, 300 步
  - 探针: 训练后固定批次逐层手算 attention scores, 测
    ① β_eff = 平均 logit spread (得分极差, E5 同定义)
    ② 注意力熵 H(α) (nats, 按 log(seq) 归一化)
  - 判定:
    ① β_eff 随深度单调/近单调上升 (退火的定量形式)
    ② H(α) 随深度下降 (归一化熵 → 0)
    ③ β_eff 峰值层 vs Δ_k = L(k−1) − L(k) 最大层的重合度
    ④ 跨 seed 稳健性

输出: scripts/experiments_e10_results.txt + experiments/results/e10_annealing.json
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

class DeepSupervisedCharLM(nn.Module):
    def __init__(self, vocab, dim=64, heads=4, n_layers=12):
        super().__init__()
        self.embed = nn.Embedding(vocab, dim)
        self.layers = nn.ModuleList()
        self.ffs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, heads, batch_first=True))
            self.ffs.append(nn.Sequential(nn.Linear(dim, 4*dim), nn.ReLU(), nn.Linear(4*dim, dim)))
            self.norms.append(nn.LayerNorm(dim))
        self.exits = nn.ModuleList([nn.Linear(dim, vocab) for _ in range(n_layers)])

    def forward_exits(self, x):
        h = self.embed(x)
        outs = []
        for l, ff, nm, ex in zip(self.layers, self.ffs, self.norms, self.exits):
            a, _ = l(h, h, h)
            h = nm(h + a)
            h = h + ff(h)
            outs.append(ex(h))
        return outs

def train(data, split, vocab, seed, steps=300, seq=64, bs=16, lr=3e-3):
    torch.manual_seed(seed)
    model = DeepSupervisedCharLM(vocab)
    opt = optim.Adam(model.parameters(), lr=lr)
    crit = nn.CrossEntropyLoss()
    X = torch.from_numpy(data)
    for _ in range(steps):
        opt.zero_grad()
        ix = torch.randint(0, split - seq, (bs,))
        xb = torch.stack([X[i:i+seq] for i in ix])
        yb = torch.stack([X[i+1:i+seq+1] for i in ix])
        outs = model.forward_exits(xb)
        loss = torch.stack([crit(o.reshape(-1, vocab), yb.reshape(-1)) for o in outs]).mean()
        loss.backward()
        opt.step()
    with torch.no_grad():
        xb = torch.from_numpy(data[split:split+seq]).unsqueeze(0)
        yb = torch.from_numpy(data[split+1:split+seq+1]).unsqueeze(0)
        outs = model.forward_exits(xb)
        losses = [crit(o.reshape(-1, vocab), yb.reshape(-1)).item() for o in outs]
    return model, losses

def probe_attention(model, xb):
    """逐层手算 attention: 返回每层 (β_eff logit spread, 归一化熵)。"""
    d = model.embed.embedding_dim
    beta_effs, ents = [], []
    with torch.no_grad():
        h = model.embed(xb)
        for l in model.layers:
            qkv = torch.nn.functional.linear(h, l.in_proj_weight, l.in_proj_bias)
            q, k, _ = torch.chunk(qkv, 3, dim=-1)
            scores = (q @ k.transpose(-1, -2)) / (d ** 0.5)      # (B, T, T)
            spread = (scores.max(-1).values - scores.min(-1).values).mean().item()
            A = torch.softmax(scores, dim=-1)
            H = -(A * torch.log(A + 1e-12)).sum(-1).mean().item()  # nats
            beta_effs.append(spread)
            ents.append(H / np.log(scores.size(-1)))               # 归一化熵
            a = l(h, h, h, need_weights=False)[0]
            h = model.norms[len(beta_effs) - 1](h + a)
            h = h + model.ffs[len(beta_effs) - 1](h)
    return beta_effs, ents

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
    p(f"E10: 注意力温度-深度退火 (vocab={vocab}, 12 层 dim=64, 3 seeds)")
    p("=" * 74)

    all_beta, all_ent, all_loss = [], [], []
    for seed in range(3):
        model, losses = train(data, split, vocab, seed)
        xb = torch.from_numpy(data[split:split+64]).unsqueeze(0)
        beta, ent = probe_attention(model, xb)
        all_beta.append(beta); all_ent.append(ent); all_loss.append(losses)
        p(f"  seed{seed} β_eff = {[f'{v:.2f}' for v in beta]}")
        p(f"         归一化熵 = {[f'{v:.3f}' for v in ent]}")
        p(f"         exit loss = {[f'{v:.3f}' for v in losses]}")

    B = np.mean(all_beta, axis=0); E = np.mean(all_ent, axis=0)
    Lm = np.mean(all_loss, axis=0)
    Lfull = np.concatenate([[np.log(vocab)], Lm])
    Delta = [Lfull[k] - Lfull[k+1] for k in range(len(Lfull)-1)]

    p("")
    p("--- 平均 (3 seeds) ---")
    p("  层 k | β_eff | 归一化熵 | exit loss | Δ_k")
    for k in range(12):
        p(f"  {k+1:4d} | {B[k]:6.2f} | {E[k]:8.3f} | {Lm[k]:9.3f} | {Delta[k]:+.4f}")

    # ① β_eff 单调性 (Spearman)
    def spearman(x, y):
        rx = np.argsort(np.argsort(x)).astype(float)
        ry = np.argsort(np.argsort(y)).astype(float)
        rx -= rx.mean(); ry -= ry.mean()
        return float((rx*ry).sum() / np.sqrt((rx**2).sum() * (ry**2).sum()))
    rho_b = spearman(np.arange(1, 13), B)
    rho_e = spearman(np.arange(1, 13), E)
    p("")
    p(f"  ① Spearman(深度, β_eff) = {rho_b:+.3f}  (正 = 随深度更集中)")
    p(f"  ② Spearman(深度, 归一化熵) = {rho_e:+.3f}  (负 = 随深度退火)")

    # ③ β_eff 峰值层 vs Δ_k 峰值层
    k_beta = int(np.argmax(B)) + 1
    k_delta = int(np.argmax(Delta[1:])) + 1
    p(f"  ③ β_eff 峰值层 = {k_beta}, Δ_k 峰值层 = {k_delta}, 重合 = {k_beta == k_delta}")

    # ④ 跨 seed 稳健性: 每 seed 的 (深度, β_eff) Spearman
    rhos = [spearman(np.arange(1, 13), b) for b in all_beta]
    p(f"  ④ 各 seed 的 Spearman(深度, β_eff) = {[f'{r:+.2f}' for r in rhos]}")

    p("")
    verdict = "退火得到支持 (β_eff 随深度上升且跨 seed 稳健)" if rho_b > 0.5 and min(rhos) > 0.3 else \
              ("方向一致但不稳健" if rho_b > 0.2 else "未见退火 (记录负面/中性结果)")
    p(f"  判定: {verdict}")
    p("")
    p("诚实边界: 弱训练小模型; 探针为单批次; β_eff 是 spread 代理非真逆温度;")
    p("  E5 曾观察到'β_eff 峰值层与正能量下降层重合'——此处只查峰值层重合, 未做逐层相关。")

    R["beta_eff_mean"] = B.tolist(); R["entropy_mean"] = E.tolist()
    R["exit_loss_mean"] = Lm.tolist(); R["delta"] = Delta[1:]
    R["rho_depth_beta"] = rho_b; R["rho_depth_entropy"] = rho_e
    R["k_beta_peak"] = k_beta; R["k_delta_peak"] = k_delta
    R["verdict"] = verdict

    with open(os.path.join(OUT, "experiments_e10_results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    os.makedirs(os.path.join(ROOT, "experiments", "results"), exist_ok=True)
    with open(os.path.join(ROOT, "experiments", "results", "e10_annealing.json"), "w") as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    p("\n结果已写入 scripts/experiments_e10_results.txt + experiments/results/e10_annealing.json")

if __name__ == "__main__":
    main()
