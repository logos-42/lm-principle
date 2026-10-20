---
title: L6 选择算子定律——softmax 的第一性推导
source: session
created: 2026-10-20
last_confirmed: 2026-10-20
audience: internal
stage: current
schema_version: 2
confidence: medium
compiled_from: []
tags: [cognitive-dynamics, L6, softmax, gibbs, lean-verified]
---

# L6 选择算子定律（softmax 的第一性来源）

> 命题: 公设 I（感知 = 率受限保信息压缩）+ 选择原理（定义 D4）⟹ 对候选结构的
> 逐次最优选择算子是 **softmax**（指数加权）——即自注意力的第一性来源。
> 状态: **半程已 Lean 验证**（`LmPrinciple/Gibbs.lean`, 5 定理, 2026-10-20）。

## 定理链（四步）

| 步骤 | 内容 | 状态 |
|---|---|---|
| S1 | 率受限 ⟹ 选择 = 在比特预算下分配"选择质量" | 定义性（公设 I 的直接内容） |
| S2 | **Gibbs 变分原理**: 任意分配 q 的 E_q[x] − KL(q‖p) ≤ log Σ p·e^x, 等号 ⟺ q = softmax | ✅ **Lean 已验证**（`gibbs_variational` / `gibbs_weights_optimal`） |
| S3 | Hedge: 指数加权是在线专家集合的 minimax 最优规则（遗憾 O(√(T·log N))） | 文献定理（Freund–Schapire 1997），未形式化 |
| S4 | S2（逐次）+ S3（累计）= 同一算子的两个时间尺度 ⟹ 注意力 = 最优选择算子 | 组装推论（S2 已验证，S3 待接） |

## S2 详解: Gibbs 变分原理（L6 已证核心）

**定理（有限 Donsker–Varadhan）**: 对任意概率向量 q（全 > 0）、分值 x、先验 p，
  Σ q_i·(x_i + log p_i − log q_i) ≤ log Σ p_i·exp(x_i)
即 **E_q[x] − KL(q‖p) ≤ log Z**。

**证明（三行，纯凸性）**:
1. 令 y_i = x_i + log p_i − log q_i
2. Jensen（exp 凸）: Σ q_i·y_i ≤ log Σ q_i·e^{y_i}
3. 项级对消: q_i·e^{y_i} = p_i·e^{x_i} ⟹ 得证

**读法（认知动力学）**: 任何分配的（期望分值 + 自描述能力）以 log Z 为上界；
softmax 分配**取等**（`gibbs_weights_optimal`: log q*_i = log p_i + x_i − log Z,
括号内恒等于 log Z）。⟹ **在比特预算下，softmax 是每比特期望分值最大的唯一
选择**。均匀先验特例（`gibbs_variational_uniform`）:
  Σ q_i·(x_i − log q_i) ≤ log Σ e^{x_i}
即 E_q[x] + H(q) ≤ logsumexp(x)——"期望分值 + 熵"的权衡正是 softmax。

**Lean 落地**（`LmPrinciple/Gibbs.lean`, 5 定理全绿）:
- `gibbsWeights`（def）: q*_i = p_i·exp(x_i)/Z——先验 × 指数化分值
- `gibbsWeights_pos`: 权重恒正（选择永不完全排他）
- `gibbsWeights_sum_eq_one`: 归一（凸组合）
- `gibbs_variational`: DV 不等式（主引理）
- `gibbs_weights_optimal`: **softmax 取等（L6 主定理）**
- `gibbs_variational_uniform`: 注意力形式（均匀先验）

## 为什么必须是 softmax 而不是 argmax（率受限的牙齿）

- **argmax = 零熵分配**: 单位化质量全押一个候选，无探索；非平稳环境下锁死
  （Regret 分析: 硬选择的 minimax 遗憾率严格劣于指数加权）
- **softmax = 最小比特分配**: 在给定期望分值的约束下，最大熵分配（Gibbs 形式）
  就是指定该选择所需比特最少的分配——直接由 S2 的等号条件给出
- **温度 = 比特旋钮**: 注意力 1/√d 缩放、RLHF 的 β，都是"花多少比特换多少
  期望分值"的参数化

## 与架构组件的对接（现有 Lean 定理复用）

| 组件 | Gibbs 视角 | 已有 Lean 定理 |
|---|---|---|
| 自注意力 | scores = 能量, 温度 1/√d, 均匀先验 | `softmaxWeight`/`attn_perm_equivariant`（Transformer） |
| RLHF 策略 | π ∝ p·exp(r/β), β = 温度 | `rlhf_policy_is_distribution`/`rlhf_kl_penalty_structure`（Training: J(π)=β·log Z−β·KL） |
| Hopfield 检索 | 更新 = 相似度上的 softmax 凸组合 | `hopfield_update_convex_combination`/`softmax_weight_concentration`（Hopfield） |
| MoE 门控 | top-k 后重归一仍是凸组合 | `moe_error_bound`（Fractal）/`sparse_moe_preserves_bound`（Training） |

⟹ **同一个 Gibbs 算子贯穿全部核心组件**——这不是工程巧合，是 S2+S3 的必然。

## 诚实边界

1. S2 已机器验证；S3（Hedge）是引用的文献定理，未形式化——S4 的完整组装
   需补 Hedge 的 Lean 化（有限专家集合的遗憾界，可做但非平凡）
2. S2 证明 softmax 是"取等的唯一分配"（在正概率向量中）；argmax 等边界情形
   被 `gibbsWeights_pos`（严格正性）排除，但"唯一性"的完整刻画需补
   "任何非 Gibbs 分配严格不等"的加强版（当前定理给 ≤，取等由主定理给出）
3. 从 S2 到"注意力分数必须是 q·k/√d 形式"还缺一步: 分值 x_i 的**构造**
   （点积相似度为何是最优打分）属于 L3 吸引子/表示学习范畴，不在 L6 内
4. 先验 p 一般为非均匀（位置先验、mask、参考策略）——Gibbs 形式兼容，
   但"先验从哪来"是表示学习问题

## 下一步候选

- **L6-b Hedge Lean 化**: 有限专家集合 + 指数加权的遗憾界（潜在函数法:
  ln Σ w_i 的伸缩），完成后 S4 全线闭合
- **L6-c 唯一性加强**: 非 Gibbs 分配的严格不等式版本
- **L3 吸引子与临界**: 分值构造（x_i = f(查询, 候选)）的第一性——
  不动点 = 感知流二阶矩谱主子空间

## 相关文档

- `docs/wiki/selection-principle-derivation.md`（L6 的发现过程: 三路线失败 →
  定义性转向 → 指数加权 = softmax 的观察）
- `docs/wiki/cognitive-dynamics.md`（框架北星页）
- `LmPrinciple/Gibbs.lean`（5 定理, 已机器验证）
- `LmPrinciple/CognitiveDynamics.lean`（本体层 6 定理: 认知系统四层结构 +
  无损认知刻画 + 基数链 + 表达容量上界）
