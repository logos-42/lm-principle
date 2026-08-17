"""H100 预算估算器: 真实大参数验证"临界点"需要多少算力?

公式基础 (Kaplan et al. 2020 / Hoffmann et al. 2022, Chinchilla):
  训练总 FLOPs = 6 × N × D
    N = 参数量, D = 训练 token 数
    (前向 2N FLOPs/token + 反向 4N FLOPs/token)

硬件:
  H100 SXM: BF16 密集 989.5 TFLOPS (峰值)
  10 卡峰值 = 9.895 PFLOPS; 实际按 MFU (Model FLOPs Utilization)

用法:
  python3 scripts/estimate_h100_budget.py
输出: scripts/estimate_h100_budget_results.txt + stdout
"""
import os, json, math

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------- 硬件常量 ----------------
H100_BF16_TFLOPS = 989.5      # SXM 峰值 (TFLOPS)
PRICE_PER_H100_HOUR = 2.5     # 英伟达云按需约 $/卡时 (可改)
MFU_SINGLE = 0.35             # 单卡训练 MFU (小模型低)
MFU_MULTI = 0.45              # 多卡数据并行 MFU (大 batch 高)

def flops_train(N, D):
    """训练总 FLOPs = 6·N·D"""
    return 6.0 * N * D

def card_hours(N, D, n_gpus, mfu):
    """给定 N 参数、D tokens、n_gpus 卡、MFU, 返回卡时"""
    flops = flops_train(N, D)
    per_gpu = H100_BF16_TFLOPS * 1e12 * mfu
    wall_s = flops / (per_gpu * n_gpus)
    return flops, wall_s / 3600.0 * n_gpus   # 卡时 = 壁钟小时 × 卡数

def fmt(n):
    if n >= 1e21: return f"{n/1e21:.2f} ZFLOP"
    if n >= 1e18: return f"{n/1e18:.2f} EFLOP"
    if n >= 1e15: return f"{n/1e15:.2f} PFLOP"
    return f"{n:.2e}"

# ---------------- 规模档位 (N, D, 说明) ----------------
# 当前本地实验基准: dim64 8层 ≈ 40 万参数, 800 样本×20token, CPU 130-167s
TIERS = [
    # 名称, 参数量, 训练 tokens, 说明
    ("基准: 40 万参数 (现状)", 4.0e5, 1.6e4, "dim64/8层, 800×20 token, CPU 2 分钟"),
    ("档1: 350M (GPT-2 级)",   3.5e8, 1.5e10, "Chinchilla 最优附近, 真实语料"),
    ("档2: 1.3B (GPT-Neo 级)", 1.3e9, 2.0e10, "单卡 80GB 可放, 10卡可行"),
    ("档3: 7B (LLaMA 级)",     7.0e9, 1.0e11, "Chinchilla, 10卡要排队跑很多天"),
]

# ---------------- 实验矩阵 (对齐项目日志的缺陷修正) ----------------
# 日志缺陷: E5 欠训练(full-batch), E6 单seed+语料仅~1.5万token
# Q1+Q2: 真实 LM 逐层 β_eff / ΔE_k (只需训练 n_seeds 个模型, 测量是前向推理)
# Q3:    深度扫描 Δ_k 递减性是否在大规模恢复 (深度点数 × 结构数 × seeds 个模型)
MATRIX_Q12 = {"seeds": 3}                              # β_eff/ΔE_k 真实规模重测
MATRIX_Q3 = {"depths": 4, "structures": 2, "seeds": 2} # 深度扫描: {4,8,16,32}×{uniform,fractal}×{2}

def main():
    lines = []
    def p(s=""):
        print(s); lines.append(s)

    p("=" * 74)
    p("H100 预算估算: 真实大参数验证'临界点' (最优深度 kstar / β 分岔相变)")
    p("=" * 74)
    p(f"公式: 训练 FLOPs = 6·N·D; H100 BF16 = {H100_BF16_TFLOPS:.0f} TFLOPS/卡;")
    p(f"      MFU 单卡 {MFU_SINGLE:.0%} / 多卡 {MFU_MULTI:.0%}; 价格 ${PRICE_PER_H100_HOUR}/卡时")
    p("")

    # ---- 1. 单次训练成本 ----
    p("--- 1. 单次训练成本 (壁钟 = 10 卡全给一个训练) ---")
    p(f"{'规模':<24} {'FLOPs':<10} {'10卡壁钟':<12} {'总卡时':<10} {'成本$':<8} 说明")
    p("-" * 74)
    for name, N, D, note in TIERS:
        flops, _ = flops_train(N, D), None
        flops = flops_train(N, D)
        ch = card_hours(N, D, 10, MFU_MULTI)
        wall = flops / (10 * H100_BF16_TFLOPS * 1e12 * MFU_MULTI) / 3600
        cost = ch[1] * PRICE_PER_H100_HOUR
        p(f"{name:<24} {fmt(flops):<10} {wall:>6.1f} h     {ch[1]:>6.1f}    ${cost:>7.0f}  {note}")
    p("")

    # ---- 2. 实验矩阵总账 ----
    p("--- 2. 实验矩阵总账 (10 卡同时并行) ---")
    s_q12 = MATRIX_Q12["seeds"]
    n_q3 = MATRIX_Q3["depths"] * MATRIX_Q3["structures"] * MATRIX_Q3["seeds"]
    p(f"Q1+Q2 (β_eff/ΔE_k 真实 LM 重测): {s_q12} 个模型训练, 其余为前向测量 (≈0)")
    p(f"Q3   (深度扫描 Δ_k 递减性):      {MATRIX_Q3['depths']} 深度 × {MATRIX_Q3['structures']} 结构 × {MATRIX_Q3['seeds']} seeds = {n_q3} 个模型")
    p("")
    p(f"{'规模':<24} {'模型数':<8} {'总卡时':<10} {'10卡壁钟':<12} {'成本$':<9} 说明")
    p("-" * 74)
    for name, N, D, note in TIERS:
        n_models = s_q12 + n_q3
        flops, _ = card_hours(N, D, 1, MFU_MULTI)
        total_ch = flops * n_models / (H100_BF16_TFLOPS * 1e12 * MFU_MULTI) / 3600
        wall = total_ch / 10
        cost = total_ch * PRICE_PER_H100_HOUR
        p(f"{name:<24} {n_models:<8} {total_ch:>7.0f}    {wall:>6.1f} h    ${cost:>7.0f}  {note}")
    p("")

    # ---- 3. 可裁剪策略 ----
    p("--- 3. 预算裁剪选项 ---")
    p("A. 只跑 Q1+Q2 (β 相变重测, 最高性价比): 3 个模型即可")
    for name, N, D, note in TIERS[1:3]:
        flops, _ = card_hours(N, D, 1, MFU_MULTI)
        total_ch = flops * s_q12 / (H100_BF16_TFLOPS * 1e12 * MFU_MULTI) / 3600
        p(f"   {name}: {s_q12} 模型 = {total_ch:.0f} 卡时 = {total_ch/10:.1f} h 壁钟 (10卡) = ${total_ch*PRICE_PER_H100_HOUR:.0f}")
    p("B. Q3 深度扫描减到 {4,8,16}×2×2 = 12 模型 (省 25%)")
    p("C. 规模降到 350M: 总成本约为 1.3B 的 1/5, 结论方向相同 (规模效应检验)")
    p("")

    # ---- 4. 单位换算备忘 ----
    p("--- 4. 常用换算 ---")
    p("1 EFLOP = 1e18 FLOPs; 1B 参数 × 1B tokens 训练 = 6 EFLOPs")
    p("H100 单卡 1 小时 ≈ 989.5e12 × 0.45 × 3600 ≈ 1.6 EFLOPs (有效)")
    p("1.3B × 20B tokens ≈ 156 EFLOPs ≈ 10 卡 MFU45% 下 ~9.7 h 壁钟")
    p("")

    # ---- 5. 参考: 现有小实验的成本 (为什么 10 卡是巨大升级) ----
    p("--- 5. 与现状对比 ---")
    cur_flops = 6.0 * 4.0e5 * 1.6e4   # 40万参数 × 1.6万 token
    h100_s = cur_flops / (H100_BF16_TFLOPS * 1e12 * MFU_SINGLE)
    p(f"现有本地实验单次 ≈ {cur_flops:.2e} FLOPs ≈ H100 单卡 {h100_s*1e3:.2f} ms (微秒级!)")
    p(f"档2 (1.3B×20B) 单次是现有规模的 {6.0*1.3e9*2.0e10/cur_flops:.1e} 倍")
    p("")

    out = os.path.join(OUT, "estimate_h100_budget_results.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    p(f"结果已写入 {out}")

if __name__ == "__main__":
    main()
