"""E8 实验: 普适权重子空间假说的本地 CPU 复现 (认知动力学 R1, 2026-10-20)

动机:
  arXiv:2512.05117v3 (universal-weight-subspace.md 编译页) 声称: 同架构训练的
  深度网络跨任务/初始化/领域收敛到少数共享低维谱子空间 (1200+ 模型实证,
  ≤16 个主方向捕获大部分方差, 存储 >100×)。其理论只是条件性的——核心假设
  A.3 (训练动力学选择层输入协方差 top-k 子空间) 未建立。E8 用本地小 CharLM
  检验三个可观测推论 (论文自述谱分解可 CPU 运行, 与本机条件匹配):

  8A 跨域共享性: 4 领域 (docs/readme/lean/tex) × 3 seeds = 12 模型。
     逐权重张量堆叠 → 居中 → SVD (mode-1 HOSVD / PCA across models)。
     - 域内子空间距离 (同域不同 seed) vs 域间子空间距离 (跨域)
     - top-k 方差捕获 (k=1..8), 检验 "≤16 方向捕获大部分方差"
  8B 感知量-精度律: 论文 Thm 3.7 给跨任务子空间误差 ~ T^{-1/2}。
     本地版: 两份不相交的 T 字符各训一个模型 (同 seed), 测两者权重子空间
     距离 d(T); log-log 斜率应 ≈ -0.5。
  8C 谱指数 vs 可训练性: 论文 suitability 判据 = 谱尾重尾指数 α∈[2,6] 的层
     才被保留。本地版: 每层 attn_out 权重谱的秩衰减指数 β (λ_i ∝ i^{-β})
     vs 该层深度监督收益 Δ_k, Spearman 相关。

诚实边界 (预登记):
  - 模型极小 (6 层 dim=64, 250 步), 域是同一仓库内的文件族 (都是代码/散文混合),
    "跨领域"是弱版本; 结论只作冒烟测试, 不构成对论文的验证或证伪
  - 每 T 仅 2 模型, 子空间估计本身噪声大; 8B 斜率只有 3 个点
  - 论文 α 定义 (ESD 尾指数, Martin & Hinrichs 2025) 与本地 β (秩衰减指数)
    不是同一个量, 只作分布对照, 不做窗口判定

输出: scripts/experiments_e8_results.txt + experiments/results/e8_subspace.json
"""
import os, re, glob, json
import numpy as np
import torch, torch.nn as nn, torch.optim as optim

torch.set_num_threads(4)
OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, ".."))

# ---------------- 语料: 按文件族分 4 个"领域" ----------------
GROUPS = {
    "docs":  ["docs/wiki/*.md"],
    "readme": ["README.md", "README.zh.md", "AGENTS.md", "CLAUDE.md"],
    "lean":  ["LmPrinciple/*.lean"],
    "tex":   ["paper/*.tex"],
}

def load_group(patterns, cap):
    parts = []
    for pat in patterns:
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            try:
                t = open(f, encoding="utf-8", errors="ignore").read()
                t = re.sub(r"%.*", "", t)
                t = re.sub(r"\s+", " ", t)
                parts.append(t)
            except Exception:
                pass
    return " ".join(parts)[:cap]

def load_corpus():
    """返回 (groups: dict[str,str], full: str)。full 不截断 (8B 需要尽量大)。"""
    groups = {g: load_group(pats, 60_000) for g, pats in GROUPS.items()}
    full = " ".join(groups.values())
    return groups, full

# ---------------- 深度监督 CharLM (同 E7 结构, 6 层) ----------------
class DeepSupervisedCharLM(nn.Module):
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

def train(data, split, vocab, seed, steps=250, seq=64, bs=16, lr=3e-3):
    """训练一个模型, 返回 (model, per-exit test losses)。"""
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

# ---------------- 权重提取与子空间分析 ----------------
def collect_weights(model, n_layers):
    """name -> 2D ndarray。跳过 1-D (norm/bias)。"""
    sd = model.state_dict()
    W = {"embed": sd["embed.weight"].numpy()}
    for i in range(n_layers):
        W[f"L{i}.attn_in"]  = sd[f"layers.{i}.in_proj_weight"].numpy()
        W[f"L{i}.attn_out"] = sd[f"layers.{i}.out_proj.weight"].numpy()
        W[f"L{i}.ffn_up"]   = sd[f"ffs.{i}.0.weight"].numpy()
        W[f"L{i}.ffn_down"] = sd[f"ffs.{i}.2.weight"].numpy()
        W[f"L{i}.exit"]     = sd[f"exits.{i}.weight"].numpy()
    return W

def pca_explained(stack):
    """stack: (M, D) 已堆叠的权重。返回 top-k 方差捕获率 (k=1..8)。"""
    Xc = stack - stack.mean(axis=0, keepdims=True)
    s = np.linalg.svd(Xc, compute_uv=False)
    tot = (s**2).sum()
    if tot <= 0:
        return [float("nan")] * 8
    return [float((s[:k]**2).sum() / tot) for k in range(1, 9)]

def top_basis(stack, r):
    """返回居中堆叠权重张量的 top-r 右奇异向量 (D, r) = 模型轴张成的子空间基。"""
    Xc = stack - stack.mean(axis=0, keepdims=True)
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
    return Vt[:r].T

def subspace_dist(Va, Vb):
    """两个 r 维子空间 (正交基 Va, Vb: D×r) 的 chordal 距离与平均主角。"""
    M = Va.T @ Vb
    sv = np.clip(np.linalg.svd(M, compute_uv=False), 0.0, 1.0)
    cos2 = sv**2
    return float(np.sqrt(max(0.0, 1.0 - cos2.mean()))), float(np.degrees(np.arccos(np.sqrt(cos2.mean()))))

def powerlaw_beta(W, lo=16, hi=32):
    """秩衰减指数 β: λ_i ∝ i^{-β}, λ = W^T W 特征值 (=奇异值平方)。窗口 [lo,hi]。"""
    s = np.linalg.svd(W, compute_uv=False)
    lam = s**2
    n = len(lam)
    hi = min(hi, n - 1)
    if hi <= lo + 2:
        return float("nan")
    idx = np.arange(lo, hi + 1)
    good = lam[lo:hi+1] > 0
    if good.sum() < 4:
        return float("nan")
    b, _ = np.polyfit(np.log(idx[good]), np.log(lam[lo:hi+1][good]), 1)
    return float(-b)  # β > 0 表示衰减

def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 4:
        return float("nan"), len(x)
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    denom = np.sqrt((rx**2).sum() * (ry**2).sum())
    return (float((rx * ry).sum() / denom) if denom > 0 else float("nan")), len(x)

# ---------------- 主流程 ----------------
def main():
    lines = []
    def p(s=""):
        print(s); lines.append(s)
    R = {}  # JSON 结果

    groups, full = load_corpus()
    chars = sorted(set(full))
    stoi = {c: i for i, c in enumerate(chars)}
    vocab = len(chars)
    data_full = np.array([stoi[c] for c in full], dtype=np.int64)
    p("=" * 76)
    p(f"E8: 普适权重子空间假说本地 CPU 复现 (vocab={vocab}, 全语料 {len(data_full)/1e3:.0f}K 字符)")
    p("=" * 76)
    for g, t in groups.items():
        p(f"  领域[{g}]: {len(t)/1e3:.1f}K 字符")
    p("")

    N_LAYERS = 6
    TENSOR_NAMES = None  # 第一次收集时确定

    def stack_group(models_W, name):
        return np.stack([m[name].reshape(-1) for m in models_W], axis=0)

    # ================= 8A: 4 领域 × 3 seeds = 12 模型 =================
    p("--- 8A 跨域共享性 (4 领域 × 3 seeds, 6 层 dim=64, 250 步) ---")
    models_W, models_loss = {}, {}
    for g in GROUPS:
        d = np.array([stoi[c] for c in groups[g]], dtype=np.int64)
        split = int(len(d) * 0.9)
        for seed in range(3):
            m, losses = train(d, split, vocab, seed)
            models_W[(g, seed)] = collect_weights(m, N_LAYERS)
            models_loss[(g, seed)] = losses
            p(f"  [{g} seed{seed}] 逐层 exit loss = {[f'{v:.3f}' for v in losses]}")
    TENSOR_NAMES = list(models_W[(list(GROUPS)[0], 0)].keys())
    p(f"  权重张量组: {len(TENSOR_NAMES)} 个 (embed/每层 attn_in/attn_out/ffn_up/ffn_down/exit)")
    p("")

    # top-k 方差捕获 (12 模型全 pooled)
    p("  top-k 方差捕获 (12 模型 pooled, 跨张量平均):")
    evo = []
    for name in TENSOR_NAMES:
        evo.append(pca_explained(stack_group([models_W[k] for k in models_W], name)))
    evo = np.nanmean(np.array(evo), axis=0)
    for k in range(8):
        p(f"    k={k+1}: {evo[k]*100:5.1f}%")
    R["8A_topk_variance"] = evo.tolist()
    p("")

    # 域内 vs 域间子空间距离 (r=8, 逐张量算完再平均)
    r = 8
    def group_subspaces(keys):
        return {name: top_basis(stack_group([models_W[k] for k in keys], name), r)
                for name in TENSOR_NAMES}
    gs = list(GROUPS)
    pooled_sub = {g: group_subspaces([(g, s) for s in range(3)]) for g in gs}
    within = []
    for g in gs:
        ds = []
        for n in TENSOR_NAMES:
            for s1, s2 in [(0, 1), (0, 2), (1, 2)]:
                sub = top_basis(stack_group([models_W[(g, s1)], models_W[(g, s2)]], n), r)
                ds.append(subspace_dist(sub, pooled_sub[g][n])[0])
        within.append(float(np.mean(ds)))
    cross = []
    per_pair = {}
    for i in range(len(gs)):
        for j in range(i + 1, len(gs)):
            ga, gb = gs[i], gs[j]
            ds = [subspace_dist(pooled_sub[ga][n], pooled_sub[gb][n])[0] for n in TENSOR_NAMES]
            cross.append(float(np.mean(ds)))
            per_pair[f"{ga}-{gb}"] = cross[-1]
    mw, mc = float(np.mean(within)), float(np.mean(cross))
    p(f"  域内子空间距离 (同域不同 seed vs 域内 pooled): {[f'{v:.3f}' for v in within]}  mean={mw:.3f}")
    p(f"  域间子空间距离 (域 pooled vs 域 pooled):")
    for kk, vv in per_pair.items():
        p(f"    {kk:14s}: {vv:.3f}")
    p(f"    mean={mc:.3f}")
    ratio = mc / mw if mw > 0 else float("nan")
    p(f"  域间/域内 = {ratio:.2f}")
    if ratio < 1.2:
        verdict8A = "强普适冒烟通过 (域间≈域内, 子空间几乎不由任务决定)"
    elif ratio < 2.0:
        verdict8A = "部分共享 (域间略大于域内, 架构共享+任务特异并存)"
    else:
        verdict8A = "弱/无共享 (域间显著大于域内, 子空间由任务主导)"
    p(f"  判定: {verdict8A}")
    p("")
    R["8A"] = {"within": within, "cross": cross, "per_pair": per_pair,
               "mean_within": mw, "mean_cross": mc, "ratio": ratio, "verdict": verdict8A}

    # ================= 8B: T^{-1/2} 感知量-精度律 =================
    # 注: 子空间需要 ≥2 个模型张成 (单模型居中后为零矩阵) —— 每半区 3 seeds,
    # 各张成 rank ≤ 2 的子空间, 测两个半区子空间的距离 d(T)。
    p("--- 8B 感知量-精度律 (两半区各 3 seeds, 测子空间距离 d(T)) ---")
    n2 = len(data_full) // 2
    T_list = [10_000, 40_000, min(100_000, n2)]
    T_list = [t for t in T_list if 2 * t <= len(data_full)]
    rB = 2
    dTs = []
    for T in T_list:
        WA = [collect_weights(train(data_full[:T], int(T * 0.9), vocab, seed=10 + s)[0], N_LAYERS)
              for s in range(3)]
        WB = [collect_weights(train(data_full[T:2*T], int(T * 0.9), vocab, seed=20 + s)[0], N_LAYERS)
              for s in range(3)]
        ds = [subspace_dist(top_basis(stack_group(WA, n), rB),
                            top_basis(stack_group(WB, n), rB))[0] for n in TENSOR_NAMES]
        dT = float(np.mean(ds))
        dTs.append(dT)
        p(f"  T={T/1e3:6.1f}K: 子空间距离 d(T) = {dT:.4f}  (跨 {len(TENSOR_NAMES)} 张量平均)")
    if len(dTs) >= 2 and all(d > 0 for d in dTs):
        slope, intercept = np.polyfit(np.log(T_list), np.log(dTs), 1)
        pred = np.polyval([slope, intercept], np.log(T_list))
        ss_res = float(((np.log(dTs) - pred)**2).sum())
        ss_tot = float(((np.log(dTs) - np.log(dTs).mean())**2).sum())
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        p(f"  log-log 斜率 = {slope:.3f} (R²={r2:.3f})  →  论文 Thm 3.7 预期 ≈ -0.5")
        p(f"  判定: {'与 T^{-1/2} 一致 (冒烟)' if abs(slope + 0.5) < 0.35 else '斜率偏离 -0.5, 本地版不成立或噪声主导'}")
        R["8B"] = {"T_list": T_list, "dT": dTs, "slope": float(slope), "r2": r2}
    else:
        p("  T 点不足, 跳过斜率拟合")
        R["8B"] = {"T_list": T_list, "dT": dTs, "slope": None}
    p("")

    # ================= 8C: 谱衰减指数 β vs 层可训练性 Δ_k =================
    p("--- 8C 谱衰减指数 β (attn_out, λ_i ∝ i^{-β}) vs 深度监督收益 Δ_k ---")
    betas, deltas = [], []
    for key, losses in models_loss.items():
        Lfull = [float(np.log(vocab))] + losses   # L[-1] = 随机基线
        for k in range(N_LAYERS):
            b = powerlaw_beta(models_W[key][f"L{k}.attn_out"])
            betas.append(b)
            deltas.append(Lfull[k] - Lfull[k + 1])
    rho, n_pts = spearman(betas, deltas)
    p(f"  β 分布: mean={np.nanmean(betas):.2f}, min={np.nanmin(betas):.2f}, "
      f"max={np.nanmax(betas):.2f}  (论文 suitability 窗口 α∈[2,6] 是 ESD 尾指数, "
      f"与 β 非同一量, 仅分布对照)")
    p(f"  Δ_k 分布: mean={np.nanmean(deltas):+.3f}, 正收益层 {sum(1 for d in deltas if d > 0)}/{len(deltas)}")
    p(f"  Spearman(β, Δ_k) = {rho:+.3f}  (n={n_pts})")
    if np.isfinite(rho):
        if rho > 0.3:
            v8c = "β 越大 (谱衰减越快) 层收益越大——支持'幂律谱层更可训练'方向"
        elif rho < -0.3:
            v8c = "β 越小 (谱越平) 层收益越大——与论文 suitability 方向相反, 记录负面"
        else:
            v8c = "无显著相关 (n 小 + 弱训练, 不足以判定)"
        p(f"  判定: {v8c}")
        R["8C"] = {"rho": float(rho), "n": n_pts, "verdict": v8c,
                   "beta_mean": float(np.nanmean(betas)), "delta_mean": float(np.nanmean(deltas))}
    else:
        R["8C"] = {"rho": None}
    p("")

    p("--- 总结论与诚实边界 ---")
    p(f"  8A {verdict8A} (域间/域内={ratio:.2f})")
    p(f"  8B 斜率={R['8B'].get('slope')}")
    p(f"  8C rho={R['8C'].get('rho')}")
    p("  边界: 6 层 dim=64 小模型 + 250 步弱训练; '领域'是同一仓库文件族 (弱跨域);")
    p("        每 T 仅 2 模型; β 与论文 α 不同量。以上为冒烟测试, 不构成验证/证伪。")
    p("        与论文的接口: 8A↔universality 主张, 8B↔Thm 3.7, 8C↔§B.1 suitability。")

    with open(os.path.join(OUT, "experiments_e8_results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    os.makedirs(os.path.join(ROOT, "experiments", "results"), exist_ok=True)
    with open(os.path.join(ROOT, "experiments", "results", "e8_subspace.json"), "w") as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    p(f"\n结果已写入 scripts/experiments_e8_results.txt + experiments/results/e8_subspace.json")

if __name__ == "__main__":
    main()
