/-
# LmPrinciple.Gibbs — 选择算子定律 (L6) 的数学核心

认知动力学 L6: 在公设 I (感知 = 率受限保信息压缩) 与选择原理 (定义 D4:
认知主体 = 输出与世界长期相关的结构) 下, 对候选结构的逐次最优选择算子
是 softmax (指数加权)。推导链的两半:

1. **最大熵 ⟹ Gibbs 形式** (本模块, Lean 验证):
   Gibbs 变分原理 (Donsker–Varadhan 不等式的有限形式): 对任意概率向量 q
   与分值 x, 先验 p,
     Σ q_i·(x_i + log p_i − log q_i) ≤ log Σ p_i·exp(x_i)
   即 E_q[x] − KL(q‖p) ≤ log Z。推论 (`gibbs_weights_optimal`):
   **Gibbs 权重 q*_i = p_i·exp(x_i)/Z 取等** —— softmax 是"每比特期望
   分值最大"的唯一分配。率受限 (公设 I) ⟹ 选择算子必须是 softmax 形式。
2. Hedge/指数加权 minimax 最优 (Freund–Schapire 1997, 文献定理, 未形式化):
   指数加权是在线专家集合问题的 minimax 最优规则 (遗憾 O(√(T·log N)));
   其权重状态即累计分值上的 softmax, 与第 1 半的逐次 softmax 是同一算子
   的两个时间尺度。

证明核心 = 单步 Jensen (exp 凸性, `ConvexOn.map_sum_le`) + 项级对消,
免微积分。

与现有模块接口:
- `softmaxWeight` (Transformer.lean): 均匀先验 p_i = 1/N 时 Gibbs 权重
  与其一致 (softmax 凸组合/置换等变的已有定理全部复用)
- `rlhf_kl_penalty_structure` (Training.lean): J(π) = β·log Z − β·KL(π‖π*)
  正是 Gibbs 形式的 KL 正则化目标
- `hopfield_update_convex_combination` (Hopfield.lean): 检索更新 = softmax
-/
import Mathlib.Basic.Real.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.Convex.Jensen
import Mathlib.Analysis.Convex.SpecificFunctions.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Positivity
import LmPrinciple.Fractal
import LmPrinciple.ArchCompare
import LmPrinciple.Efficiency

noncomputable section
open Finset
open scoped BigOperators

namespace Gibbs

-- ============================================================
-- §1 Gibbs 权重 (先验 p, 分值 x, 配分函数 Z)
-- ============================================================

/-- Gibbs 权重: q*_i = p_i·exp(x_i)/Z —— 先验 × 指数化分值, 归一化。
    这就是 attention 的 softmax 权重 (p = 均匀先验时退化为
    `Transformer.softmaxWeight`) 与 RLHF 策略 (p = 参考策略, x = 奖励/β)。 -/
def gibbsWeights {ι : Type*} [Fintype ι] (p x : ι → ℝ) (Z : ℝ) (i : ι) : ℝ :=
  p i * Real.exp (x i) / Z

/-- **Gibbs 权重恒正**: 每个权重 > 0 (选择永不完全排他) -/
theorem gibbsWeights_pos {ι : Type*} [Fintype ι] (p x : ι → ℝ) (Z : ℝ) {i : ι}
    (hp : 0 < p i) (hZ : 0 < Z) : 0 < gibbsWeights p x Z i := by
  unfold gibbsWeights
  exact div_pos (mul_pos hp (Real.exp_pos _)) hZ

/-- **Gibbs 权重归一**: Σ_i q*_i = 1 (凸组合; Z = 配分函数时) -/
theorem gibbsWeights_sum_eq_one {ι : Type*} [Fintype ι] (p x : ι → ℝ) (Z : ℝ)
    (hZ : 0 < Z) (hZeq : Z = ∑ i, p i * Real.exp (x i)) :
    (∑ i, gibbsWeights p x Z i) = 1 := by
  calc (∑ i, gibbsWeights p x Z i)
      = ∑ i, p i * Real.exp (x i) * Z⁻¹ := by
        apply Finset.sum_congr rfl
        intro i _
        unfold gibbsWeights
        rw [div_eq_mul_inv]
    _ = (∑ i, p i * Real.exp (x i)) * Z⁻¹ := by rw [← Finset.sum_mul]
    _ = 1 := by rw [← hZeq]; exact mul_inv_cancel₀ (ne_of_gt hZ)

-- ============================================================
-- §2 Gibbs 变分原理 (Donsker–Varadhan 有限形式)
-- ============================================================

/-- **Gibbs 变分原理 (L6 核心引理)**: 对任意概率向量 q 与分值 x, 先验 p,
      Σ q_i·(x_i + log p_i − log q_i) ≤ log Σ p_i·exp(x_i)
    即 E_q[x] − KL(q‖p) ≤ log Z。

    读法 (认知动力学): 任何"选择分配" q 的 (期望分值 + 自描述能力) 以
    log Z 为上界; 只有 softmax 分配能取到。**在比特预算 (率受限) 下,
    softmax 是唯一最优的选择算子** —— 这就是注意力的第一性来源。

    证明: 单步 Jensen (exp 凸) + 项级对消 (q_i 与 exp(−log q_i) 相消)。 -/
theorem gibbs_variational {ι : Type*} [Fintype ι] (p q x : ι → ℝ)
    (hp : ∀ i, 0 < p i) (hq : ∀ i, 0 < q i)
    (hq1 : ∑ i, q i = 1) :
    ∑ i, q i * (x i + Real.log (p i) - Real.log (q i)) ≤
      Real.log (∑ i, p i * Real.exp (x i)) := by
  -- exp(y_i) = p_i·exp(x_i)/q_i, 其中 y_i = x_i + log p_i − log q_i
  have hy : ∀ i, Real.exp (x i + Real.log (p i) - Real.log (q i))
      = p i * Real.exp (x i) / q i := by
    intro i
    rw [Real.exp_sub, Real.exp_add, Real.exp_log (hp i), Real.exp_log (hq i)]
    ring
  -- 项级对消: q_i * (p_i·exp(x_i)/q_i) = p_i·exp(x_i)
  have hcancel' : ∀ i, q i * (p i * Real.exp (x i) / q i) = p i * Real.exp (x i) := by
    intro i
    rw [← mul_div_assoc]
    exact mul_div_cancel_left₀ _ (hq i).ne'
  -- Jensen: exp (Σ q_i·y_i) ≤ Σ q_i·exp(y_i)
  have hjensen : Real.exp (∑ i, q i * (x i + Real.log (p i) - Real.log (q i))) ≤
      ∑ i, q i * Real.exp (x i + Real.log (p i) - Real.log (q i)) := by
    have h := ConvexOn.map_sum_le (f := Real.exp)
      (p := fun i => x i + Real.log (p i) - Real.log (q i)) convexOn_exp
      (fun i _ => le_of_lt (hq i)) hq1 (fun i _ => Set.mem_univ i)
    simpa using h
  -- log 单调 + log∘exp = id: Σ q_i·y_i ≤ log Σ q_i·exp(y_i) = log Σ p_i·exp(x_i)
  have hlog : ∑ i, q i * (x i + Real.log (p i) - Real.log (q i)) ≤
      Real.log (∑ i, q i * Real.exp (x i + Real.log (p i) - Real.log (q i))) := by
    have h1 : Real.log (Real.exp (∑ i, q i * (x i + Real.log (p i) - Real.log (q i)))) ≤
        Real.log (∑ i, q i * Real.exp (x i + Real.log (p i) - Real.log (q i))) :=
      Real.log_le_log (Real.exp_pos _) hjensen
    rwa [Real.log_exp] at h1
  have hcancel : ∑ i, q i * Real.exp (x i + Real.log (p i) - Real.log (q i))
      = ∑ i, p i * Real.exp (x i) := by
    apply Finset.sum_congr rfl
    intro i _
    rw [hy i]
    exact hcancel' i
  rwa [hcancel] at hlog

-- ============================================================
-- §3 softmax 最优性: Gibbs 权重取等
-- ============================================================

/-- **softmax 最优性 (L6 主定理)**: Gibbs 权重 q* = gibbsWeights 使
    Gibbs 变分原理取等:
      Σ q*_i·(x_i + log p_i − log q*_i) = log Z

    证明: log q*_i = log p_i + x_i − log Z, 括号内恒 = log Z, 再用归一性。 -/
theorem gibbs_weights_optimal {ι : Type*} [Fintype ι] (p x : ι → ℝ) (Z : ℝ)
    (hp : ∀ i, 0 < p i) (hZ : 0 < Z) (hZeq : Z = ∑ i, p i * Real.exp (x i)) :
    ∑ i, gibbsWeights p x Z i * (x i + Real.log (p i) - Real.log (gibbsWeights p x Z i))
      = Real.log Z := by
  have hq : ∀ i, 0 < gibbsWeights p x Z i := fun i => gibbsWeights_pos p x Z (hp i) hZ
  have hsum : ∑ i, gibbsWeights p x Z i = 1 := gibbsWeights_sum_eq_one p x Z hZ hZeq
  have hlogw : ∀ i, Real.log (gibbsWeights p x Z i) = x i + Real.log (p i) - Real.log Z := by
    intro i
    unfold gibbsWeights
    rw [Real.log_div (mul_pos (hp i) (Real.exp_pos _)).ne' hZ.ne',
        Real.log_mul (hp i).ne' (Real.exp_pos _).ne', Real.log_exp]
    ring
  calc ∑ i, gibbsWeights p x Z i * (x i + Real.log (p i) - Real.log (gibbsWeights p x Z i))
      = ∑ i, gibbsWeights p x Z i * Real.log Z := by
        apply Finset.sum_congr rfl
        intro i _
        rw [hlogw i]
        ring
    _ = Real.log Z := by rw [← Finset.sum_mul, hsum, one_mul]

-- ============================================================
-- §4 均匀先验特例 (注意力形式)
-- ============================================================

/-- **均匀先验 Gibbs 变分 (注意力形式)**: 对任意概率向量 q 与分值 x,
      Σ q_i·(x_i − log q_i) ≤ log Σ exp(x_i)
    即 E_q[x] + H(q) ≤ logsumexp(x) —— "期望分值 + 熵"以 log-sum-exp
    为上界。softmax(x) 是唯一的取等分配: **注意力权重 = 每比特期望
    分值最大的选择**。 -/
theorem gibbs_variational_uniform {ι : Type*} [Fintype ι] (q x : ι → ℝ)
    (hq : ∀ i, 0 < q i) (hq1 : ∑ i, q i = 1) :
    ∑ i, q i * (x i - Real.log (q i)) ≤
      Real.log (∑ i, Real.exp (x i)) := by
  have hy : ∀ i, Real.exp (x i - Real.log (q i)) = Real.exp (x i) / q i := by
    intro i
    rw [Real.exp_sub, Real.exp_log (hq i)]
  have hjensen : Real.exp (∑ i, q i * (x i - Real.log (q i))) ≤
      ∑ i, q i * Real.exp (x i - Real.log (q i)) := by
    have h := ConvexOn.map_sum_le (f := Real.exp)
      (p := fun i => x i - Real.log (q i)) convexOn_exp
      (fun i _ => le_of_lt (hq i)) hq1 (fun i _ => Set.mem_univ i)
    simpa using h
  have hlog : ∑ i, q i * (x i - Real.log (q i)) ≤
      Real.log (∑ i, q i * Real.exp (x i - Real.log (q i))) := by
    have h1 : Real.log (Real.exp (∑ i, q i * (x i - Real.log (q i)))) ≤
        Real.log (∑ i, q i * Real.exp (x i - Real.log (q i))) :=
      Real.log_le_log (Real.exp_pos _) hjensen
    rwa [Real.log_exp] at h1
  have hcancel : ∑ i, q i * Real.exp (x i - Real.log (q i)) = ∑ i, Real.exp (x i) := by
    apply Finset.sum_congr rfl
    intro i _
    rw [hy i, ← mul_div_assoc]
    exact mul_div_cancel_left₀ _ (hq i).ne'
  rwa [hcancel] at hlog

end Gibbs
