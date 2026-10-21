"""GPU 版认知动力学实验整合脚本 (CUDA 感知, 放大版 E8-E12 + E13 先验预测).

设计 (2026-10-21): 把 CPU 冒烟版 experiments_e{8,9,11,12}.py 搬上 GPU 并放大
模型/数据/seed, 复刻同一套判据指标, 并新增 E13 (先验预测分水岭).
所有子命令共享语料与模型定义; 设备自动选择 cuda/cpu.

子命令: e9 e11 e12 e8 e13 all
  --device 自动; 默认 cuda (服务器设 CUDA_VISIBLE_DEVICES=0 避开被占的 GPU1)

输出: experiments/results/gpu_{exp}.json + 打印到 stdout (tee 到 txt 由调用方做)
"""
import os, re, glob, json, time, argparse, subprocess
import numpy as np
import torch, torch.nn as nn, torch.optim as optim

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

OUT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(OUT, ".."))
RESULTS = os.path.join(REPO, "experiments", "results")
os.makedirs(RESULTS, exist_ok=True)

CORPUS_PATTERNS = ["docs/wiki/*.md", "README.md", "README.zh.md", "AGENTS.md",
                   "CLAUDE.md", "LmPrinciple/*.lean", "paper/*.tex"]


# ---------------- 语料 ----------------
def load_corpus(max_chars=None):
    parts = []
    for pat in CORPUS_PATTERNS:
        for f in sorted(glob.glob(os.path.join(REPO, pat))):
            try:
                t = open(f, encoding="utf-8", errors="ignore").read()
                t = re.sub(r"%.*", "", t)
                t = re.sub(r"\s+", " ", t)
                parts.append(t)
            except Exception:
                pass
    txt = " ".join(parts)
    if max_chars:
        txt = txt[:max_chars]
    return txt


def build_vocab(text):
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    return chars, stoi, len(chars)


# ---------------- 模型 ----------------
class CharLM(nn.Module):
    """E9: 标准 6 层 MHA+FFN+残差 (输出仅末层)。"""
    def __init__(self, vocab, dim=256, heads=4, n_layers=6):
        super().__init__()
        self.embed = nn.Embedding(vocab, dim)
        self.layers = nn.ModuleList()
        self.ffs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, heads, batch_first=True))
            self.ffs.append(nn.Sequential(nn.Linear(dim, 4 * dim), nn.ReLU(), nn.Linear(4 * dim, dim)))
            self.norms.append(nn.LayerNorm(dim))
        self.exit = nn.Linear(dim, vocab)

    def forward(self, x):
        h = self.embed(x)
        for l, ff, nm in zip(self.layers, self.ffs, self.norms):
            a, _ = l(h, h, h)
            h = nm(h + a)
            h = h + ff(h)
        return self.exit(h)


class ResCharLM(nn.Module):
    """E11: skip ∈ {none, plain, gated}。"""
    def __init__(self, vocab, dim=256, heads=4, n_layers=6, skip="plain"):
        super().__init__()
        self.skip = skip
        self.embed = nn.Embedding(vocab, dim)
        self.layers = nn.ModuleList()
        self.ffs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, heads, batch_first=True))
            self.ffs.append(nn.Sequential(nn.Linear(dim, 4 * dim), nn.ReLU(), nn.Linear(4 * dim, dim)))
            self.norms.append(nn.LayerNorm(dim))
        if skip == "gated":
            self.alpha = nn.ParameterList([nn.Parameter(torch.full((dim,), 0.5)) for _ in range(n_layers)])
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


class TinyCharLM(nn.Module):
    """E12: 极小模型 (逆模式 vs 无梯度)。"""
    def __init__(self, vocab, dim=48, heads=4, n_layers=2):
        super().__init__()
        self.embed = nn.Embedding(vocab, dim)
        self.layers = nn.ModuleList()
        self.ffs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, heads, batch_first=True))
            self.ffs.append(nn.Sequential(nn.Linear(dim, 4 * dim), nn.ReLU(), nn.Linear(4 * dim, dim)))
            self.norms.append(nn.LayerNorm(dim))
        self.exit = nn.Linear(dim, vocab)

    def forward(self, x):
        h = self.embed(x)
        for l, ff, nm in zip(self.layers, self.ffs, self.norms):
            a, _ = l(h, h, h)
            h = nm(h + a)
            h = h + ff(h)
        return self.exit(h)


class DeepSupervisedCharLM(nn.Module):
    """E8: 每层都有 exit 的深度监督模型。"""
    def __init__(self, vocab, dim=128, heads=4, n_layers=6):
        super().__init__()
        self.embed = nn.Embedding(vocab, dim)
        self.layers = nn.ModuleList()
        self.ffs = nn.ModuleList()
        self.norms = nn.ModuleList()
        self.exits = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, heads, batch_first=True))
            self.ffs.append(nn.Sequential(nn.Linear(dim, 4 * dim), nn.ReLU(), nn.Linear(4 * dim, dim)))
            self.norms.append(nn.LayerNorm(dim))
            self.exits.append(nn.Linear(dim, vocab))

    def forward_exits(self, x):
        h = self.embed(x)
        outs = []
        for l, ff, nm, ex in zip(self.layers, self.ffs, self.norms, self.exits):
            a, _ = l(h, h, h)
            h = nm(h + a)
            h = h + ff(h)
            outs.append(ex(h))
        return outs


# ---------------- 训练工具 ----------------
def make_batch(data, split, seq=64, bs=16, device=DEVICE):
    X = torch.from_numpy(data).to(device)
    def make():
        ix = torch.randint(0, split - seq, (bs,)).to(device)
        xb = torch.stack([X[i:i + seq] for i in ix])
        yb = torch.stack([X[i + 1:i + seq + 1] for i in ix])
        return xb, yb
    return make, X


def train_model(model, make, vocab, steps, lr=3e-3, device=DEVICE):
    model.to(device)
    opt = optim.Adam(model.parameters(), lr=lr)
    crit = nn.CrossEntropyLoss()
    for _ in range(steps):
        xb, yb = make()
        opt.zero_grad()
        loss = crit(model(xb).reshape(-1, vocab), yb.reshape(-1))
        loss.backward()
        opt.step()
    return model


def eval_loss(model, xb, yb, vocab):
    with torch.no_grad():
        return nn.functional.cross_entropy(model(xb).reshape(-1, vocab), yb.reshape(-1)).item()


def n_params(model):
    return sum(p.numel() for p in model.parameters())


# ============================================================
# E9: 规模法则双区间 (放大)
# ============================================================
def run_e9(cfg):
    print(f"[E9] dims={cfg['dims']} Ts={cfg['Ts']} seeds={cfg['seeds']} steps={cfg['steps']} "
          f"device={DEVICE}")
    text = load_corpus(cfg.get("max_chars"))
    _, stoi, vocab = build_vocab(text)
    data = np.array([stoi[c] for c in text], dtype=np.int64)
    print(f"[E9] vocab={vocab} corpus={len(data)/1e3:.0f}K chars")
    L = {}
    for dim in cfg["dims"]:
        for T in cfg["Ts"]:
            T = min(T, len(data) - 1000)
            d = data[:T]
            split = int(T * 0.9)
            for seed in cfg["seeds"]:
                torch.manual_seed(seed)
                m = CharLM(vocab, dim=dim).to(DEVICE)
                make, X = make_batch(d, split, seq=cfg["seq"], bs=cfg["bs"])
                m = train_model(m, make, vocab, cfg["steps"], lr=cfg.get("lr", 3e-3))
                xb = X[split:split + cfg["seq"]].unsqueeze(0)
                yb = X[split + 1:split + 1 + cfg["seq"]].unsqueeze(0)
                loss = eval_loss(m, xb, yb, vocab)
                N = n_params(m)
                L[(dim, T, seed)] = (N, loss)
                print(f"   dim={dim:4d} T={T/1e3:6.1f}K seed{seed}: N={N:9d} loss={loss:.4f}", flush=True)
    # 汇总
    grid = {}
    for T in cfg["Ts"]:
        T = min(T, len(data) - 1000)
        for dim in cfg["dims"]:
            grid[(dim, T)] = float(np.mean([L[(dim, T, s)][1] for s in cfg["seeds"]]))
    print("\n[E9] --- loss 表 ---")
    print("   T\\dim |" + "".join(f"{d:>12d}" for d in cfg["dims"]))
    for T in cfg["Ts"]:
        T = min(T, len(data) - 1000)
        row = [grid[(d, T)] for d in cfg["dims"]]
        Ns = [L[(d, T, cfg["seeds"][0])][0] for d in cfg["dims"]]
        print(f"  {T/1e3:6.1f}K |" + "".join(f"{v:>12.4f}" for v in row) + f"   (N={Ns})")
    # 幂律斜率
    slopes = []
    for T in cfg["Ts"]:
        T = min(T, len(data) - 1000)
        vals = np.array([grid[(d, T)] for d in cfg["dims"]])
        floor = vals[-1]
        excess = vals[:-1] - floor
        ok = excess > 1e-4
        if ok.sum() >= 2:
            Ns = np.array([L[(d, T, cfg["seeds"][0])][0] for d in cfg["dims"][:-1]], float)
            sl, _ = np.polyfit(np.log(Ns[ok]), np.log(excess[ok]), 1)
            slopes.append(float(sl))
            print(f"  T={T/1e3:6.1f}K: 幂律斜率 (excess~N^{sl:.2f})")
    res = {"grid": {f"dim{d}_T{t}": v for (d, t), v in grid.items()},
           "params": {f"dim{d}": L[(d, cfg["Ts"][0], cfg["seeds"][0])][0] for d in cfg["dims"]},
           "powerlaw_slopes": slopes, "verdict": "GPU 放大版; 见打印"}
    with open(os.path.join(RESULTS, "gpu_e9.json"), "w") as f:
        json.dump(res, f, indent=2)
    print("[E9] 结果 -> experiments/results/gpu_e9.json")
    return res


# ============================================================
# E11: 残差消融 (放大)
# ============================================================
def run_e11(cfg):
    print(f"[E11] depths={cfg['depths']} skips={cfg['skips']} seeds={cfg['seeds']} "
          f"dim={cfg['dim']} steps={cfg['steps']} device={DEVICE}")
    text = load_corpus(cfg.get("max_chars"))
    _, stoi, vocab = build_vocab(text)
    data = np.array([stoi[c] for c in text], dtype=np.int64)
    split = int(len(data) * 0.9)
    res = {}
    for skip in cfg["skips"]:
        for d in cfg["depths"]:
            for seed in cfg["seeds"]:
                torch.manual_seed(seed)
                m = ResCharLM(vocab, dim=cfg["dim"], n_layers=d, skip=skip).to(DEVICE)
                make, X = make_batch(data, split, seq=cfg["seq"], bs=cfg["bs"])
                m = train_model(m, make, vocab, cfg["steps"], lr=cfg.get("lr", 3e-3))
                x1 = X[split:split + cfg["seq"]].unsqueeze(0)
                x2 = X[split + 500:split + 500 + cfg["seq"]].unsqueeze(0)
                loss = eval_loss(m, x1, x2, vocab)
                # 分离度: 两批次最终隐态 (复刻 CPU 版)
                h1 = m.embed(x1); h2 = m.embed(x2)
                for i, (l, ff, nm) in enumerate(zip(m.layers, m.ffs, m.norms)):
                    a1, _ = l(h1, h1, h1); b1 = ff(nm(h1 + a1))
                    a2, _ = l(h2, h2, h2); b2 = ff(nm(h2 + a2))
                    if m.skip == "none":
                        h1, h2 = b1, b2
                    elif m.skip == "plain":
                        h1, h2 = h1 + b1, h2 + b2
                    else:
                        g = torch.sigmoid(m.alpha[i])
                        h1, h2 = h1 + g * b1, h2 + g * b2
                sep = ((h1 - h2).norm() / (h1.norm() + h2.norm())).item()
                res[(skip, d, seed)] = (loss, sep)
                print(f"   [{skip:5s} L={d:2d} seed{seed}] loss={loss:.4f} sep={sep:.4f}", flush=True)
    # 汇总
    skips = cfg["skips"]; depths = cfg["depths"]
    print("\n[E11] --- 汇总 ---")
    slopes = {}
    for skip in skips:
        for d in depths:
            l = np.mean([res[(skip, d, s)][0] for s in cfg["seeds"]])
            s_ = np.mean([res[(skip, d, s)][1] for s in cfg["seeds"]])
            print(f"  {skip:5s} L={d:2d}: loss={l:.4f} sep={s_:.4f}")
        xs = np.array(depths, float)
        for tag, idx in [("loss", 0), ("sep", 1)]:
            ys = np.array([np.mean([res[(skip, d, s)][idx] for s in cfg["seeds"]]) for d in depths])
            sl, _ = np.polyfit(xs, ys, 1)
            slopes[(skip, tag)] = float(sl)
        print(f"  {skip:5s}: loss 斜率 {slopes[(skip,'loss')]:+.4f}/层, sep 斜率 {slopes[(skip,'sep')]:+.5f}/层")
    # L8 的真实信号是表征分离度: 无跳连随深度坍缩 vs 恒等路径跨深度恒定
    none_sep = {d: float(np.mean([res[("none", d, s)][1] for s in cfg["seeds"]])) for d in depths}
    plain_sep = {d: float(np.mean([res[("plain", d, s)][1] for s in cfg["seeds"]])) for d in depths}
    none_deep = none_sep[max(depths)]; none_shallow = none_sep[depths[0]]
    plain_mean = float(np.mean(list(plain_sep.values())))
    if none_deep < 0.05 and plain_mean > 0.15:
        verdict = "支持 L8: 无跳连深度>=4 完全坍缩(sep=0), 恒等路径跨深度恒定"
    elif none_deep < 0.5 * none_shallow:
        verdict = "方向支持: 无跳连分离度随深度显著下降"
    else:
        verdict = "未观测到差异"
    print(f"  [E11] none_sep(L2={none_shallow:.3f} -> L{max(depths)}={none_deep:.3f}); "
          f"plain_sep 均值={plain_mean:.3f}")
    print(f"  [E11] 判定: {verdict}")
    R = {"slopes": {f"{k[0]}_{k[1]}": v for k, v in slopes.items()},
         "grid": {f"{k[0]}_L{k[1]}_s{k[2]}": v for k, v in res.items()}, "verdict": verdict}
    with open(os.path.join(RESULTS, "gpu_e11.json"), "w") as f:
        json.dump(R, f, indent=2)
    print("[E11] -> experiments/results/gpu_e11.json")
    return R


# ============================================================
# E12: 逆模式 vs 无梯度 (放大)
# ============================================================
def _set_flat(params, flat):
    idx = 0
    for p in params:
        m = p.numel()
        p.data.copy_(flat[idx:idx + m].reshape(p.shape))
        idx += m


def run_e12(cfg):
    print(f"[E12] dim={cfg['dim']} layers={cfg['layers']} budget={cfg['budget']}s device={DEVICE}")
    text = load_corpus(cfg.get("max_chars"))
    _, stoi, vocab = build_vocab(text)
    data = np.array([stoi[c] for c in text], dtype=np.int64)
    split = int(len(data) * 0.9)
    make, X = make_batch(data, split, seq=cfg["seq"], bs=cfg["bs"])
    xb0 = X[split:split + cfg["seq"]].unsqueeze(0)
    yb0 = X[split + 1:split + 1 + cfg["seq"]].unsqueeze(0)

    def run_adam(model, budget):
        opt = optim.Adam(model.parameters(), lr=3e-3)
        crit = nn.CrossEntropyLoss()
        tr, t0, fwd = [], time.time(), 0
        while time.time() - t0 < budget:
            xb, yb = make()
            opt.zero_grad(); loss = crit(model(xb).reshape(-1, vocab), yb.reshape(-1))
            loss.backward(); opt.step(); fwd += 1
            tr.append(eval_loss(model, xb0, yb0, vocab))
        return tr, fwd

    def run_es(model, budget, lr, sigma, K=32):
        params = [p for p in model.parameters()]
        flat = torch.cat([p.data.reshape(-1) for p in params]).clone().to(DEVICE)
        n = flat.numel(); tr, t0, fwd = [], time.time(), 0
        xb_f, yb_f = make()  # 固定评估 batch 降噪 (标准 ES)
        while time.time() - t0 < budget:
            eps = torch.randn(K // 2, n, device=DEVICE)
            g = torch.zeros(n, device=DEVICE)
            for k in range(K // 2):
                for sgn in (1, -1):
                    _set_flat(params, flat + sgn * sigma * eps[k])
                    L = eval_loss(model, xb_f, yb_f, vocab)
                    g += sgn * L * eps[k]; fwd += 1
            g = g / (K * sigma); flat = flat - lr * g; _set_flat(params, flat)
            tr.append(eval_loss(model, xb0, yb0, vocab))
        return tr, fwd

    def run_hill(model, budget, sigma, K=32):
        params = [p for p in model.parameters()]
        flat = torch.cat([p.data.reshape(-1) for p in params]).clone().to(DEVICE)
        best = eval_loss(model, xb0, yb0, vocab); tr, t0, fwd = [], time.time(), 0
        xb_f, yb_f = make()
        while time.time() - t0 < budget:
            cands = []
            for _ in range(K):
                delta = torch.randn(flat.numel(), device=DEVICE) * sigma
                _set_flat(params, flat + delta)
                cands.append((eval_loss(model, xb_f, yb_f, vocab), delta)); fwd += 1
            cands.sort(key=lambda t: t[0])
            if cands[0][0] < best:
                best = cands[0][0]; flat = flat + cands[0][1]
            _set_flat(params, flat); tr.append(best)
        return tr, fwd

    B = cfg["budget"]
    torch.manual_seed(0); m = TinyCharLM(vocab, dim=cfg["dim"], n_layers=cfg["layers"]).to(DEVICE)
    N = n_params(m); l0 = eval_loss(m, xb0, yb0, vocab)
    tr_a, fwd_a = run_adam(m, B)
    best_lr, best_final = None, 1e9
    for lr in [1e-2, 3e-2, 5e-2]:
        torch.manual_seed(0); m = TinyCharLM(vocab, dim=cfg["dim"], n_layers=cfg["layers"]).to(DEVICE)
        tr, _ = run_es(m, 5.0, lr, 5e-3)
        if tr[-1] < best_final: best_final, best_lr = tr[-1], lr
    torch.manual_seed(0); m = TinyCharLM(vocab, dim=cfg["dim"], n_layers=cfg["layers"]).to(DEVICE)
    tr_e, fwd_e = run_es(m, B, best_lr, 5e-3)
    best_sig, best_final = None, 1e9
    for sig in [5e-3, 1e-2, 2e-2]:
        torch.manual_seed(0); m = TinyCharLM(vocab, dim=cfg["dim"], n_layers=cfg["layers"]).to(DEVICE)
        tr, _ = run_hill(m, 5.0, sig)
        if tr[-1] < best_final: best_final, best_sig = tr[-1], sig
    torch.manual_seed(0); m = TinyCharLM(vocab, dim=cfg["dim"], n_layers=cfg["layers"]).to(DEVICE)
    tr_h, fwd_h = run_hill(m, B, best_sig)
    drop_a, drop_e, drop_h = tr_a[-1] - tr_a[0], tr_e[-1] - tr_e[0], tr_h[-1] - tr_h[0]
    eff_a, eff_e, eff_h = drop_a / (fwd_a * 3), drop_e / fwd_e, drop_h / fwd_h
    ratio = eff_a / eff_e if eff_e else float("inf")
    ratio_h = eff_a / eff_h if eff_h else float("inf")
    print(f"  Adam: Δ={drop_a:+.4f} / {fwd_a*3} 当量 = {eff_a:+.3e}")
    print(f"  ES  : Δ={drop_e:+.4f} / {fwd_e} 当量 = {eff_e:+.3e}")
    print(f"  爬山: Δ={drop_h:+.4f} / {fwd_h} 当量 = {eff_h:+.3e}")
    print(f"  逆模式/ES 每 FLOP 效率比 = {ratio:.1f}× ; 逆模式/爬山 = {ratio_h:.1f}×")
    verdict = "支持 L7" if (ratio > 3 and ratio_h > 3) else (
        "方向支持" if (ratio > 1.5 and ratio_h > 1.5) else "差距不显著")
    print(f"  [E12] 判定: {verdict} (N={N})")
    R = {"n_params": N, "efficiency": {"adam": eff_a, "es": eff_e, "hillclimb": eff_h, "ratio": ratio},
         "verdict": verdict}
    with open(os.path.join(RESULTS, "gpu_e12.json"), "w") as f:
        json.dump(R, f, indent=2)
    print("[E12] -> experiments/results/gpu_e12.json")
    return R


# ============================================================
# E8: 普适权重子空间 (放大)
# ============================================================
def collect_weights(model):
    sd = model.state_dict(); W = {"embed": sd["embed.weight"].detach().cpu().numpy()}
    for i in range(len(model.layers)):
        W[f"L{i}.attn_in"] = sd[f"layers.{i}.in_proj_weight"].detach().cpu().numpy()
        W[f"L{i}.attn_out"] = sd[f"layers.{i}.out_proj.weight"].detach().cpu().numpy()
        W[f"L{i}.ffn_up"] = sd[f"ffs.{i}.0.weight"].detach().cpu().numpy()
        W[f"L{i}.ffn_down"] = sd[f"ffs.{i}.2.weight"].detach().cpu().numpy()
        W[f"L{i}.exit"] = sd[f"exits.{i}.weight"].detach().cpu().numpy()
    return W


def pca_explained(stack):
    Xc = stack - stack.mean(0, keepdims=True)
    s = np.linalg.svd(Xc, compute_uv=False)
    tot = (s ** 2).sum()
    if tot <= 0: return [float("nan")] * 8
    return [float((s[:k] ** 2).sum() / tot) for k in range(1, 9)]


def top_basis(stack, r):
    Xc = stack - stack.mean(0, keepdims=True)
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
    return Vt[:r].T


def subspace_dist(Va, Vb):
    M = Va.T @ Vb; sv = np.clip(np.linalg.svd(M, compute_uv=False), 0, 1)
    c2 = sv ** 2
    return float(np.sqrt(max(0, 1 - c2.mean())))


def powerlaw_beta(W, lo=16, hi=32):
    s = np.linalg.svd(W, compute_uv=False); lam = s ** 2; n = len(lam)
    hi = min(hi, n - 1)
    if hi <= lo + 2: return float("nan")
    idx = np.arange(lo, hi + 1); good = lam[lo:hi + 1] > 0
    if good.sum() < 4: return float("nan")
    b, _ = np.polyfit(np.log(idx[good]), np.log(lam[lo:hi + 1][good]), 1)
    return float(-b)


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y); x, y = x[ok], y[ok]
    if len(x) < 4: return float("nan"), len(x)
    rx = np.argsort(np.argsort(x)).astype(float) - np.mean(np.arange(len(x)))
    ry = np.argsort(np.argsort(y)).astype(float) - np.mean(np.arange(len(y)))
    den = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return (float((rx * ry).sum() / den) if den > 0 else float("nan")), len(x)


def run_e8(cfg):
    print(f"[E8] domains=4 seeds={cfg['seeds']} dim={cfg['dim']} steps={cfg['steps']} device={DEVICE}")
    GROUPS = {"docs": ["docs/wiki/*.md"], "readme": ["README.md", "README.zh.md", "AGENTS.md", "CLAUDE.md"],
              "lean": ["LmPrinciple/*.lean"], "tex": ["paper/*.tex"]}
    groups = {}
    for g, pats in GROUPS.items():
        parts = []
        for pat in pats:
            for f in sorted(glob.glob(os.path.join(REPO, pat))):
                t = open(f, encoding="utf-8", errors="ignore").read()
                parts.append(re.sub(r"\s+", " ", re.sub(r"%.*", "", t)))
        groups[g] = " ".join(parts)[:cfg.get("cap", 60000)]
    full = " ".join(groups.values())
    _, stoi, vocab = build_vocab(full)
    data_full = np.array([stoi[c] for c in full], dtype=np.int64)
    NL = cfg["layers"]
    models_W, models_loss = {}, {}
    for g in GROUPS:
        d = np.array([stoi[c] for c in groups[g]], dtype=np.int64)
        split = int(len(d) * 0.9)
        for seed in cfg["seeds"]:
            torch.manual_seed(seed)
            m = DeepSupervisedCharLM(vocab, dim=cfg["dim"], n_layers=NL).to(DEVICE)
            make, X = make_batch(d, split, seq=cfg["seq"], bs=cfg["bs"])
            crit = nn.CrossEntropyLoss(); opt = optim.Adam(m.parameters(), lr=cfg.get("lr", 3e-3))
            for _ in range(cfg["steps"]):
                xb, yb = make(); outs = m.forward_exits(xb)
                loss = torch.stack([crit(o.reshape(-1, vocab), yb.reshape(-1)) for o in outs]).mean()
                opt.zero_grad(); loss.backward(); opt.step()
            with torch.no_grad():
                xb = X[split:split + cfg["seq"]].unsqueeze(0)
                yb = X[split + 1:split + 1 + cfg["seq"]].unsqueeze(0)
                losses = [crit(o.reshape(-1, vocab), yb.reshape(-1)).item() for o in m.forward_exits(xb)]
            models_W[(g, seed)] = collect_weights(m); models_loss[(g, seed)] = losses
            print(f"  [{g} seed{seed}] exits={[f'{v:.3f}' for v in losses]}", flush=True)
    TENSOR_NAMES = list(models_W[("docs", cfg["seeds"][0])].keys())
    # 8A
    def stack_group(keys, name):
        return np.stack([models_W[k][name].reshape(-1) for k in keys], 0)

    def stack_list(dicts, name):
        return np.stack([d[name].reshape(-1) for d in dicts], 0)
    evo = np.nanmean([pca_explained(stack_group(list(models_W), n)) for n in TENSOR_NAMES], 0)
    r = 8
    gs = list(GROUPS)
    pooled = {g: {n: top_basis(stack_group([(g, s) for s in cfg["seeds"]], n), r) for n in TENSOR_NAMES} for g in gs}
    within = []
    for g in gs:
        ds = []
        for n in TENSOR_NAMES:
            for s1, s2 in [(0, 1), (0, 2), (1, 2)] if len(cfg["seeds"]) >= 3 else [(0, 1)]:
                sub = top_basis(stack_group([(g, s1), (g, s2)], n), r)
                ds.append(subspace_dist(sub, pooled[g][n]))
        within.append(float(np.mean(ds)))
    cross = []
    for i in range(len(gs)):
        for j in range(i + 1, len(gs)):
            ds = [subspace_dist(pooled[gs[i]][n], pooled[gs[j]][n]) for n in TENSOR_NAMES]
            cross.append(float(np.mean(ds)))
    mw, mc = float(np.mean(within)), float(np.mean(cross))
    ratio = mc / mw if mw > 0 else float("nan")
    print(f"  [8A] 域内={mw:.3f} 域间={mc:.3f} 比={ratio:.2f}")
    print(f"  [8A] top-k 方差: " + ", ".join(f"k{k+1}={evo[k]*100:.0f}%" for k in range(8)))
    # 8B (修正版: 同 seed 跨数据拆分, K 模型)
    K = cfg.get("K8b", 5)
    T_list = [min(t, len(data_full) // 2) for t in cfg.get("T8b", [20000, 60000, 100000])]
    T_list = [t for t in T_list if 2 * t <= len(data_full)]
    dTs = []
    for T in T_list:
        WA = [collect_weights(DeepSupervisedCharLM(vocab, dim=cfg["dim"], n_layers=NL).to(DEVICE)) for _ in range(K)]
        WB = [collect_weights(DeepSupervisedCharLM(vocab, dim=cfg["dim"], n_layers=NL).to(DEVICE)) for _ in range(K)]
        # 同 seed 跨数据
        for kk in range(K):
            torch.manual_seed(100 + kk)
            m = DeepSupervisedCharLM(vocab, dim=cfg["dim"], n_layers=NL).to(DEVICE)
            make, X = make_batch(data_full[:T], int(T * 0.9), seq=cfg["seq"], bs=cfg["bs"])
            opt = optim.Adam(m.parameters(), lr=cfg.get("lr", 3e-3))
            for _ in range(cfg["steps"]):
                xb, yb = make(); outs = m.forward_exits(xb)
                loss = torch.stack([crit(o.reshape(-1, vocab), yb.reshape(-1)) for o in outs]).mean()
                opt.zero_grad(); loss.backward(); opt.step()
            WA[kk] = collect_weights(m)
            torch.manual_seed(100 + kk)
            m = DeepSupervisedCharLM(vocab, dim=cfg["dim"], n_layers=NL).to(DEVICE)
            make, X = make_batch(data_full[T:2 * T], int(T * 0.9), seq=cfg["seq"], bs=cfg["bs"])
            opt = optim.Adam(m.parameters(), lr=cfg.get("lr", 3e-3))
            for _ in range(cfg["steps"]):
                xb, yb = make(); outs = m.forward_exits(xb)
                loss = torch.stack([crit(o.reshape(-1, vocab), yb.reshape(-1)) for o in outs]).mean()
                opt.zero_grad(); loss.backward(); opt.step()
            WB[kk] = collect_weights(m)
        ds = [subspace_dist(top_basis(stack_list(WA, n), 2), top_basis(stack_list(WB, n), 2)) for n in TENSOR_NAMES]
        dT = float(np.mean(ds)); dTs.append(dT)
        print(f"  [8B] T={T/1e3:.0f}K d(T)={dT:.4f}", flush=True)
    slope8b = None
    if len(dTs) >= 2 and all(d > 0 for d in dTs):
        slope8b, _ = np.polyfit(np.log(T_list), np.log(dTs), 1)
        print(f"  [8B] log-log 斜率={slope8b:.3f} (预期≈-0.5)")
    # 8C
    betas, deltas = [], []
    for key, losses in models_loss.items():
        Lfull = [float(np.log(vocab))] + losses
        for k in range(NL):
            betas.append(powerlaw_beta(models_W[key][f"L{k}.attn_out"]))
            deltas.append(Lfull[k] - Lfull[k + 1])
    rho, n_pts = spearman(betas, deltas)
    print(f"  [8C] Spearman(β,Δ_k)={rho:+.3f} (n={n_pts})")
    R = {"8A": {"within": within, "cross": cross, "mean_within": mw, "mean_cross": mc, "ratio": ratio,
                "topk": evo.tolist()},
         "8B": {"T_list": T_list, "dT": dTs, "slope": slope8b},
         "8C": {"rho": rho, "n": n_pts, "beta_mean": float(np.nanmean(betas))}}
    with open(os.path.join(RESULTS, "gpu_e8.json"), "w") as f:
        json.dump(R, f, indent=2)
    print("[E8] -> experiments/results/gpu_e8.json")
    return R


# ============================================================
# E13: 先验预测分水岭 (测数据谱 + xz 熵地板 -> 对照 E9 网格)
# ============================================================
def run_e13():
    print(f"[E13] 先验预测: 测语料谱尾指数 β + xz 熵地板, 对照 gpu_e9 网格 device={DEVICE}")
    import gzip
    text = load_corpus()
    _, stoi, vocab = build_vocab(text)
    data = np.array([stoi[c] for c in text], dtype=np.int64)
    # ① 熵地板 (xz 压缩率)
    raw = (" ".join(text)).encode("utf-8")
    try:
        comp = subprocess.run(["xz", "--stdout", "-9"], input=raw, capture_output=True).stdout
        hfloor_bits = 8.0 * len(comp) / len(raw)
    except Exception as e:
        comp = b""
        hfloor_bits = float("nan")
        print(f"  xz 不可用: {e}")
    hfloor_nats = hfloor_bits * np.log(2)
    print(f"  语料 {len(raw)} 字符; xz 压缩 {len(comp)} 字节; H_floor ≈ {hfloor_bits:.3f} bits/char = {hfloor_nats:.3f} nats/char")
    # ② 数据谱尾指数 β: 字符转移共现矩阵 SVD
    M = np.zeros((vocab, vocab))
    for i in range(len(data) - 1):
        M[data[i], data[i + 1]] += 1
    s = np.linalg.svd(M, compute_uv=False)
    lam = s ** 2
    lo, hi = 4, min(40, vocab - 1)
    idx = np.arange(lo, hi + 1); good = lam[lo:hi + 1] > 0
    b_data, _ = np.polyfit(np.log(idx[good]), np.log(lam[lo:hi + 1][good]), 1)
    beta_data = float(-b_data)
    print(f"  转移矩阵谱尾指数 β_data = {beta_data:.3f} (λ_i ∝ i^(-β))")
    # ③ 读 E9 网格: 取最小实测 loss 与其配置 (数据受限区下最大模型非地板, 幂律-over-N 无定义)
    e9 = json.load(open(os.path.join(RESULTS, "gpu_e9.json")))
    grid = e9["grid"]; params = e9["params"]
    dims = sorted({int(k.split("_")[0][3:]) for k in grid})
    Ts = sorted({int(k.split("_")[1][1:]) for k in grid})
    min_key = min(grid, key=grid.get)
    min_loss = grid[min_key]
    d_min = int(min_key.split("_")[0][3:]); T_min = int(min_key.split("_")[1][1:])
    fit_slopes = []
    for T in Ts:
        vals = np.array([grid[f"dim{d}_T{T}"] for d in dims])
        floor = vals[-1]
        excess = vals[:-1] - floor
        ok = excess > 1e-4
        if ok.sum() >= 2:
            Ns = np.array([params[f"dim{d}"] for d in dims[:-1]], float)
            sl, _ = np.polyfit(np.log(Ns[ok]), np.log(excess[ok]), 1)
            fit_slopes.append((T, float(sl)))
            print(f"  E9 T={T/1e3:.0f}K: 实测超额幂律斜率 β_fit = {-sl:.3f}")
    mean_fit = float(np.mean([s for _, s in fit_slopes])) if fit_slopes else float("nan")
    # ④ 缺口: 实测最小 loss 与熵地板之差 = 容量不足+优化缺口+估计误差 (三混合, 目前不可单独算)
    gap = min_loss - hfloor_nats
    print(f"  E9 最小实测 loss = {min_loss:.3f} nats (dim{d_min}, T={T_min/1e3:.0f}K)")
    print(f"  熵地板 H_floor = {hfloor_nats:.3f} nats; 不可约缺口 = {gap:.3f} nats "
          f"(= 容量不足+优化缺口+估计误差, 理论未拆分)")
    # ⑤ 判定
    if np.isnan(mean_fit):
        verdict = (f"E13 分水岭部分成立: 熵地板已先验测出 ({hfloor_nats:.2f} nats), "
                   f"E9 最小实测 {min_loss:.2f} nats, 差 {gap:.2f} nats 即预测差距; "
                   f"β 形状预测因数据受限区(最大模型非地板)暂不可定义")
    elif abs(beta_data - mean_fit) < 0.6:
        verdict = f"支持 E13: β_data={beta_data:.2f} ≈ β_fit={mean_fit:.2f} (先验预测成立)"
    else:
        verdict = f"未对齐: β_data={beta_data:.2f} vs β_fit={mean_fit:.2f} (记录差异)"
    print(f"  [E13] 判定: {verdict}")
    R = {"hfloor_nats": hfloor_nats, "hfloor_bits": hfloor_bits, "beta_data": beta_data,
         "beta_fit_per_T": fit_slopes, "beta_fit_mean": mean_fit,
         "e9_min_loss": min_loss, "e9_min_config": {"dim": d_min, "T": T_min},
         "prediction_gap_nats": gap, "verdict": verdict}
    with open(os.path.join(RESULTS, "gpu_e13.json"), "w") as f:
        json.dump(R, f, indent=2)
    print("[E13] -> experiments/results/gpu_e13.json")
    return R


# ---------------- 配置 ----------------
DEFAULTS = {
    "e9":  {"dims": [128, 256, 512], "Ts": [200_000, 600_000, 900_000], "seeds": [0, 1],
            "steps": 1500, "seq": 128, "bs": 64},
    "e11": {"depths": [2, 4, 6, 8, 12], "skips": ["none", "plain", "gated"], "seeds": [0, 1],
            "dim": 256, "steps": 800, "seq": 128, "bs": 64},
    "e12": {"dim": 48, "layers": 2, "budget": 15.0, "seq": 128, "bs": 64},
    "e8":  {"seeds": [0, 1, 2], "dim": 128, "layers": 6, "steps": 400, "seq": 128, "bs": 64,
            "cap": 60000, "K8b": 5, "T8b": [20000, 60000, 100000]},
}


def cfg_for(name, args):
    c = dict(DEFAULTS[name])
    if args.dims:
        c["dims"] = [int(x) for x in args.dims.split(",")]
    if args.Ts:
        c["Ts"] = [int(x) for x in args.Ts.split(",")]
    if args.steps:
        c["steps"] = args.steps
    if args.seeds:
        c["seeds"] = [int(x) for x in args.seeds.split(",")]
    if args.lr:
        c["lr"] = args.lr
    if args.budget is not None:
        c["budget"] = args.budget
    if args.max_chars:
        c["max_chars"] = args.max_chars
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp", choices=["e9", "e11", "e12", "e8", "e13", "all"])
    ap.add_argument("--max_chars", type=int, default=None)
    ap.add_argument("--dims", type=str, default=None)
    ap.add_argument("--Ts", type=str, default=None)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--seeds", type=str, default=None)
    ap.add_argument("--lr", type=float, default=None)
    ap.add_argument("--budget", type=float, default=None)
    args = ap.parse_args()
    print(f"=== gpu_experiments [{args.exp}] device={DEVICE} ===")
    if args.exp == "e9" or args.exp == "all":
        run_e9(cfg_for("e9", args))
    if args.exp == "e11" or args.exp == "all":
        run_e11(cfg_for("e11", args))
    if args.exp == "e12" or args.exp == "all":
        run_e12(cfg_for("e12", args))
    if args.exp == "e8" or args.exp == "all":
        run_e8(cfg_for("e8", args))
    if args.exp == "e13" or args.exp == "all":
        run_e13()


if __name__ == "__main__":
    main()
