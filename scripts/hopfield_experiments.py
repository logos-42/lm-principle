"""Hopfield 框架下一轮实验 (hopfile.md 驱动)

E1 联想记忆容量: Hebbian 权重, P/N vs 恢复率
E2 能量单调性: 异步更新 E(s) 轨迹 (应单调非增 + 收敛)
E3 β 分岔: 现代 Hopfield 更新 x ← X·softmax(βXᵀx), 重叠 cos(x,ξ1) vs β 相变
E4 逐层 Hopfield 能量 (回应上轮 Δ_k 不递减): 训练 Transformer, 每层注意力
   的能量 E_k = -1/β log Σ_j exp(β Q_i·V_j) + ½|Q_i|², 检验 ΔE_k 递减性
   —— 若能量度量下递减, 则临界点定理前提在 Hopfield 能量视角下成立
"""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import os

torch.set_num_threads(4)
OUT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(42)

# ---------------- E1: 联想记忆容量 ----------------
def hopfield_capacity(N=100, P_list=None, n_trials=30, max_iter=100):
    if P_list is None:
        P_list = list(range(1, 31))
    results = []
    for P in P_list:
        recoveries = []
        for _ in range(n_trials):
            patterns = rng.choice([-1.0, 1.0], size=(P, N))
            W = (patterns.T @ patterns) / N
            np.fill_diagonal(W, 0.0)
            # 从 20% 噪声模式异步更新
            probe = patterns[0].copy()
            flip = rng.choice(N, size=int(0.2 * N), replace=False)
            probe[flip] *= -1
            s = probe.copy()
            for _ in range(max_iter):
                order = rng.permutation(N)
                for i in order:
                    net = W[i] @ s
                    if s[i] * net < 0:
                        s[i] = -s[i]
            rec = np.mean(s == patterns[0])
            recoveries.append(rec)
        results.append((P, np.mean(recoveries), np.std(recoveries)))
    return results

# ---------------- E2: 能量轨迹 ----------------
def energy_trace(N=100, P=10, n_steps=200):
    patterns = rng.choice([-1.0, 1.0], size=(P, N))
    W = (patterns.T @ patterns) / N
    np.fill_diagonal(W, 0.0)
    def E(s):
        return -0.5 * s @ W @ s
    s = rng.choice([-1.0, 1.0], size=N)
    trace = [E(s)]
    for _ in range(n_steps):
        i = rng.integers(N)
        net = W[i] @ s
        if s[i] * net < 0:
            s[i] = -s[i]
        trace.append(E(s))
    return trace, E(s)

# ---------------- E3: β 分岔 (现代 Hopfield) ----------------
def beta_bifurcation(d=8, P=2, beta_list=None, n_queries=200, n_iter=50):
    if beta_list is None:
        beta_list = np.logspace(-1, 1.5, 30)
    Xi = rng.normal(size=(P, d))
    Xi /= np.linalg.norm(Xi, axis=1, keepdims=True)
    curves = []
    for beta in beta_list:
        ov = []
        for _ in range(n_queries):
            x = Xi[0] + 0.05 * rng.normal(size=d)   # 模式 1 附近
            x = x / np.linalg.norm(x)
            for _ in range(n_iter):
                logits = beta * Xi @ x
                w = np.exp(logits - logits.max())
                w /= w.sum()
                x = w @ Xi
                x = x / (np.linalg.norm(x) + 1e-9)
            ov.append(x @ Xi[0])
        curves.append((beta, np.mean(ov), np.std(ov)))
    return curves

# ---------------- E4: Transformer 逐层 Hopfield 能量 ----------------
class SmallTransformer(nn.Module):
    """单层块: MHA + FFN (残差), 记录每层 QKV"""
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
    def forward_qkv(self, x):
        dim = self.embed.out_features
        x = self.embed(x)
        qkvs = []
        hiddens = []
        for attn, ff, nm in zip(self.layers, self.ffs, self.norms):
            # 手动 QKV 投影 (nn.MultiheadAttention 的 in_proj): x @ Wᵀ + b
            q = x @ attn.in_proj_weight[:dim].T + attn.in_proj_bias[:dim]
            k = x @ attn.in_proj_weight[dim:2*dim].T + attn.in_proj_bias[dim:2*dim]
            v = x @ attn.in_proj_weight[2*dim:].T + attn.in_proj_bias[2*dim:]
            qkvs.append((q.detach().numpy(), k.detach().numpy(), v.detach().numpy()))
            hiddens.append(x.detach().numpy())
            a, _ = attn(x, x, x)
            x = nm(x + a)
            x = x + ff(x)
        return qkvs, hiddens

def hopfield_energy(q, V, beta):
    """现代 Hopfield 能量 E(x) = -1/β log Σ_j exp(β x·ξ_j) + ½|x|²  (x = q, ξ_j = V 行)"""
    q = q / (np.linalg.norm(q) + 1e-9)
    Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    lse = (1 / beta) * np.log(np.sum(np.exp(beta * Vn @ q)) + 1e-9)
    return -lse + 0.5 * np.dot(q, q)

def train_small(dim=32, n_layers=6, epochs=150, seed=0):
    torch.manual_seed(seed)
    X_train = torch.randn(500, 20, 10)
    y_train = X_train[:, :, 0].sum(dim=1) * 2 + X_train[:, :, 1].sum(dim=1) * 1.5 + torch.randn(500) * 0.3
    X_test = torch.randn(100, 20, 10)
    y_test = X_test[:, :, 0].sum(dim=1) * 2 + X_test[:, :, 1].sum(dim=1) * 1.5 + torch.randn(100) * 0.3
    m = SmallTransformer(dim, n_layers)
    opt = optim.Adam(m.parameters(), lr=0.001)
    crit = nn.MSELoss()
    for ep in range(epochs):
        opt.zero_grad()
        x = m.embed(X_train)
        for attn, ff, nm in zip(m.layers, m.ffs, m.norms):
            a, _ = attn(x, x, x)
            x = nm(x + a)
            x = x + ff(x)
        loss = crit(m.out(x.mean(dim=1)).squeeze(-1), y_train)
        loss.backward()
        opt.step()
    with torch.no_grad():
        qkvs, hiddens = m.forward_qkv(X_test[:20])
        test_loss = crit(m.out(m.embed(X_test).mean(dim=1)), y_test).item()
    return qkvs, hiddens, test_loss

def main():
    lines = []
    def p(s=""):
        print(s); lines.append(s)

    p("=== Hopfield 框架实验 (hopfile.md 驱动) ===")

    p("\n--- E1: 联想记忆容量 (N=100, Hebbian, 20% 噪声恢复) ---")
    for P, mean, std in hopfield_capacity(N=100):
        p(f"  P={P:3d} (P/N={P/100:.2f}): 恢复率 {mean:.3f} ± {std:.3f}")

    p("\n--- E2: 能量轨迹 (N=100, P=10, 200 步异步更新) ---")
    for trial in range(3):
        trace, Efinal = energy_trace()
        mono = all(trace[k + 1] <= trace[k] + 1e-9 for k in range(len(trace) - 1))
        p(f"  trial{trial}: E 起点 {trace[0]:.1f} → 终点 {Efinal:.1f}, 单调非增: {mono}, 末 20 步波动 {max(trace[-20:])-min(trace[-20:]):.2e}")

    p("\n--- E3: β 分岔 (现代 Hopfield, 2 模式, 重叠 vs β) ---")
    for beta, mean, std in beta_bifurcation():
        p(f"  β={beta:6.2f}: 重叠 cos(x,ξ₁) = {mean:.3f} ± {std:.3f}")

    p("\n--- E4: Transformer 逐层 Hopfield 能量 (6 层, 回应 Δ_k 递减性) ---")
    for beta in [1.0, 10.0]:
        qkvs, hiddens, test_loss = train_small()
        p(f"  (模型 test loss = {test_loss:.3f})")
        E_k = []
        for k, (q, K, V) in enumerate(qkvs):
            # 逐 token 平均能量 (取 batch 首样本: q[0] : (seq, dim), V : (seq, dim))
            energies = [hopfield_energy(q[0, t], V, beta) for t in range(q.shape[1])]
            E_k.append(np.mean(energies))
            p(f"   β={beta:5.1f} 层{k+1}: E = {E_k[-1]:8.4f}")
        dE = [E_k[k] - E_k[k + 1] for k in range(len(E_k) - 1)]
        pos = sum(1 for d in dE if d > 0)
        dec = sum(1 for k in range(1, len(dE)) if dE[k] <= dE[k - 1] + 1e-9)
        p(f"   β={beta:5.1f}: ΔE_k 全正: {pos}/{len(dE)} (每层能量下降), ΔE 递减一致性: {dec}/{len(dE)-1}")
        p(f"   β={beta:5.1f}: ΔE_k 序列 = {[f'{d:+.4f}' for d in dE]}")

    with open(os.path.join(OUT, "hopfield_experiments_results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    p("\n结果已写入 scripts/hopfield_experiments_results.txt")

if __name__ == "__main__":
    main()
