"""实验扩展 (hopfile.md 第二轮):

E5 每层实际 β_eff × 深度扫描:
  - β_eff(层) = mean_i (max_j S[i,j] - min_j S[i,j]), S = QK^T/√d (注意力 logits)
  - 深度 2/4/6/8 训练 (合成任务, 同 E4 模型), 测每层 β_eff 序列
  - 对照 E3 toy 的 β_c≈4: 各层处于混合态 (< β_c) 还是锁定区 (> β_c)
  - β_eff 与逐层 Hopfield 能量下降 ΔE_k 的相关性 (注意力集中层是否能量下降大)

E6 字符级 LM 重测 ΔE_k (排除合成任务伪影):
  - 真实语料: paper/main_conf.tex + main_jrnl.tex (英文文本)
  - CharLM: embed + 4×(MHA+FFN) + LM head, next-char 交叉熵
  - 训练到收敛后, 每层注意力 QKV → Hopfield 能量 E_k (β=1, 10)
  - 检验 ΔE_k 递减性 —— 合成任务 3/5 全正, 真实任务是否不同?
"""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import os, re

torch.set_num_threads(4)
OUT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(42)

# ---------------- 共享: 逐层 QKV + Hopfield 能量 ----------------
def hopfield_energy(q, V, beta):
    q = q / (np.linalg.norm(q) + 1e-9)
    Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    lse = (1 / beta) * np.log(np.sum(np.exp(beta * Vn @ q)) + 1e-9)
    return -lse + 0.5 * np.dot(q, q)

def extract_qkv_energies(model, x, beta):
    """返回 (E_k 序列, β_eff 序列); x 是 (batch, seq, dim) 输入 (已 embed)"""
    dim = model.embed.embedding_dim if isinstance(model.embed, nn.Embedding) else model.embed.out_features
    h = model.embed(x)
    E_k, B_k = [], []
    with torch.no_grad():
        for attn, ff, nm in zip(model.layers, model.ffs, model.norms):
            q = h @ attn.in_proj_weight[:dim].T + attn.in_proj_bias[:dim]
            k = h @ attn.in_proj_weight[dim:2*dim].T + attn.in_proj_bias[dim:2*dim]
            v = h @ attn.in_proj_weight[2*dim:].T + attn.in_proj_bias[2*dim:]
            qn, kn, vn = q.numpy(), k.numpy(), v.numpy()
            # β_eff: logit spread 的 token 平均 (取首样本)
            S = qn[0] @ kn[0].T / np.sqrt(dim)
            B_k.append(np.mean(S.max(axis=1) - S.min(axis=1)))
            # Hopfield 能量 (query = q 行, 存储 = v 行)
            energies = [hopfield_energy(qn[0, t], vn[0], beta) for t in range(qn.shape[1])]
            E_k.append(np.mean(energies))
            a, _ = attn(h, h, h)
            h = nm(h + a)
            h = h + ff(h)
    return E_k, B_k

# ---------------- E5: β_eff × 深度 (合成任务) ----------------
class SmallTransformer(nn.Module):
    def __init__(self, dim=32, n_layers=6):
        super().__init__()
        self.embed = nn.Linear(10, dim)
        self.out = nn.Linear(dim, 1)
        self.layers = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, 2, batch_first=True))
        self.ffs = nn.ModuleList([nn.Sequential(nn.Linear(dim, 4 * dim), nn.ReLU(), nn.Linear(4 * dim, dim))
                                  for _ in range(n_layers)])
        self.norms = nn.ModuleList([nn.LayerNorm(dim) for _ in range(n_layers)])

def train_synth(dim=32, n_layers=6, epochs=100, seed=0):
    torch.manual_seed(seed)
    X = torch.randn(400, 20, 10)
    y = X[:, :, 0].sum(dim=1) * 2 + X[:, :, 1].sum(dim=1) * 1.5 + torch.randn(400) * 0.3
    Xt = torch.randn(80, 20, 10)
    yt = Xt[:, :, 0].sum(dim=1) * 2 + Xt[:, :, 1].sum(dim=1) * 1.5 + torch.randn(80) * 0.3
    m = SmallTransformer(dim, n_layers)
    opt = optim.Adam(m.parameters(), lr=0.001)
    crit = nn.MSELoss()
    for ep in range(epochs):
        opt.zero_grad()
        x = m.embed(X)
        for attn, ff, nm in zip(m.layers, m.ffs, m.norms):
            a, _ = attn(x, x, x)
            x = nm(x + a)
            x = x + ff(x)
        loss = crit(m.out(x.mean(dim=1)).squeeze(-1), y)
        loss.backward()
        opt.step()
    with torch.no_grad():
        tl = crit(m.out(m.embed(Xt).mean(dim=1)), yt).item()
    return m, tl

# ---------------- E6: 字符级 LM ----------------
class CharLM(nn.Module):
    def __init__(self, vocab, dim=48, n_layers=4):
        super().__init__()
        self.embed = nn.Embedding(vocab, dim)
        self.layers = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, 2, batch_first=True))
        self.ffs = nn.ModuleList([nn.Sequential(nn.Linear(dim, 4 * dim), nn.ReLU(), nn.Linear(4 * dim, dim))
                                  for _ in range(n_layers)])
        self.norms = nn.ModuleList([nn.LayerNorm(dim) for _ in range(n_layers)])
        self.head = nn.Linear(dim, vocab)

def load_text_corpus():
    parts = []
    for f in ["paper/main_conf.tex", "paper/main_jrnl.tex"]:
        p = os.path.join(OUT, "..", f)
        if os.path.exists(p):
            t = open(p).read()
            parts.append(t)
    text = "\n".join(parts)
    text = re.sub(r"%.*", "", text)          # 去 LaTeX 注释
    text = re.sub(r"\s+", " ", text)[:60000]
    return text

def train_charlm(seq=64, epochs=30, seed=1):
    torch.manual_seed(seed)
    text = load_text_corpus()
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    data = np.array([stoi[c] for c in text], dtype=np.int64)
    n = len(data)
    split = int(n * 0.9)
    m = CharLM(len(chars))
    opt = optim.Adam(m.parameters(), lr=0.001)
    crit = nn.CrossEntropyLoss()
    Xall = torch.from_numpy(data)
    for ep in range(epochs):
        opt.zero_grad()
        ix = torch.randint(0, split - seq, (32,))
        xb = torch.stack([Xall[i:i + seq] for i in ix])
        yb = torch.stack([Xall[i + 1:i + seq + 1] for i in ix])
        h = m.embed(xb)
        for attn, ff, nm in zip(m.layers, m.ffs, m.norms):
            a, _ = attn(h, h, h)
            h = nm(h + a)
            h = h + ff(h)
        logits = m.head(h)
        loss = crit(logits.reshape(-1, len(chars)), yb.reshape(-1))
        loss.backward()
        opt.step()
    # 测试 loss
    with torch.no_grad():
        xb = Xall[split:split + seq].unsqueeze(0)
        yb = Xall[split + 1:split + seq + 1].unsqueeze(0)
        h = m.embed(xb)
        for attn, ff, nm in zip(m.layers, m.ffs, m.norms):
            a, _ = attn(h, h, h)
            h = nm(h + a)
            h = h + ff(h)
        logits = m.head(h)
        tl = crit(logits.reshape(-1, len(chars)), yb.reshape(-1)).item()
    return m, tl, len(chars)

def main():
    lines = []
    def p(s=""):
        print(s); lines.append(s)

    p("=== 实验扩展: β_eff×深度 + 真实 LM ΔE_k ===")

    p("\n--- E5: 每层实际 β_eff × 深度扫描 (合成任务) ---")
    for depth in [2, 4, 6, 8]:
        m, tl = train_synth(n_layers=depth)
        E_k, B_k = extract_qkv_energies(m, torch.randn(1, 20, 10), beta=1.0)
        p(f"  depth={depth} (test loss {tl:.3f}):")
        for k in range(depth):
            p(f"    层{k+1}: β_eff = {B_k[k]:6.2f} ({'锁定区 β>β_c' if B_k[k] > 4 else '混合区 β<β_c'}), E = {E_k[k]:8.4f}")
        dE = [E_k[k] - E_k[k + 1] for k in range(len(E_k) - 1)]
        p(f"    ΔE_k = {[f'{d:+.4f}' for d in dE]}, 全正: {sum(1 for d in dE if d > 0)}/{len(dE)}")
        # β_eff 与 ΔE_k 的关系 (浅层→深层, β_eff 变化方向)
        if len(B_k) >= 2:
            trend = "深层更集中" if B_k[-1] > B_k[0] else "深层更分散"
            p(f"    β_eff 趋势: {B_k[0]:.2f} → {B_k[-1]:.2f} ({trend})")

    p("\n--- E6: 字符级 LM 重测 ΔE_k (真实文本语料) ---")
    m, tl, vocab = train_charlm()
    p(f"  (vocab={vocab}, test loss={tl:.3f}; 随机基线 ≈ {np.log(vocab):.2f})")
    # 真实测试序列 (语料尾部)
    text = load_text_corpus()
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    data = np.array([stoi[c] for c in text], dtype=np.int64)
    xb = torch.from_numpy(data[-64:]).unsqueeze(0)
    for beta in [1.0, 10.0]:
        E_k, B_k = extract_qkv_energies(m, xb, beta)
        p(f"   β={beta:5.1f}: 层 E 序列 = {[f'{e:.4f}' for e in E_k]}")
        dE = [E_k[k] - E_k[k + 1] for k in range(len(E_k) - 1)]
        pos = sum(1 for d in dE if d > 0)
        dec = sum(1 for k in range(1, len(dE)) if dE[k] <= dE[k - 1] + 1e-9)
        p(f"   β={beta:5.1f}: ΔE_k 全正: {pos}/{len(dE)}, ΔE 递减一致性: {dec}/{len(dE)-1}, ΔE_k = {[f'{d:+.4f}' for d in dE]}")
        p(f"   β={beta:5.1f}: β_eff 每层 = {[f'{b:.2f}' for b in B_k]}")

    with open(os.path.join(OUT, "experiments_h2_results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    p("\n结果已写入 scripts/experiments_h2_results.txt")

if __name__ == "__main__":
    main()
