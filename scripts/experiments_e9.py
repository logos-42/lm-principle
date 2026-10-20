"""E9 判定实验: 规模法则的双地板结构 (认知动力学 L2, 零成本 CPU)

动机 (2026-10-20):
  L2 预测损失下界 = 残余失真 D*(R(N)) + 不可约熵 H(𝒫|𝒾*)——两块地板:
  参数地板 (N→∞ 时由数据量 T 决定) 与数据地板 (T→∞ 时由参数量 N 决定)。
  若两块地板近似可加, 则规模法则的"有效"与"截止"都有同一个解释:
  幂律谱 ⟹ 失真幂律下降 (有效); 不可约熵 + 有限数据谱估计误差 (截止)。

E9 设计:
  - 模型: CharLM (dim ∈ {24, 48, 96}, 6 层), 实际参数数为 N (实测)
  - 数据: T ∈ {10K, 40K, 160K} 字符 (同语料不同前缀)
  - 网格 3×3×2 seeds = 18 模型, 测最终 mean-exit loss L(N, T)
  - 判定:
    ① 参数地板: 固定 T, L 随 N 下降并趋缓 (趋近该 T 的地板)
    ② 数据地板: 固定 N, L 随 T 下降并趋缓 (趋近该 N 的地板)
    ③ 可加性: L(N,T) − L(N_max,T) 与 L(N,T) − L(N,T_max) 的分解残差
       (若双地板可加, 两个方向的"剩余下降"应近似互不干扰)
    ④ 幂律拟合: log(L − L_floor) vs log N 的斜率 (α)

输出: scripts/experiments_e9_results.txt + experiments/results/e9_scaling.json
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
    return " ".join(parts)[:170_000]

class CharLM(nn.Module):
    def __init__(self, vocab, dim=64, heads=4, n_layers=6):
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

def train(data, split, vocab, seed, dim, steps=250, seq=64, bs=16, lr=3e-3):
    torch.manual_seed(seed)
    model = CharLM(vocab, dim=dim)
    n_params = sum(p.numel() for p in model.parameters())
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
    return n_params, test_loss

def main():
    lines = []
    def p(s=""):
        print(s); lines.append(s)
    R = {}

    text = load_corpus()
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    vocab = len(chars)
    data_full = np.array([stoi[c] for c in text], dtype=np.int64)
    p("=" * 74)
    p(f"E9: 规模法则双地板结构 (vocab={vocab}, 语料 {len(data_full)/1e3:.0f}K 字符)")
    p("=" * 74)

    dims = [24, 48, 96]
    Ts = [10_000, 40_000, 160_000]
    L = {}   # (dim, T, seed) -> (n_params, loss)
    for dim in dims:
        for T in Ts:
            for seed in range(2):
                d = data_full[:T]
                split = int(T * 0.9)
                n_params, loss = train(d, split, vocab, seed, dim)
                L[(dim, T, seed)] = (n_params, loss)
                p(f"  dim={dim:3d} T={T/1e3:5.1f}K seed{seed}: N={n_params:7d}  loss={loss:.4f}")

    # 汇总: 每格 2 seeds 平均
    p("")
    p("--- loss 表 (2 seeds 平均) ---")
    p("   T\\dim |" + "".join(f"{d:>10d}" for d in dims))
    grid = {}
    for T in Ts:
        row = []
        for dim in dims:
            v = np.mean([L[(dim, T, s)][1] for s in range(2)])
            grid[(dim, T)] = v
            row.append(v)
        Ns = [L[(d, T, 0)][0] for d in dims]
        p(f"  {T/1e3:5.1f}K |" + "".join(f"{v:>10.4f}" for v in row) + f"   (N={Ns})")

    # ① 参数地板: 固定 T, 沿 dim 的边际下降
    p("")
    p("--- ① 参数地板: 固定 T 的边际下降 Δ_dim = L(dim_k) − L(dim_max) ---")
    for T in Ts:
        vals = [grid[(d, T)] for d in dims]
        deltas = [vals[k] - vals[-1] for k in range(len(dims)-1)]
        p(f"  T={T/1e3:5.1f}K: Δ = {[f'{v:+.4f}' for v in deltas]}  "
          f"(dim24→96 总下降 {vals[0]-vals[-1]:.4f})")

    # ② 数据地板: 固定 dim, 沿 T 的边际下降
    p("--- ② 数据地板: 固定 dim 的边际下降 Δ_T = L(T_k) − L(T_max) ---")
    for dim in dims:
        vals = [grid[(dim, T)] for T in Ts]
        deltas = [vals[k] - vals[-1] for k in range(len(Ts)-1)]
        p(f"  dim={dim:3d}: Δ = {[f'{v:+.4f}' for v in deltas]}  "
          f"(10K→160K 总下降 {vals[0]-vals[-1]:.4f})")

    # ③ 可加性: 双向分解残差
    # L(N,T) − L(Nmax,T) ≈ [L(N,Tmax) − L(Nmax,Tmax)] ⟺ 可加
    p("")
    p("--- ③ 可加性检查: |双向剩余下降之差| (小 = 双地板近似可加) ---")
    resid = []
    for dim in dims[:-1]:
        for T in Ts[:-1]:
            a = grid[(dim, T)] - grid[(dims[-1], T)]      # 参数方向的剩余下降
            b = grid[(dim, T)] - grid[(dim, Ts[-1])]      # 数据方向的剩余下降
            resid.append(abs(a - b))
            p(f"  dim={dim:3d} T={T/1e3:5.1f}K: 参数向 {a:.4f} vs 数据向 {b:.4f}  |差|={abs(a-b):.4f}")
    p(f"  平均残差 = {np.mean(resid):.4f} (相对 loss 量级 {np.mean(list(grid.values())):.3f})")

    # ④ 幂律拟合: log(L − floor) vs log N, floor = 该 T 列最小 loss
    p("")
    p("--- ④ 幂律拟合: log(L(N) − L_floor) vs log N (固定 T) ---")
    slopes = []
    for T in Ts:
        vals = np.array([grid[(d, T)] for d in dims])
        floor = vals[-1]
        excess = vals[:-1] - floor
        ok = excess > 1e-6
        if ok.sum() >= 2:
            Ns = np.array([L[(d, T, 0)][0] for d in dims[:-1]], dtype=float)
            slope, _ = np.polyfit(np.log(Ns[ok]), np.log(excess[ok]), 1)
            slopes.append(slope)
            p(f"  T={T/1e3:5.1f}K: 斜率 = {slope:.3f} (L − floor ~ N^{slope:.2f})")
    if slopes:
        p(f"  平均斜率 = {np.mean(slopes):.3f} (负 = 幂律下降; 规模法则的形状)")

    p("")
    p("--- 判定 ---")
    param_drops = [grid[(dims[0], T)] - grid[(dims[-1], T)] for T in Ts]
    data_drops = [grid[(dims[0], T)] - grid[(dims[0], Ts[-1])] for T in Ts]
    v1 = all(dp > 0.01 for dp in param_drops)
    v2 = data_drops[0] > 0.01  # dim24 时数据也有明显下降
    p(f"  ① 参数地板: {'成立' if v1 else '不显著'} (dim24→96 在各 T 下降 {[f'{v:.3f}' for v in param_drops]})")
    p(f"  ② 数据地板: {'成立' if v2 else '不显著'} (dim24 时 10K→160K 降 {data_drops[0]:.3f})")
    p(f"  ③ 可加性: 平均残差 {np.mean(resid):.4f}")
    p(f"  ④ 幂律斜率均值 {np.mean(slopes) if slopes else float('nan'):.3f}")
    p("")
    p("诚实边界: 小模型 + 250 步弱训练; vocab~1.2K 使 exit 头占参数大头;")
    p("  '地板'用网格最内点近似而非真极限; 单语料族。冒烟测试, 非验证/证伪。")

    R["grid"] = {f"dim{d}_T{t}": v for (d, t), v in grid.items()}
    R["params"] = {f"dim{d}": L[(d, Ts[0], 0)][0] for d in dims}
    R["param_drops"] = param_drops
    R["data_drops"] = data_drops
    R["additivity_resid"] = float(np.mean(resid))
    R["powerlaw_slopes"] = slopes

    with open(os.path.join(OUT, "experiments_e9_results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    os.makedirs(os.path.join(ROOT, "experiments", "results"), exist_ok=True)
    with open(os.path.join(ROOT, "experiments", "results", "e9_scaling.json"), "w") as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    p("\n结果已写入 scripts/experiments_e9_results.txt + experiments/results/e9_scaling.json")

if __name__ == "__main__":
    main()
