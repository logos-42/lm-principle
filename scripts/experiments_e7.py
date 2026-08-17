"""E7 判定实验: Δ_k 递减性在真实 LM 任务上是否恢复? (零成本, 本机 CPU)

动机 (2026-08-17):
  日志"证伪"Δ_k 不严格递减 (5/11) 用的是合成线性任务
  y = 2·x1 + 1.5·x2 + noise —— 线性模型可精确求解 (loss=0.09=噪声下限)。
  该任务第一层饱和后加层全是噪声 ⟹ "Δ_k 不递减"可能是任务饱和伪影,
  而非深度收益的物理事实。
  E6 真实 LM 仅 4 层 / 1.5 万 token / 单 seed, 统计上无意义。

E7 设计:
  - 语料: wiki + README + LmPrinciple/*.lean + paper/*.tex (~31 万字符, 5× E6)
  - 模型: CharLM 12 层 (dim=64, heads=4), 深度监督 (每层 exit head)
  - 训练: next-char 交叉熵, 12 个 exit 平均 loss, 3 seeds
  - 判定: 逐层 test loss → Δ_k = L(k-1) - L(k) (L[0]=随机基线 log(vocab))
    递减一致性 = #(Δ_k ≥ Δ_{k+1}) / (n-1)。若真实任务上显著 > 50%
    (对比合成任务 45%) ⟹ 前提恢复, H100 实验值得做; 否则前提真伪存疑。

输出: scripts/experiments_e7_results.txt
"""
import os, re, glob, numpy as np
import torch, torch.nn as nn, torch.optim as optim

torch.set_num_threads(4)
OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, ".."))

# ---------------- 语料: 所有仓库文本 (比 E6 的 6 万字符大 5 倍) ----------------
def load_corpus():
    parts = []
    for pat in ["docs/wiki/*.md", "README.md", "LmPrinciple/*.lean", "paper/*.tex"]:
        for f in glob.glob(os.path.join(ROOT, pat)):
            try:
                t = open(f, encoding="utf-8", errors="ignore").read()
                t = re.sub(r"%.*", "", t)          # 去 LaTeX 注释
                t = re.sub(r"\s+", " ", t)
                parts.append(t)
            except Exception:
                pass
    text = " ".join(parts)
    return text[:200_000]                           # 截断到 20 万字符, 控制 CPU 时间

# ---------------- 深度监督 CharLM (同 experiments_v2 DeepSupervisedNet 结构) ----------------
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
        """x: (B, T) token ids → 每层 exit logits 列表 (B, T, V)"""
        h = self.embed(x)
        outs = []
        for l, ff, nm, ex in zip(self.layers, self.ffs, self.norms, self.exits):
            a, _ = l(h, h, h)
            h = nm(h + a)
            h = h + ff(h)
            outs.append(ex(h))
        return outs

def train(model, data, split, vocab, seq=96, bs=32, epochs=25, seed=0):
    torch.manual_seed(seed)
    opt = optim.Adam(model.parameters(), lr=0.001)
    crit = nn.CrossEntropyLoss()
    X = torch.from_numpy(data)
    for ep in range(epochs):
        opt.zero_grad()
        ix = torch.randint(0, split - seq, (bs,))
        xb = torch.stack([X[i:i+seq] for i in ix])
        yb = torch.stack([X[i+1:i+seq+1] for i in ix])
        outs = model.forward_exits(xb)
        loss = torch.stack([crit(o.reshape(-1, vocab), yb.reshape(-1)) for o in outs]).mean()
        loss.backward()
        opt.step()
    # 逐层 test loss
    with torch.no_grad():
        xb = torch.from_numpy(data[split:split+seq]).unsqueeze(0)
        yb = torch.from_numpy(data[split+1:split+seq+1]).unsqueeze(0)
        outs = model.forward_exits(xb)
        return [crit(o.reshape(-1, vocab), yb.reshape(-1)).item() for o in outs]

def main():
    lines = []
    def p(s=""):
        print(s); lines.append(s)

    text = load_corpus()
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    data = np.array([stoi[c] for c in text], dtype=np.int64)
    vocab = len(chars)
    split = int(len(data) * 0.9)
    random_loss = np.log(vocab)
    p("=" * 74)
    p(f"E7 判定实验: Δ_k 递减性在真实 LM 上是否恢复? (语料 {len(text)/1e3:.0f}K 字符, vocab={vocab})")
    p("=" * 74)
    p(f"随机基线 loss ≈ {random_loss:.3f} (Δ_0 参照)")
    p("")

    n_layers = 12
    all_layer_losses = []
    for seed in range(3):
        m = DeepSupervisedCharLM(vocab, dim=64, heads=4, n_layers=n_layers)
        outs = train(m, data, split, vocab, seed=seed)
        all_layer_losses.append(outs)
        p(f"seed{seed}: 逐层 test loss = {[f'{v:.3f}' for v in outs]}")

    L = np.mean(all_layer_losses, axis=0)          # L[k] = 用前 k+1 层 (0-indexed)
    L = np.concatenate([[random_loss], L])          # L[0] = 随机基线 (0 层)
    Delta = [L[k] - L[k+1] for k in range(len(L)-1)]
    p("")
    p(f"--- 平均 (3 seeds): 层数 k | loss(k) | 边际收益 Δ_k ---")
    for k in range(len(L)):
        if k == 0:
            p(f"     0 | {L[k]:8.3f} | (随机基线)")
        else:
            p(f"   {k:4d} | {L[k]:8.3f} | Δ_{k} = {L[k-1]-L[k]:+.4f}")
    dec = sum(1 for k in range(1, len(Delta)) if Delta[k] <= Delta[k-1] + 1e-9)
    p(f"")
    p(f"Δ 递减一致性: {dec}/{len(Delta)-1} 步 (Δ_k ≥ Δ_{k+1})  →  {dec/(len(Delta)-1)*100:.0f}%")
    p(f"对比: 合成线性任务 5/11 = 45%; 随机期望 = 50%")
    verdict = "前提恢复 (递减一致性显著 > 50%, 且 Δ 前段大后段小)" if dec/(len(Delta)-1) > 0.7 else \
              ("临界/需更大规模" if dec/(len(Delta)-1) > 0.55 else "前提未恢复 (递减一致性 ≈ 随机)")
    p(f"判定: {verdict}")
    p("")
    p("注: 真实 LM 有层次化深度收益 (浅层语法→深层语义), 与线性任务的本质区别")
    p("    在 Δ 的幅度分布: 真实任务 Δ 应前大后小且逐层减小, 而非全部 ≈ 噪声")

    with open(os.path.join(OUT, "experiments_e7_results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    p(f"\n结果已写入 scripts/experiments_e7_results.txt")

if __name__ == "__main__":
    main()
