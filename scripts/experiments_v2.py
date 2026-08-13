"""实验 v2: 修正缺陷后的收益-成本测量

缺陷修正:
  实验一: 树级成本加流量守恒因子 Q_g = Q/2^g ⟹ 最优收敛 2^(-1/3) (见 diagnose_murray_cost.py)
  实验二: 原任务模型不学习 (loss 113.6 ~ 常数基线 113.78) ⟹ 改 mini-batch + 更低 lr + 线性基线对照
  实验三: 单 seed 不可复现 ⟹ 多 seed mean±std + **深度监督逐层边际收益 Δ_k 测量** + 交叉点 L*(λ)

输出: scripts/experiments_v2_results.txt
"""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import os

torch.set_num_threads(4)
OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------- 数据 (与 shape.md 相同, 任务可被线性模型精确求解) ----------------
def make_data(seed):
    torch.manual_seed(seed)
    X_train = torch.randn(800, 20, 10)
    y_train = X_train[:, :, 0].sum(dim=1) * 2 + X_train[:, :, 1].sum(dim=1) * 1.5 + torch.randn(800) * 0.3
    X_test = torch.randn(200, 20, 10)
    y_test = X_test[:, :, 0].sum(dim=1) * 2 + X_test[:, :, 1].sum(dim=1) * 1.5 + torch.randn(200) * 0.3
    return X_train, y_train, X_test, y_test

class FractalLayer(nn.Module):
    def __init__(self, dim=64, heads=4, is_deep=False, connection_density=1.0):
        super().__init__()
        actual_heads = max(2, heads if not is_deep else heads // 2)
        self.attn = nn.MultiheadAttention(dim, actual_heads, batch_first=True)
        ff_ratio = 4 if not is_deep else max(1, int(4 * connection_density))
        self.ff = nn.Sequential(nn.Linear(dim, dim * ff_ratio), nn.ReLU(), nn.Linear(dim * ff_ratio, dim))
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
    def forward(self, x):
        a, _ = self.attn(x, x, x)
        x = self.norm1(x + a)
        return self.norm2(x + self.ff(x))

class UniformNet(nn.Module):
    def __init__(self, dim=64, heads=4, n_layers=8):
        super().__init__()
        self.layers = nn.ModuleList([FractalLayer(dim, heads) for _ in range(n_layers)])
        self.embed = nn.Linear(10, dim)
        self.output = nn.Linear(dim, 1)
    def forward(self, x):
        x = self.embed(x)
        for l in self.layers:
            x = l(x)
        return self.output(x.mean(dim=1)).squeeze(-1)

class FractalNet(nn.Module):
    def __init__(self, dim=64, heads=4, n_layers=8, fractal_dim=2.5):
        super().__init__()
        self.layers = nn.ModuleList()
        for i in range(n_layers):
            dr = i / max(1, n_layers - 1)
            self.layers.append(FractalLayer(dim, heads, is_deep=dr > 0.5,
                                            connection_density=(1 - dr) ** (fractal_dim - 1)))
        self.embed = nn.Linear(10, dim)
        self.output = nn.Linear(dim, 1)
    def forward(self, x):
        x = self.embed(x)
        for l in self.layers:
            x = l(x)
        return self.output(x.mean(dim=1)).squeeze(-1)

class DeepSupervisedNet(nn.Module):
    """深度监督: 每层后一个 exit head, 全部有监督信号 ⟹ 可测每层边际收益 Δ_k"""
    def __init__(self, dim=32, n_layers=12):
        super().__init__()
        self.layers = nn.ModuleList([FractalLayer(dim, 2) for _ in range(n_layers)])
        self.embed = nn.Linear(10, dim)
        self.exits = nn.ModuleList([nn.Linear(dim, 1) for _ in range(n_layers)])
    def forward_exits(self, x):
        x = self.embed(x)
        outs = []
        for l, e in zip(self.layers, self.exits):
            x = l(x)
            outs.append(e(x.mean(dim=1)).squeeze(-1))
        return outs

class LinearBaseline(nn.Module):
    """线性读出头: mean_t(w·x_t) ⟹ 任务的最优解 w=[2,1.5,0..] 可达, 验证任务可学习"""
    def __init__(self):
        super().__init__()
        self.w = nn.Linear(10, 1)
    def forward(self, x):
        return self.w(x).squeeze(-1).mean(dim=1)

def train(model, X, y, Xt, yt, epochs=200, lr=0.001, bs=64, deep=False):
    opt = optim.Adam(model.parameters(), lr=lr)
    crit = nn.MSELoss()
    n = X.shape[0]
    for ep in range(epochs):
        perm = torch.randperm(n)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            opt.zero_grad()
            if deep:
                outs = model.forward_exits(X[idx])
                loss = torch.stack([crit(o, y[idx]) for o in outs]).mean()
            else:
                loss = crit(model(X[idx]), y[idx])
            loss.backward()
            opt.step()
    with torch.no_grad():
        if deep:
            outs = [crit(o, yt).item() for o in model.forward_exits(Xt)]
            return outs
        return crit(model(Xt), yt).item()

def main():
    lines = []
    def p(s=""):
        print(s); lines.append(s)

    p("=== 实验 v2: 收益-成本测量 (3 seeds) ===")

    # ---- 基线: 常数预测 + 线性读出头 (任务可学习性验证) ----
    const_losses, lin_losses = [], []
    for seed in range(3):
        X, y, Xt, yt = make_data(seed)
        const_losses.append(yt.var().item())
        lin = LinearBaseline()
        lin_losses.append(train(lin, X, y, Xt, yt, epochs=50, lr=0.05))
    p(f"常数预测器 (y 方差): {np.mean(const_losses):.4f}")
    p(f"线性读出头:          {np.mean(lin_losses):.4f}  (≪常数 ⟹ 任务可学习)")
    p(f"任务最优 (噪声²):     ≈0.09")

    # ---- 实验二 v2: 分形 vs 均匀, 多 seed + mini-batch ----
    p("\n--- 实验二 v2: 分形 vs 均匀 (mini-batch 64, lr 0.001, 200 epochs, 3 seeds) ---")
    u_l, f_l = [], []
    u_p, f_p = [], []
    for seed in range(3):
        X, y, Xt, yt = make_data(seed)
        u = UniformNet(dim=64, heads=4, n_layers=8)
        f = FractalNet(dim=64, heads=4, n_layers=8)
        u_p.append(sum(p.numel() for p in u.parameters()))
        f_p.append(sum(p.numel() for p in f.parameters()))
        u_l.append(train(u, X, y, Xt, yt))
        f_l.append(train(f, X, y, Xt, yt))
        p(f"  seed{seed}: uniform={u_l[-1]:.4f} fractal={f_l[-1]:.4f}")
    p(f"  参数: uniform={u_p[0]} fractal={f_p[0]} (省 {(1 - f_p[0]/u_p[0])*100:.1f}%)")
    p(f"  loss mean±std: uniform={np.mean(u_l):.4f}±{np.std(u_l):.4f}  fractal={np.mean(f_l):.4f}±{np.std(f_l):.4f}")

    # ---- 实验三 v2: 深度扫描 (3 seeds) + 深度监督 Δ_k 测量 + 交叉点 ----
    p("\n--- 实验三 v2a: 深度扫描 (dim32, 80 epochs, 3 seeds, mean±std) ---")
    depths = [2, 4, 6, 8, 10, 12]
    u_sweep = {d: [] for d in depths}
    for seed in range(3):
        X, y, Xt, yt = make_data(seed)
        for d in depths:
            m = UniformNet(dim=32, heads=2, n_layers=d)
            u_sweep[d].append(train(m, X, y, Xt, yt, epochs=80, lr=0.001))
    for d in depths:
        p(f"  depth={d:2d}: {np.mean(u_sweep[d]):8.4f} ± {np.std(u_sweep[d]):.4f}")

    p("\n--- 实验三 v2b: 深度监督逐层边际收益 Δ_k (12 层, 150 epochs, 3 seeds) ---")
    # 逐层 loss 曲线: loss(k) = 第 k 层 exit 的 test loss; Δ_k = loss(k-1) - loss(k)
    layer_losses = []
    for seed in range(3):
        X, y, Xt, yt = make_data(seed)
        m = DeepSupervisedNet(dim=32, n_layers=12)
        outs = train(m, X, y, Xt, yt, epochs=150, lr=0.001, deep=True)
        layer_losses.append(outs)
    L = np.mean(layer_losses, axis=0)          # L[k] = 用前 k+1 层时的 loss (0-indexed)
    const = np.mean(const_losses)
    L = np.concatenate([[const], L])            # L[0] = 常数基线 (0 层)
    Delta = [L[k] - L[k + 1] for k in range(len(L) - 1)]   # Δ_k = 加第 k+1 层(k从0)的边际收益
    p(f"  层数 k | loss(k)   | 边际收益 Δ_k")
    for k in range(len(L)):
        if k == 0:
            p(f"     0  | {L[k]:8.4f} | (基线)")
        else:
            p(f"   {k:4d}  | {L[k]:8.4f} | Δ_{k} = {L[k-1]-L[k]:+.4f}")
    # 递减性检验
    dec = sum(1 for k in range(1, len(Delta)) if Delta[k] <= Delta[k-1] + 1e-9)
    p(f"  Δ 递减一致性: {dec}/{len(Delta)-1} 步 (Δ_k ≥ Δ_{k+1})")
    # 交叉点: 对 λ ∈ {0.05, 0.1, 0.2}, L*(λ) = 第一个 Δ_k < λ 的层
    p("  交叉点 L*(λ) = 第一个 Δ_k < λ 的层 (收益成本不等式的临界位置):")
    for lam in [0.05, 0.1, 0.2]:
        cross = None
        for k, d in enumerate(Delta):
            if d < lam:
                cross = k
                break
        p(f"    λ={lam}: L* = {cross if cross is not None else '无 (λ 全程低于收益)'}")

    with open(os.path.join(OUT, "experiments_v2_results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    p(f"\n结果已写入 scripts/experiments_v2_results.txt")

if __name__ == "__main__":
    main()
