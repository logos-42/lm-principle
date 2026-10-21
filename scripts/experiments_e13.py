"""E13 分水岭实验: 先验预测 (从"训练后测量"走向"先算后对照")

设计 (docs/wiki/predictive-gap.md §4):
  S1 测数据谱: 对语料做 (上下文 h-gram -> 下一字符) 的加权协方差 SVD, 得 {λ_i},
     幂律指数 α, 有效秩; 全部只用数据, 不碰 loss。
  S2 测熵地板: xz/LZMA 压缩率 -> H_floor (nats/char); unigram 交叉熵 -> D_0。
  S3 组装预测: L̂(N,T) = H_floor + D(R(N)),
     D = 逆向注水 (reverse water-filling) 的率-失真失真量,
     谱按 Σλ = D_0 归一 (量纲来自数据, 不是 loss);
     R(N) = ln( N · n² / (3 d²) )  ← Efficiency.lean 的每参数交互率 (计数界取对数),
     零个从 loss 拟合出来的参数。
     ★ 预测结果在任何训练开始之前写盘 (带 sha256 + 时间戳), 供事后核对顺序。
  S4 训练 (GPU): 与 E9 同族 CharLM, dim ∈ 网格, T ∈ 网格, 多 seed,
     测试集 = 训练前缀之后的尾部整段 (不再用 64 字符单窗)。
  S5 对照 + 反演诊断: 用实测 L 反演 R_eff(N) (注水反解),
     检验 log R_eff vs log N 是否幂律 —— 这是缺口 #2 (架构→可达率) 的实证探测。
     再用 "小 dim 拟合 a,γ / 大 dim 预测" 的留出检验看封闭式映射是否存在。

用法:
  python experiments_e13.py --device cuda          # 正式
  python experiments_e13.py --device cpu --scale smoke   # 冒烟 (写 *_smoke.json)
"""
import argparse, glob, hashlib, json, lzma, math, os, re, time
import numpy as np
import torch, torch.nn as nn, torch.optim as optim

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, ".."))
RES = os.path.join(ROOT, "experiments", "results")


# ─────────────────────────── 语料 ───────────────────────────
def block_split(data, bs=256, seed=12345, frac=(0.8, 0.1, 0.1)):
    """块级随机 80/10/10 划分 (演示/验证/测试)。

    为什么不用"尾部 10%": 本语料是 wiki+Lean+tex 混合体, 各段难度差很大
    (实测 val 5.42 vs test 4.97 同模型差 0.45 nats) —— 尾部单窗会把"文件异质性"
    混进 loss, 噪声地板远大于要检验的效应。块级随机划分让三个集合覆盖同一分布,
    代价是失去"预测未来文本"的语义 (E13 测的是容量可达损失, 不是前瞻泛化)。
    """
    n = len(data)
    nb = n // bs
    blocks = [data[i * bs:(i + 1) * bs] for i in range(nb)]
    rng = np.random.RandomState(seed)
    perm = rng.permutation(nb)
    ntr = int(nb * frac[0]); nva = int(nb * frac[1])
    parts = {"train": perm[:ntr], "val": perm[ntr:ntr + nva], "test": perm[ntr + nva:]}
    out = {}
    for k, v in parts.items():
        out[k] = (np.concatenate([blocks[i] for i in sorted(v)])
                  if len(v) else np.zeros(0, dtype=data.dtype))
    return out


def load_corpus(limit=170_000):
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
    return " ".join(parts)[:limit]


# ─────────────────── S1 数据谱 (仅数据) ───────────────────
def context_spectrum(data, vocab, h=8, min_count=5, max_contexts=400_000, max_rows=50_000):
    """(h-gram ctx -> next char) 的加权协方差谱。

    对每个上下文 c: p_c = 下一字符条件分布 (V 维), 权重 w_c = count_c / 总位置。
    Σ = Σ_c w_c (p_c − p̄)(p_c − p̄)ᵀ  (V×V), p̄ = 位置加权的边缘分布。
    λ_i 降序 = "可预测结构" 在各方向上的方差预算。
    同时算 I(ctx;next) = Σ w_c KL(p_c‖p̄) (nats) — 数据侧的可利用信息量。
    """
    n = len(data) - h
    counts = {}
    for i in range(n):
        key = data[i:i + h].tobytes()
        c = counts.get(key)
        if c is None:
            if len(counts) >= max_contexts:
                continue
            c = counts[key] = np.zeros(vocab, dtype=np.float32)
        c[data[i + h]] += 1
    rows, wts = [], []
    total = 0.0
    for c in counts.values():
        s = c.sum()
        if s >= min_count:
            rows.append(c / s)
            wts.append(s)
            total += s
    if not rows:
        raise RuntimeError("contexts 太少")
    wts = np.asarray(wts, dtype=np.float64)
    if len(rows) > max_rows:                      # 大 T 时按计数取头部, 覆盖质量单列报告
        order = np.argsort(wts)[::-1][:max_rows]
        rows = [rows[i] for i in order]
        wts = wts[order]
    coverage = float(wts.sum() / total)
    P = np.asarray(rows, dtype=np.float64)            # (m, V) 条件分布
    w = wts / wts.sum()                               # 归一权重, Σw = 1
    pbar = w @ P                                      # 边缘分布
    # Σ = Pᵀ diag(w) P − p̄p̄ᵀ  (一次 BLAS, 避免逐行 outer)
    Sig = (P * w[:, None]).T @ P - np.outer(pbar, pbar)
    Sig = 0.5 * (Sig + Sig.T)
    mi = float(np.sum(w * np.sum(P * np.log(np.maximum(P, 1e-300) / np.maximum(pbar, 1e-300)), axis=1)))
    lam = np.linalg.eigvalsh(Sig)[::-1]
    lam = np.clip(lam, 0.0, None)
    lam_sum = float(lam.sum())
    pn = lam / max(lam_sum, 1e-12)
    ent = -float(np.sum(pn[pn > 0] * np.log(pn[pn > 0])))
    eff_rank = float(np.exp(ent))
    # 90% 能量秩
    cum = np.cumsum(pn)
    r90 = int(np.searchsorted(cum, 0.90) + 1)
    # 幂律指数 α: log λ_i ~ −α log i, 用 i ∈ [2, min(200, k)] 里 λ>0 的点
    kmax = min(512, len(lam))
    idx = np.arange(2, min(200, kmax) + 1)
    ok = lam[idx - 1] > lam_sum * 1e-9
    alpha = float("nan")
    if ok.sum() >= 3:
        alpha = float(-np.polyfit(np.log(idx[ok]), np.log(lam[idx[ok] - 1]), 1)[0])
    kept = float(lam[:kmax].sum() / max(lam_sum, 1e-12))
    return {
        "h": h, "n_contexts": len(counts), "n_used": len(rows),
        "lambda": [float(x) for x in lam[:kmax]],
        "lambda_sum": lam_sum, "alpha": alpha,
        "eff_rank": eff_rank, "rank90": r90, "mutual_info_nats": mi,
        "max_share": float(pn[0]), "mass_kept": kept, "context_coverage": coverage,
        "n_rows_used": int(P.shape[0]),
    }


# ─────────────────── S2 熵地板 (仅数据) ───────────────────
def xz_rate(text, preset=9):
    raw = text.encode("utf-8", errors="ignore")
    if not raw:
        return float("nan")
    comp = lzma.compress(raw, format=lzma.FORMAT_ALONE, preset=preset)
    return len(comp) * 8.0 * math.log(2.0) / len(raw)   # nats / byte (≈ per char here)


def xz_conditional_rate(train_txt, test_txt, preset=9):
    """条件压缩率: [LZMA(train+test) − LZMA(train)] 折算到 test 每字符 —— 自适应的
    "看过训练集之后, 预测这段文本还要多少 nats"。比单段 xz 稳定得多 (无窗口 overhead 偏差)。"""
    a = train_txt.encode("utf-8", errors="ignore")
    b = test_txt.encode("utf-8", errors="ignore")
    if not b:
        return float("nan")
    ca = len(lzma.compress(a, format=lzma.FORMAT_ALONE, preset=preset))
    cab = len(lzma.compress(a + b, format=lzma.FORMAT_ALONE, preset=preset))
    return max(cab - ca, 0) * 8.0 * math.log(2.0) / len(b)


def unigram_ce(train_ids, test_ids, vocab):
    cnt = np.bincount(train_ids, minlength=vocab).astype(np.float64) + 1e-9
    p = cnt / cnt.sum()
    return float(-np.mean(np.log(p[test_ids])))


def order_h_entropy(train_ids, test_ids, vocab, h=8):
    """顺序 h 的插件熵 (在 test 上平均): 只用 train 的条件分布, 极少见的 ctx 回退到 unigram。"""
    cnt_u = np.bincount(train_ids, minlength=vocab).astype(np.float64) + 1e-9
    pu = cnt_u / cnt_u.sum()
    tab = {}
    for i in range(len(train_ids) - h):
        key = train_ids[i:i + h].tobytes()
        a = tab.get(key)
        if a is None:
            a = tab[key] = np.zeros(vocab, dtype=np.float64)
        a[train_ids[i + h]] += 1
    tot = 0.0
    k = 0
    for i in range(len(test_ids) - h):
        key = test_ids[i:i + h].tobytes()
        a = tab.get(key)
        tgt = test_ids[i + h]
        if a is not None and a.sum() >= 2:
            q = (a + 1e-3) / (a.sum() + 1e-3 * vocab)
        else:
            q = pu
        tot += -math.log(q[tgt]); k += 1
    return tot / max(k, 1)


# ─────────────── S3 率-失真 (逆向注水) ───────────────
def waterfill_D(lam, R):
    """Σ_i min(λ_i, θ), θ 满足 Σ_{λ_i>θ} ½ ln(λ_i/θ) = R。R=0 ⟹ 全失真 Σλ。"""
    lam = np.asarray(lam, dtype=np.float64)
    tot = float(lam.sum())
    if R <= 0:
        return tot
    lo, hi = 1e-12 * max(tot, 1e-12), float(lam.max()) + 1e-12
    for _ in range(200):
        th = math.sqrt(lo * hi)
        r = float(np.sum(0.5 * np.log(lam[lam > th] / th)))
        if r > R:
            lo = th
        else:
            hi = th
    th = math.sqrt(lo * hi)
    return float(np.sum(np.minimum(lam, th)))


def R_of_D(lam, D, iters=80):
    """反演: 给定失真 D, 求达到它所需的率 R (nats)。二分 D(R) 单调。"""
    lam = np.asarray(lam, dtype=np.float64)
    tot = float(lam.sum())
    if D >= tot:
        return 0.0
    if D <= 0:
        return float("inf")
    th_lim = max(float(lam.max()), 1e-300) * 1e-12
    hi = float(np.sum(0.5 * np.maximum(0.0, np.log(np.maximum(lam, th_lim) / th_lim)))) + 10.0
    lo = 0.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if waterfill_D(lam, mid) > D:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def interaction_rate(N, seq, dim):
    """Efficiency.lean: 注意力每参数交互率 n²/(3d²); 总交互数取对数 = 率 (nats)。"""
    I = N * (seq ** 2) / (3.0 * dim ** 2)
    return float(math.log(max(I, 1.0)))


# ─────────────────── 模型 / 训练 (GPU) ───────────────────
class CharLM(nn.Module):
    def __init__(self, vocab, dim=64, heads=4, n_layers=6):
        super().__init__()
        self.embed = nn.Embedding(vocab, dim)
        self.layers = nn.ModuleList()
        self.ffs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.MultiheadAttention(dim, heads, batch_first=True))
            self.ffs.append(nn.Sequential(nn.Linear(dim, 4 * dim), nn.ReLU(),
                                          nn.Linear(4 * dim, dim)))
            self.norms.append(nn.ModuleList([nn.LayerNorm(dim), nn.LayerNorm(dim)]))
        self.norm_f = nn.LayerNorm(dim)      # pre-LN + 末端归一: 3000 步不发散
        self.exit = nn.Linear(dim, vocab)

    def forward(self, x):
        h = self.embed(x)
        for l, ff, ns in zip(self.layers, self.ffs, self.norms):
            a = ns[0](h)
            a, _ = l(a, a, a)
            h = h + a
            h = h + ff(ns[1](h))
        return self.exit(self.norm_f(h))


def eval_loss(model, seg, vocab, seq, crit, device, bs=256):
    """按 256 字符块逐窗评估 (窗口不跨块), 按 token 加权。"""
    B = torch.from_numpy(seg).to(device)
    tot, cnt = 0.0, 0
    nb = len(seg) // bs
    with torch.no_grad():
        for b in range(nb):
            for s in range(b * bs, (b + 1) * bs - seq, seq):
                xb = B[s:s + seq].unsqueeze(0)
                yb = B[s + 1:s + seq + 1].unsqueeze(0)
                l = crit(model(xb).reshape(-1, vocab), yb.reshape(-1)).item()
                tot += l * seq; cnt += seq
    return tot / max(cnt, 1)


def train_eval(splits, vocab, dim, seed, steps, bs, seq, device, heads=4, n_layers=6,
               lr=1e-3, warmup=200, clip=1.0, eval_every=100, block=256, patience=800):
    """块级 80/10/10: train / val (选 checkpoint) / test (报告)。

    "可达最优损失" = val 最优那一步的 test loss —— 容量预测 L̂ 对应的是
    给定 (N, T) 能达到的最好水平, 不是某个固定步数的水平 (否则测的是过拟合)。
    """
    tr, val, te = splits["train"], splits["val"], splits["test"]
    torch.manual_seed(seed)
    model = CharLM(vocab, dim=dim, heads=heads, n_layers=n_layers).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    opt = optim.Adam(model.parameters(), lr=lr)
    sched = optim.lr_scheduler.LambdaLR(
        opt, lambda t: min(1.0, (t + 1) / warmup) * (0.1 + 0.9 * 0.5 *
                                                     (1 + math.cos(math.pi * min(1.0, t / steps)))))
    crit = nn.CrossEntropyLoss()
    trb = len(tr) // block
    X = torch.from_numpy(tr).to(device)
    t0 = time.time()
    best = {"val": float("inf"), "step": -1, "state": None}
    model.train()
    for t in range(steps):
        opt.zero_grad()
        bi = torch.randint(0, trb, (bs,))
        st = bi * block + torch.randint(0, block - seq - 1, (bs,))
        xb = torch.stack([X[i:i + seq] for i in st])
        yb = torch.stack([X[i + 1:i + seq + 1] for i in st])
        loss = crit(model(xb).reshape(-1, vocab), yb.reshape(-1))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        opt.step()
        sched.step()
        if (t + 1) % eval_every == 0 or t == steps - 1:
            model.eval()
            vl = eval_loss(model, val, vocab, seq, crit, device, block)
            if vl < best["val"]:
                best = {"val": vl, "step": t + 1,
                        "state": {k: v.detach().clone() for k, v in model.state_dict().items()}}
            model.train()
            if best["step"] > 0 and (t + 1) - best["step"] >= patience:
                steps_done = t + 1
                break
    model.eval()
    if best["state"] is not None:
        model.load_state_dict(best["state"])
    test_best = eval_loss(model, te, vocab, seq, crit, device, block)
    train_at_best = eval_loss(model, tr, vocab, seq, crit, device, block)
    return {"n_params": n_params, "test_loss": test_best,
            "val_loss": best["val"], "best_step": best["step"],
            "train_loss": train_at_best, "steps": steps,
            "steps_done": locals().get("steps_done", steps),
            "test_tokens": (len(te) // block) * ((block - seq) // seq) * seq,
            "secs": time.time() - t0, "device": str(device)}


# ─────────────────── main ───────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="auto")
    ap.add_argument("--scale", default="full", choices=["smoke", "full"])
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--seq", type=int, default=64)
    ap.add_argument("--bs", type=int, default=64)
    ap.add_argument("--ctx", type=int, default=8, help="谱测量的上下文长度 h")
    args = ap.parse_args()

    if args.device == "auto":
        args.device = "cuda" if torch.cuda.is_available() else "cpu"
    dev = torch.device(args.device)
    if args.scale == "smoke":
        dims, Ts = [24], [10_000]
        steps = args.steps or 60
        seeds = args.seeds or 1
        tag = "smoke"
    else:
        dims, Ts = [24, 48, 96, 192], [10_000, 40_000, 160_000]
        steps = args.steps or 3000
        seeds = args.seeds or 3
        tag = "full"
    seq, bs = args.seq, args.bs

    os.makedirs(RES, exist_ok=True)
    lines = []

    def p(s=""):
        print(s, flush=True); lines.append(s)

    p("=" * 78)
    p(f"E13 先验预测实验 | scale={tag} | device={dev} | steps={steps} seeds={seeds}")
    p(f"torch {torch.__version__} cuda={torch.version.cuda} avail={torch.cuda.is_available()}")
    if dev.type == "cuda":
        p(f"GPU: {torch.cuda.get_device_name(0)} x{torch.cuda.device_count()}")
    p("=" * 78)

    text = load_corpus()
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    vocab = len(chars)
    data_full = np.array([stoi[c] for c in text], dtype=np.int64)
    p(f"语料 {len(data_full)/1e3:.1f}K 字符, vocab={vocab}, 随机基线 {math.log(vocab):.3f} nats")

    # ── 阶段 A: 先验量 (只用数据) ──
    p("")
    p("── 阶段 A: 数据侧先验量 (不碰 loss) ──")
    prior = {}
    splits_all = {}
    for T in Ts:
        d = data_full[:T]
        sp = context_spectrum(d, vocab, h=args.ctx)
        sp_split = block_split(d)                            # 与训练用同一划分
        splits_all[T] = sp_split
        train_txt = "".join(chars[i] for i in sp_split["train"])
        test_txt = "".join(chars[i] for i in sp_split["test"])
        floor = xz_conditional_rate(train_txt, test_txt)     # 主用: 条件压缩地板
        floor_alone = xz_rate(test_txt)                      # 诊断: 单段 xz (小窗会虚高)
        floor_all = xz_rate(train_txt + test_txt)            # 诊断: 全前缀单段
        ce_uni = unigram_ce(sp_split["train"], sp_split["test"], vocab)
        H_h = order_h_entropy(sp_split["train"], sp_split["test"], vocab, h=args.ctx)
        prior[T] = {
            "spectrum": sp, "H_floor": floor, "H_floor_xz_alone": floor_alone,
            "H_floor_xz_all": floor_all, "CE_unigram": ce_uni, "H_order_h": H_h,
            "D0": ce_uni - floor,
        }
        p(f"  T={T/1e3:5.1f}K: α={sp['alpha']:.2f} eff_rank={sp['eff_rank']:.1f} "
          f"rank90={sp['rank90']} mass_kept={sp['mass_kept']:.3f} "
          f"I(ctx;next)={sp['mutual_info_nats']:.3f} nats")
        p(f"           地板: 条件xz={floor:.3f} (单段 {floor_alone:.3f}, 全前缀 {floor_all:.3f}) "
          f"H_h={H_h:.3f} CE_uni={ce_uni:.3f} D0={prior[T]['D0']:.3f}")

    # ── 阶段 B: 组装预测, 训练前写盘 ──
    p("")
    p("── 阶段 B: 先验预测 (训练前落盘) ──")
    pred = {"scale": tag, "steps": steps, "seeds": seeds, "seq": seq,
            "bs": bs, "dims": dims, "Ts": Ts, "created": time.time(),
            "R_rule": "R(N) = ln(N * seq^2 / (3 dim^2))  [Efficiency.lean 交互率计数]", "cells": {}}
    for T in Ts:
        pr = prior[T]
        lam = np.array(pr["spectrum"]["lambda"], dtype=np.float64)
        # 谱归一: Σλ = D0 (量纲由数据给出, 份额由谱给出)
        lam_n = lam / lam.sum() * pr["D0"]
        for dim in dims:
            N = sum(p.numel() for p in CharLM(vocab, dim=dim).parameters())  # 架构精确参数数 (非训练)
            R = interaction_rate(N, seq, dim)
            D = waterfill_D(lam_n, R)
            pred["cells"][f"dim{dim}_T{T}"] = {
                "N_est": int(N), "R_nats": R,
                "L_pred": pr["H_floor"] + D,
                "H_floor": pr["H_floor"], "D_pred": D, "D0": pr["D0"],
                "excess_frac": D / pr["D0"] if pr["D0"] > 0 else float("nan"),
            }
            p(f"  dim={dim:3d} T={T/1e3:5.1f}K: N={N:8d} R={R:5.2f} nats "
              f"⟹ 预测损失 L̂={pr['H_floor'] + D:.3f} "
              f"(地板 {pr['H_floor']:.3f} + 失真 {D:.3f}, 占 D0 {D/pr['D0']*100:5.1f}%)")
    pj = os.path.join(RES, f"e13_predictions_{tag}.json")
    with open(pj, "w") as f:
        json.dump(pred, f, ensure_ascii=False, indent=2)
    h_pred = hashlib.sha256(open(pj, "rb").read()).hexdigest()[:16]
    p(f"  预测已写盘: {os.path.relpath(pj, ROOT)} sha256={h_pred}")

    # ── 阶段 C: 训练 (GPU) ──
    p("")
    p("── 阶段 C: 训练与实测 ──")
    meas = {}
    for dim in dims:
        for T in Ts:
            for seed in range(seeds):
                r = train_eval(splits_all[T], vocab, dim, seed, steps, bs, seq, dev)
                meas[f"dim{dim}_T{T}_s{seed}"] = r
                p(f"  dim={dim:3d} T={T/1e3:5.1f}K seed{seed}: N={r['n_params']:7d} "
                  f"test={r['test_loss']:.4f} val={r['val_loss']:.4f} "
                  f"train={r['train_loss']:.4f} @step{r['best_step']} "
                  f"tok={r['test_tokens']} {r['secs']:.1f}s")
    mj = os.path.join(RES, f"e13_measured_{tag}.json")
    with open(mj, "w") as f:
        json.dump(meas, f, ensure_ascii=False, indent=2)

    # 每格多 seed 均值/标准差
    grid = {}
    for dim in dims:
        for T in Ts:
            v = [meas[f"dim{dim}_T{T}_s{s}"]["test_loss"] for s in range(seeds)]
            grid[(dim, T)] = (float(np.mean(v)), float(np.std(v)))
    noise = float(np.mean([grid[k][1] for k in grid]))
    p("")
    p("--- loss 表 (mean ± sd over seeds) ---")
    p("   T\\dim |" + "".join(f"{d:>16d}" for d in dims))
    for T in Ts:
        p(f"  {T/1e3:5.1f}K |" + "".join(
            f"  {grid[(d,T)][0]:7.4f}±{grid[(d,T)][1]:.3f}" for d in dims))
    p(f"  训练噪声 (跨 seed sd 均值) = {noise:.4f} nats")

    # ── 阶段 D: 对照 ──
    p("")
    p("── 阶段 D: 预测 vs 实测 ──")
    errs, rows = [], []
    for dim in dims:
        for T in Ts:
            k = f"dim{dim}_T{T}"
            Lp = pred["cells"][k]["L_pred"]; Lm = grid[(dim, T)][0]
            errs.append(Lp - Lm)
            rows.append({"cell": k, "L_pred": Lp, "L_meas": Lm, "err": Lp - Lm,
                         "abs": abs(Lp - Lm), "N_meas": meas[f"dim{dim}_T{T}_s0"]["n_params"]})
            p(f"  {k:18s} 预测 {Lp:7.4f}  实测 {Lm:7.4f}  误差 {Lp-Lm:+7.4f}")
    mae = float(np.mean([r["abs"] for r in rows]))
    bias = float(np.mean([r["err"] for r in rows]))
    rmse = float(np.sqrt(np.mean([r["err"] ** 2 for r in rows])))
    p(f"  MAE={mae:.4f}  bias={bias:+.4f}  RMSE={rmse:.4f}  训练噪声={noise:.4f}")
    verdict_prior = ("成立" if mae < max(0.2, noise) else
                     ("方向对但幅度不足" if abs(bias) < mae and rmse < 1.0 else "不成立"))

    # ── 阶段 E: 反演诊断 (缺口 #2) ──
    p("")
    p("── 阶段 E: 反演 R_eff(N) — 架构→可达率的实证探测 ──")
    inv = {}
    for T in Ts:
        pr = prior[T]
        lam = np.array(pr["spectrum"]["lambda"], dtype=np.float64)
        lam_n = lam / lam.sum() * pr["D0"]
        pts = []
        for dim in dims:
            Lm = grid[(dim, T)][0]
            E = Lm - pr["H_floor"]
            R = R_of_D(lam_n, E) if E > 0 else 0.0
            N = meas[f"dim{dim}_T{T}_s0"]["n_params"]
            pts.append((dim, N, E, R))
            p(f"  T={T/1e3:5.1f}K dim={dim:3d}: 实测超额 {E:.4f} nats ⟹ R_eff={R:6.3f} nats "
              f"(谱 R∞ 上界 {R_of_D(lam_n, 1e-6):.2f})")
        inv[T] = pts

    # log R_eff vs log N 线性检验 (每个 T)
    fits = {}
    for T in Ts:
        pts = [x for x in inv[T] if x[3] > 0.05]
        if len(pts) >= 2:
            lnN = np.log([x[1] for x in pts]); lnR = np.log([x[3] for x in pts])
            A = np.vstack([lnN, np.ones_like(lnN)]).T
            (g, b), res, *_ = np.linalg.lstsq(A, lnR, rcond=None)
            r2 = 1 - ((lnR - A @ np.array([g, b])) ** 2).sum() / max(((lnR - lnR.mean()) ** 2).sum(), 1e-12)
            fits[T] = {"gamma": float(g), "log_a": float(b), "r2": float(r2), "n": len(pts)}
            p(f"  T={T/1e3:5.1f}K: log R_eff = {g:.3f}·log N + {b:.2f}  (R²={r2:.3f}, n={len(pts)})")

    # 留出检验: 小 dim 拟合, 大 dim 预测
    holdout = {}
    if len(dims) >= 3:
        dims_fit = dims[:2]; dims_pred = dims[2:]
        for T in Ts:
            pr = prior[T]
            lam = np.array(pr["spectrum"]["lambda"], dtype=np.float64)
            lam_n = lam / lam.sum() * pr["D0"]
            pts = [(meas[f"dim{d}_T{T}_s0"]["n_params"], grid[(d, T)][0]) for d in dims_fit]
            # 拟合 L = Hf + D0·exp(−k·N^γ) 形式 (三参数族里取 (k,γ) 两参数最小二乘)
            best = None
            for g in np.linspace(0.02, 0.6, 30):
                xs = np.array([n ** g for n, _ in pts]); ys = np.array([l - pr["H_floor"] for _, l in pts])
                A = np.vstack([xs, np.ones_like(xs)]).T
                (m, c), *_ = np.linalg.lstsq(A, ys, rcond=None)
                r = float(np.sum((ys - (m * xs + c)) ** 2))
                if best is None or r < best[0]:
                    best = (r, g, m, c)
            _, g, m, c = best
            for d in dims_pred:
                N = meas[f"dim{d}_T{T}_s0"]["n_params"]
                Lp = pr["H_floor"] + m * (N ** g) + c
                holdout[f"dim{d}_T{T}"] = {"L_pred": float(Lp), "L_meas": grid[(d, T)][0],
                                           "err": float(Lp - grid[(d, T)][0]),
                                           "gamma": float(g)}
                p(f"  留出 T={T/1e3:5.1f}K dim={d:3d}: 预测 {Lp:.4f} vs 实测 {grid[(d,T)][0]:.4f} "
                  f"误差 {Lp-grid[(d,T)][0]:+.4f} (γ={g:.2f})")

    p("")
    p("--- 判定 ---")
    p(f"  ① 先验预测 (零 loss 拟合): MAE={mae:.4f} vs 噪声 {noise:.4f} ⟹ {verdict_prior}")
    if fits:
        gs = [f["gamma"] for f in fits.values()]
        r2s = [f["r2"] for f in fits.values()]
        p(f"  ② 反演 R_eff: γ={[f'{g:.2f}' for g in gs]} R²={[f'{r:.2f}' for r in r2s]} "
          f"⟹ {'幂律映射存在' if min(r2s) > 0.9 else '映射非干净幂律'}")
    if holdout:
        he = [abs(v['err']) for v in holdout.values()]
        p(f"  ③ 留出 (小 dim 拟合→大 dim 预测): 平均 |误差| = {np.mean(he):.4f}")
    p("")
    p("诚实边界: 单语料 (本仓库文档/论文/Lean 混合体); 谱是二阶协方差代理, 非严格率-失真源;")
    p("  R(N) 用了 Efficiency.lean 的交互率计数——这一条本身是缺口 #2 的假设, 不是定理;")
    p("  小模型 (≤192 dim, 6 层), 固定步数; 结论只在该族内成立。")

    report = {
        "scale": tag, "device": str(dev), "steps": steps, "seeds": seeds,
        "corpus_chars": int(len(data_full)), "vocab": vocab,
        "prior": {str(k): {kk: vv for kk, vv in v.items() if kk != "spectrum"} for k, v in prior.items()},
        "spectrum": {str(k): v["spectrum"] for k, v in prior.items()},
        "predictions": pred, "predictions_sha256": h_pred,
        "measured": meas, "grid": {f"{d}_{t}": grid[(d, t)] for d in dims for t in Ts},
        "noise_sd": noise, "mae": mae, "bias": bias, "rmse": rmse,
        "verdict_prior": verdict_prior, "rows": rows,
        "inversion": {str(t): [{"dim": a, "N": b, "excess": c, "R_eff": d} for a, b, c, d in inv[t]]
                      for t in Ts},
        "fits": {str(k): v for k, v in fits.items()}, "holdout": holdout,
    }
    suffix = "" if tag == "full" else "_smoke"
    with open(os.path.join(RES, f"e13_report{suffix}.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    txt = "experiments_e13_results_smoke.txt" if tag == "smoke" else "experiments_e13_results.txt"
    with open(os.path.join(OUT, txt), "w") as f:
        f.write("\n".join(lines) + "\n")
    p(f"\n报告: experiments/results/e13_report{suffix}.json + scripts/{txt}")


if __name__ == "__main__":
    main()
