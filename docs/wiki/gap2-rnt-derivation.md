---
title: 缺口 #2 推导目标书——架构→可达率 R(N,T)
source: session
created: 2026-10-22
last_confirmed: 2026-10-22
audience: internal
stage: current
schema_version: 2
confidence: medium
compiled_from: [experiment-results-gpu, experiment-results-e13, universal-weight-subspace, paper-fractal-criticality, dynamics-source-structure]
tags: [cognitive-dynamics, gap2, R(N,T), derivation-target, scaling-law, rate-distortion, E13]
---

# 缺口 #2 推导目标书: 架构 → 可达率 R(N,T)

> 定位 (2026-10-22): 用户定优先级 C→B→A, 其中 C = 先闭理论缺口 #2 再修假设/放实验。
> 本文把缺口 #2 从"预测差距账簿里的一条"升级为**可施工的推导目标书**:
> 明确目标、E13 反演给出的经验约束、候选结构、三个缺失引理、Lean 钩子、可证伪预测。

## 1. 缺口 #2 是什么 (为什么是主线)

`predictive-gap.md` 的三个缺口: ①感知流谱先验测定 ②**架构→可达率 R(N) 封闭映射**
③优化缺口。E13 先验预测 (GPU, MAE 2.80) 的失败 + 反演, 把 ② 精确改写为:

> **可达率是一个二变量函数 R(N,T), 且被数据 T 门控** —— 谱决定预算 D0 与地板,
> 但决定不了"有限数据 + 有限优化能多快拿到可压缩结构"。

这就是"从公理算出具体困惑度"的**最后一块理论拼图**: 有了它, 预测公式
`L̂ = H_floor + waterfill_D(λ, R_ach(N,T))` 才能成立; 缺它, E13 永远只能给界不能给值。

## 2. E13 反演给出的经验约束 (推导必须匹配的形状)

来自 `experiment-results-gpu.md §5` / `experiment-results-e13.md` (gpu_e13.json):

| 量 | 实测 | 含义 |
|---|---|---|
| 反演 `R_needed` ∝ lnN 斜率 | **−0.46** | 数据受限区内**更大 N 反而更差**(负相关) |
| 反演 `R_needed` ∝ lnT 斜率 | **+0.83** | 可达率被**数据 T 主导**(正相关) |
| `R_cap` ↔ `R_needed` 相关 | **+0.69** | 计数型容量率方向对, 但尺度/门控错 |
| 公式点预测 MAE | **2.80 nats** | `R_cap` (Efficiency.lean 交互率) 尺度错配 ⟹ 过度注水 |
| 先验可测量 | H_floor=0.931, D0=3.688, β_data=2.570 | 谱侧 (缺口①) **已闭合**: 下界+预算可先验给 |
| E9 最小实测 | 2.483 (dim128, T=300K) | 预测缺口 = 1.553 nats = 未闭合 R(N,T) 的实测总和 |

**关键约束**: 在数据受限区 (本批全部配置), `R_ach` 随 T 增长 (∝lnT)、随 N 微降 ——
所以任何候选 R(N,T) 必须在"数据受限区"重现 `∂R/∂lnT > 0`、`∂R/∂lnN < 0`, 且在
某 crossover 后转为 `∂R/∂lnN > 0` (参数受限区, 见 §4 L-switch)。

## 3. 候选结构 (推导目标)

**目标定理 (HB 系列之外, 记为 G2)**: 存在闭式可达率
```
R_ach(N, T, {λ_i}) = min( R_cap(N), R_data(T) ) · η(N, T)
```
使得训练后的最优损失满足 `L(N,T) = H_floor + waterfill_D(λ_norm, R_ach)`。

三项分解:
- `R_cap(N) = ln(N · seq² / (3 · dim²))` —— **容量率**, Efficiency.lean 交互率已有 (候选)。
  回答"这么多参数能承载多少有效自由度"。
- `R_data(T)` —— **数据率**: T 个样本能 populate 多少结构。与 UWS 定理 3.7 的
  `T^{-1/2}` 估计地板同源 (感知量 ⟹ 吸引子精度)。
- `η(N,T) ≤ 1` —— **优化效率**: 梯度下降多接近率-失真最优 = 优化缺口 (缺口③)。
  介于"可达上界"与"真正拿到"之间。

## 4. 三个缺失引理 (施工清单)

- **L-data (数据率)**: `R_data(T) = c(λ) · ln T`? 常数 `c(λ)` 与谱 λ 的"有效可学
  模式数"挂钩 (∝ 有效秩 / ∫谱)。需从 UWS 的 `T^{-1/2}` 估计误差反推出率单位下的
  `ln T` 增长。**这是 E13 反演 (+0.83) 要解释的核心**。
  ✅ **方向内核已 Lean 证 (2026-10-22)** `LmPrinciple/DataRate.lean`: `data_rate_mono`
  (以 UWS `ε(T)=c/√T` 地板为假设, `R_data(T)=Σ max(λ_i−εT)0` 随 T 单调不减) +
  `usable_modes_mono` (可用谱模数随 T 不减), `#print axioms` 仅 `[propext, Classical.choice,
  Quot.sound]` 无 sorry。**剩**: 具体幂指数 (~0.83) 与常数 `c(λ)` 的经验/半经验标定。
  ✅ **GPU E13-cross 实测确认方向 (2026-10-22, 细 T 网格 dims{128,256,512}×T{50K,100K,200K,353K}×3 seeds)**:
  反演 `R_needed ∝ lnT 斜率 +0.527`（>0 数据门控）、`∝ lnN 斜率 −0.431`（<0 数据受限区越大越差）
  —— 与 `data_rate_mono` 的"随 T 不减 + N 不门控"方向**一致**。诚实: `lnT` 幅度随**网格**而变
  （旧网格 T{100,200,300}K → +0.83; 新细网格 T{50,100,200,353}K → +0.53）——是 T 取值范围不同导致的拟合差异,
  **非**语料快照问题; 点预测 MAE 3.38 仍失败 ⟹ R(N,T) 整体未闭合, 但数据门控这一侧方向已双重确认（Lean 方向 + GPU 符号）。
  📌 **B 冻结语料复核 (2026-10-22)**: 加 `freeze` 子命令冻结语料快照重跑, 发现此前"e9 训练 353K / e13 反演 849K 不同步"是**误读**——`run_e13` 打印的"848730"是 `" ".join(text)` 的空格连接字节数(≈2×), 真实语料 e9/e13 一直是同一份 ~354K; 冻结后 e13 输出与冻结前**完全一致**(+0.527/−0.431), 证实无快照差。
- **L-eta (优化效率)**: `η(N,T)` 多接近 1? E13 旧版测到 dim192/T160K 训练损失已低于
  xz 地板 (记忆化) ⟹ 优化非绑定项 (η 在某些 regime 可视为 1, 但参数受限区的 η 未测)。
  这是缺口③, 项目自认"零理论", 是 G2 最不确定的一环。
  ✅ **方向内核已 Lean 证 (2026-10-22)** `LmPrinciple/OptEff.lean`: `loss_mono_in_eta`
  (以失真-率函数 `D(R)` 非增为假设, 损失 `H_floor + D(η·R₀)` 随 η **单调不增**) +
  `eff_rate_mono` (`η·R₀` 随 η 不减) + `loss_mono_in_rate` (与 data_rate_mono 合成 G2 单调底座),
  `#print axioms` 仅 `[propext, Classical.choice, Quot.sound]` 无 sorry。**剩**: η 的**具体值/上界**
  （= 优化缺口③, 需收敛率/Lyapunov/临界性理论）——真正困难处, 记为开放。
  ✅ **η 的几何重构已形式化 (2026-10-22, 用户"毛球向内折叠"直觉)** `LmPrinciple/Folding.lean`:
  把 η 从抽象标量重构为**折叠深度**（表示流形往低失真/吸引子折叠的程度）——`residual_excess E0 η=E₀(1−η)`
  （还没折掉的可约超额）、`loss_after_fold H E0 η=H+E₀(1−η)`、`loss_after_fold_mono`（折越深损失越低）、
  `full_fold_reaches_floor`（η=1 折到底⟹损失=地板, 对应实测记忆化）、`capped_fold_above_floor`（封顶 η_max<1⟹下不去地板）。
  **HB1 桥**: "纯切向折叠必在强制零点卡住⟹封顶"接 `HairyBall.forced_zero_trapped`, "残差解封⟹可达 η=1" 接
  `HairyBall.residual_removes_forced_zero`; 标量 η↔拓扑零点是**建模桥**(诚实标注, 非拓扑等价)。**剩（验证留后）**: 折叠深度 η 的实测标定 + 与 UWS 吸引子形状的对应。
- **L-switch (crossover)**: `R_cap(N) = R_data(T)` 解出 `N*(T)` = Chinchilla 式最优配比。
  E9 已见 crossover 起点 (T=300K dim512 首超 dim256), `N*(T)` 应预测它的位置。

## 5. Lean 钩子 (已有 / 需新增)

| 已有内核 | 用途 |
|---|---|
| `Training.lean: scaling_law_strict_anti` | 规模律幂律递减的地板形状 |
| `Efficiency.lean: interaction_rate` | `R_cap(N)` 容量率候选 |
| `Fractal.lean` 幂律密度 | 谱尾 ⟹ `D*(R)` 幂律 (L2 推导链) |
| `HairyBall.lean` (新) | 残差/临界线的拓扑根 (与 η 的"防坍缩"接壤) |
| `WaterFilling.lean` (新, 第一梯队①) | 注水失真 `D(R)`: `waterfill_D_mono_theta`/`distortion_antitone_rate` (率越多失真越低) / 端点; **证明了 `OptEff` 的 `Antitone D` 假设** |
| `G2.lean` (新, 第一梯队②) | 组装 `R_ach=min(R_cap,R_data)·η`, `L=H_floor+D(R_ach)`; `g2_loss_mono_data`/`_eta`/`_both` (数据↑、折叠↑ 都压低损失) |

**第一梯队已完成 (2026-10-22)**:
- `R_data(T)` 引理 (率单位下的 `ln T` 数据率, 接 UWS `T^{-1/2}`) — 方向内核 `DataRate.lean` 已证 (data_rate_mono)
- `η` 的形式化 — 方向内核 `OptEff.lean` + 几何重构 `Folding.lean` (η=折叠深度) 已证
- **注水 `D(R)`** — `WaterFilling.lean` 已证 (keystone)
- **G2 组装 `min·η` + `H+D` 单调性** — `G2.lean` 已证

**仍需 (第二/三梯队)**:
- `min`/crossover 的存在性与唯一性 (`N*(T)` 良定义) — L-switch, 需 R_cap/R_data 做成 Lean 函数 + 大语料测 crossover
- 谱尾 → 规模律指数 (L2 链); 泛化/估计项 (test−train, 真绑定缺口); 完整 HB1 (Poincaré–Hopf)

## 6. 可证伪预测 (一旦 G2 导出即可测)

1. **crossover 位置**: `N*(T)` 预测 E9 双区间切换点; 当前 E9 只见到起点 (T=300K)。
2. **参数受限区 β-fit 恢复**: 进参数受限区 (语料 >1M 或更大模型) 后, `∂R/∂lnN` 应转正,
   幂律-over-N 斜率可定义 (当前卡数据受限区故不可测)。
3. **E13-b/c 联动**: 用 G2 先验预测第二语料族, 留出检验 (幂律形式可迁移、系数需 per-corpus)。

### 一键可发实验 (E13-crossover, 就绪待 GPU 隧道恢复)

**目标**: 把 E9 网格推到参数受限区, 定位 crossover `N*(T)`, 看 `∂R_needed/∂lnN` 由负转正
（数据门控→容量门控的切换）, 并让幂律-over-N 的 β-fit 变得可测（验证 G2 的 L-switch）。

**前提**: 需更大语料（现有 docs/wiki ~830K 字符, 要覆盖 T≥1M 需 >2M 字符；可并入
`CORPUS_PATTERNS` 更多源或 `--max-chars` 放大）。

**命令**（远程 2×A100, `scripts/gpu_experiments.py`）:
```bash
# 1) 训更大网格进参数受限区（dims 上探 512, T 上探 2M+）
CUDA_VISIBLE_DEVICES=0 python scripts/gpu_experiments.py e9 \
    --dims 128 256 512 --Ts 100000 300000 1000000 3000000 --seeds 42 43 44
# 2) 反演: R_needed(N,T) 的 ∂/∂lnN、∂/∂lnT; 定位 crossover (∂/∂lnN 变号处)
python scripts/gpu_experiments.py e13
```
**判定**: ① 大 T 下 `∂R_needed/∂lnN` 转正 = L-data/L-cap 切换 (G2 的 `min` 成立);
② crossover `N*(T)` 位置与 `R_cap(N)=R_data(T)` 解一致; ③ 参数受限区 β-fit 可定义且
与谱尾 β_data 同量级。

**当前阻塞 (2026-10-22)**: A100 隧道 (100.100.30.185:6100) SSH banner 失效 (端口开但无
SSH 服务), 上个 session 的转发通道过期; 需用户重连隧道后才能执行。

## 7. 诚实边界

- G2 是**推导目标**, 不是已证定理; §3 的 `min(...)·η` 结构是**假设形态**,
  E13 只支持"数据门控"这一半, `min`/`η` 两项**未被数据直接检验**。
- 缺口③ (η) 是项目最薄弱处 (无优化理论), 可能长期只能给条件性界而非闭式 η。
- 与用户 C→B→A 排序一致: G2 未闭前, 放大实验 (A) 只是再次确认数据受限区, 不给新信息。

## 相关文档

- `docs/wiki/predictive-gap.md`（预测差距账簿, 缺口 #2 定位）
- `docs/wiki/experiment-results-gpu.md` §5 / `experiment-results-e13.md`（E13 反演数据）
- `docs/wiki/universal-weight-subspace.md`（UWS `T^{-1/2}` 估计地板, L-data 来源）
- `docs/wiki/topology-hairyball-notes.md`（HB1 拓扑根, 与 η/防坍缩接壤）
- `LmPrinciple/{Efficiency,Training,Fractal}.lean`（G2 的已有 Lean 内核）
