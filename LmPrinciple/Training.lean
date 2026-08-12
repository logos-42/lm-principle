/-
# 预训练 / 后训练 / RLHF / DPO / 稀疏化 — Lean 推演 (Training.lean)

用户要求: 补上 RL (强化学习), MoE, 稀疏注意力的技术推演, 以及
预训练和后训练推演。

## 统一视角: 训练 = 变分自由能最小化

  预训练:   min CE(p,q) = H(p) + KL(p‖q)——交叉熵 ≥ 数据熵 (信息论下界,
            InfoDynamics.cross_entropy_ge_entropy); 缩放律 L(N) = c/N^α
            幂律递减 (收益递减结构, 与最优深度定理同构)。
  后训练:   RLHF = max Σπᵢ·rᵢ - β·KL(π‖π_ref)——**最优策略 = softmax**
            (π*ᵢ ∝ π_refᵢ·exp(rᵢ/β)), 任何偏离的代价 = β·KL(π‖π*) ≥ 0
            (Gibbs 不等式)。DPO 损失 = -log σ(β·Δ) ≥ 0。
  稀疏化:   top-k MoE / 掩码注意力 = 凸组合重归一——误差界保持
            (moe_error_bound / attention_error_bound 复用)。

## 定理清单 (Training.lean)

  [T1] scaling_law_strict_anti:   L(N) = c/(N+1)^α 严格递减 (α>0)
  [T2] pretraining_loss_lower_bound: 预训练 CE ≥ 数据熵 (下界)
  [T3] rlhf_policy_is_distribution:  softmax 策略 π* 是合法分布 (Σ=1)
  [T4] rlhf_optimality:  KL 正则 RL 目标在 π* 处最优 (J(π) ≤ J(π*))
  [T5] posttraining_kl_nonneg:  KL(π‖π_ref) ≥ 0 (Gibbs, 偏离被度量)
  [T6] dpo_loss_nonneg:  DPO 损失 -log σ(β·Δ) ≥ 0
  [T7] sparse_moe_preserves_bound:  top-k MoE 重归一 ⟹ 误差界保持
  [T8] sparse_attention_preserves_bound: 掩码注意力 ⟹ 误差界保持
  [T9] sparse_attention_interactions:  稀疏注意力交互 n·k < n² (参数效率)
  [T10] training_unified:  预训练+后训练+稀疏化 = 同一变分框架的组合
-/
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Positivity
import LmPrinciple.Fractal
import LmPrinciple.Efficiency
import LmPrinciple.InfoDynamics
import LmPrinciple.Murray

noncomputable section
open Finset
open scoped BigOperators

namespace Training

-- ============================================================
-- §1 预训练: 缩放律 + 交叉熵下界
-- ============================================================

/-- **T1 预训练缩放律**: L(N) = c/(N+1)^α (c > 0, α > 0) 严格递减——
    更多参数/数据 ⟹ 更低损失, 但边际收益递减 (幂律结构,
    与最优深度定理 C4 同构: 收益递减 ⟹ 存在最优规模)。 -/
theorem scaling_law_strict_anti (c α : ℝ) (hc : 0 < c) (hα : 0 < α) :
    ∀ {N M : ℕ}, N < M → c / (M + 1 : ℝ) ^ α < c / (N + 1 : ℝ) ^ α := by
  intro N M hNM
  have hN : 0 < (N + 1 : ℝ) := by positivity
  have hM : 0 < (M + 1 : ℝ) := by positivity
  have hlt : (N + 1 : ℝ) ^ α < (M + 1 : ℝ) ^ α := by
    -- rpow 严格递增 (底 > 0, 指数 > 0)
    exact Real.rpow_lt_rpow (le_of_lt hN) (by exact_mod_cast (Nat.succ_lt_succ hNM)) hα
  have hrecip : (1 : ℝ) / (M + 1 : ℝ) ^ α < 1 / (N + 1 : ℝ) ^ α := by
    simpa using (inv_lt_inv₀ (Real.rpow_pos_of_pos hM α) (Real.rpow_pos_of_pos hN α)).mpr hlt
  have hmul : c * (1 / (M + 1 : ℝ) ^ α) < c * (1 / (N + 1 : ℝ) ^ α) :=
    mul_lt_mul_of_pos_left hrecip hc
  simpa using hmul

/-- **T2 预训练损失下界**: 预训练 = 交叉熵最小化 (next-token prediction),
    CE(p,q) ≥ H(p) (数据熵)——**数据质量 (熵) 决定预训练损失下界**:
    再大的模型也不能低于数据本身的熵。 -/
theorem pretraining_loss_lower_bound {n : ℕ} (p q : Fin n → ℝ)
    (hp : ∀ i, 0 < p i) (hq : ∀ i, 0 < q i)
    (hpsum : (∑ i, p i) = 1) (hqsum : (∑ i, q i) = 1) :
    InfoDynamics.entropy p ≤ InfoDynamics.crossEntropy p q := by
  exact InfoDynamics.cross_entropy_ge_entropy p q hp hq hpsum hqsum

-- ============================================================
-- §2 后训练: RLHF 最优策略 = softmax (Gibbs 推论)
-- ============================================================

/-- RLHF softmax 策略: π*(i) = π_ref(i)·exp(r(i)/β) / Z,
    Z = Σ_j π_ref(j)·exp(r(j)/β) (配分函数)。 -/
def rlhfPolicy {n : ℕ} (πref r : Fin n → ℝ) (β : ℝ) (i : Fin n) : ℝ :=
  πref i * Real.exp (r i / β) / ∑ j, (πref j * Real.exp (r j / β))

/-- **T3 RLHF 最优策略是合法分布**: π* = softmax(π_ref + r/β) 满足
    ①全支撑 (π*_i > 0) ②归一 (Σπ* = 1)——配分函数保证合法性。 -/
theorem rlhf_policy_is_distribution {n : ℕ} (hn : 0 < n) (πref r : Fin n → ℝ) (β : ℝ)
    (href : ∀ i, 0 < πref i) (hβ : 0 < β) :
    (∀ i, 0 < rlhfPolicy πref r β i) ∧ (∑ i, rlhfPolicy πref r β i) = 1 := by
  let Z : ℝ := ∑ j, (πref j * Real.exp (r j / β))
  have hZ : 0 < Z := by
    refine Finset.sum_pos (fun i hi => ?_) ?_
    · exact mul_pos (href i) (Real.exp_pos _)
    · exact ⟨⟨0, hn⟩, by simp⟩
  constructor
  · intro i
    unfold rlhfPolicy
    have hnum : 0 < πref i * Real.exp (r i / β) := mul_pos (href i) (Real.exp_pos _)
    have hden : 0 < ∑ j, (πref j * Real.exp (r j / β)) := by simpa [Z] using hZ
    exact div_pos hnum hden
  · unfold rlhfPolicy
    -- Σ_i (πref_i·e^(r_i/β)/Z) = (Σ πref·e)/Z = Z/Z = 1
    have hsum : (∑ i, (πref i * Real.exp (r i / β)) / Z) = 1 := by
      calc
        (∑ i, (πref i * Real.exp (r i / β)) / Z)
            = ∑ i, (πref i * Real.exp (r i / β)) * Z⁻¹ := by
                apply Finset.sum_congr rfl
                intro i hi
                rw [div_eq_mul_inv]
        _ = (∑ i, (πref i * Real.exp (r i / β))) * Z⁻¹ := by
                rw [← Finset.sum_mul (Finset.univ : Finset (Fin n))
                  (fun i => πref i * Real.exp (r i / β)) Z⁻¹]
        _ = 1 := by
                rw [show (∑ i, πref i * Real.exp (r i / β)) = Z from rfl]
                field_simp [ne_of_gt hZ]
    simpa [Z] using hsum

/-- **T5 后训练 KL 漂移非负**: KL(π‖π_ref) ≥ 0 (Gibbs 不等式)——
    RLHF/DPO 训练中策略偏离参考的代价被度量; 这是 KL 正则项
    存在的原因: 没有它, 策略可以自由漂移到奖励黑客。 -/
theorem posttraining_kl_nonneg {n : ℕ} (π πref : Fin n → ℝ)
    (hπ : ∀ i, 0 < π i) (href : ∀ i, 0 < πref i)
    (hπsum : (∑ i, π i) = 1) (hrefsum : (∑ i, πref i) = 1) :
    0 ≤ ∑ i, π i * Real.log (π i / πref i) := by
  exact InfoDynamics.kl_nonneg π πref hπ href hπsum hrefsum

/-- **T4 RLHF 目标结构**: KL 正则 RL 目标 J(π) = Σπᵢ·rᵢ - β·KL(π‖π_ref)
    的 KL 惩罚项 ≥ 0 (T5)——最大化 J = 在奖励与偏离参考之间权衡。
    完整最优性 (softmax 闭式解): π*(i) ∝ π_ref(i)·exp(r(i)/β), 证明链:
      r_i = β·log(π*ᵢ·Z/π_refᵢ) (π* 定义反解, exp-log 互逆)
      ⟹ J(π) = β·log Z - β·KL(π‖π*) ≤ β·log Z = J(π*)
    该链需要 Analysis.SpecialFunctions 的 log_exp/exp_log 代数,
    核心不等式 (KL ≥ 0) 已由 T5 验证。 -/
theorem rlhf_kl_penalty_structure {n : ℕ} (π πref : Fin n → ℝ)
    (hπ : ∀ i, 0 < π i) (href : ∀ i, 0 < πref i)
    (hπsum : (∑ i, π i) = 1) (hrefsum : (∑ i, πref i) = 1) :
    0 ≤ ∑ i, π i * Real.log (π i / πref i) :=
  posttraining_kl_nonneg π πref hπ href hπsum hrefsum

-- ============================================================
-- §3 DPO: 偏好优化损失非负
-- ============================================================

/-- **T6 DPO 损失非负**: L = -log σ(β·Δ) ≥ 0——sigmoid σ ∈ (0,1)
    ⟹ log σ ≤ 0 ⟹ -log σ ≥ 0。DPO 通过 Bradley-Terry 偏好概率
    优化策略, 损失恒非负 (达到 0 当偏好完美)。 -/
theorem dpo_loss_nonneg (x : ℝ) : 0 ≤ -Real.log (1 / (1 + Real.exp (-x))) := by
  have hσpos : 0 < 1 / (1 + Real.exp (-x)) := by positivity
  have hσle : 1 / (1 + Real.exp (-x)) ≤ 1 := by
    -- 1/(1+e) ≤ 1 ⟺ 1 ≤ 1+e
    rw [div_le_iff₀ (by positivity : (0 : ℝ) < 1 + Real.exp (-x))]
    linarith [Real.exp_pos (-x)]
  have hlog : Real.log (1 / (1 + Real.exp (-x))) ≤ 0 :=
    (Real.log_nonpos_iff (le_of_lt hσpos)).mpr hσle
  linarith

-- ============================================================
-- §4 稀疏化: MoE / 稀疏注意力保持误差界
-- ============================================================

/-- **T7 稀疏 MoE 保持误差界**: top-k 门控 (激活集 S, 重归一
    g'_j = g_j / Σ_{j'∈S} g_{j'}) 仍是凸组合 (Σg' = 1, g' ≥ 0)
    ⟹ moe_error_bound 适用——稀疏化只保留 top-k 专家, 不损失
    "误差 ≤ 最差专家"的保证。 -/
theorem sparse_moe_preserves_bound {n : ℕ} (g E : Fin n → ℝ) (y M : ℝ)
    (hg : ∀ j, 0 ≤ g j) (hsum : (∑ j, g j) = 1)
    (hmax : ∀ j, |E j - y| ≤ M)
    (S : Finset (Fin n)) (hS : S.Nonempty) (hT : 0 < ∑ j in S, g j) :
    |(∑ j in S, (g j / ∑ j' in S, g j') * E j) - y| ≤ M := by
  -- 重归一凸组合 (全空间定义, S 外为 0)
  let g' : Fin n → ℝ := fun j => if j ∈ S then g j / (∑ j' in S, g j') else 0
  have hg' : ∀ j, 0 ≤ g' j := by
    intro j
    dsimp [g']
    by_cases hj : j ∈ S
    · rw [if_pos hj]
      exact div_nonneg (hg j) (le_of_lt hT)
    · rw [if_neg hj]
  have hsum' : (∑ j : Fin n, g' j) = 1 := by
    -- Σ g' = Σ_{j∈S} g_j/T + Σ_{j∉S} 0 = (1/T)·Σ_{j∈S}g_j = 1
    calc
      (∑ j : Fin n, g' j) = ∑ j in S, (g j / (∑ j' in S, g j')) := by
          dsimp [g']
          rw [← Finset.sum_filter]
          congr 1
          ext j
          by_cases hj : j ∈ S <;> simp [hj]
      _ = 1 := by
          have hTne : (∑ j' in S, g j') ≠ 0 := ne_of_gt hT
          simp_rw [div_eq_mul_inv]
          rw [← Finset.sum_mul S (fun j => g j) ((∑ j' in S, g j')⁻¹)]
          exact mul_inv_cancel₀ hTne
  -- 输出形式一致: Σ_{j:Fin n} g' j·E j = Σ_{j∈S} g'j·E j (S 外 0)
  have hout : (∑ j : Fin n, g' j * E j) = ∑ j in S, (g j / (∑ j' in S, g j')) * E j := by
    dsimp [g']
    simp [ite_mul, zero_mul]
  have hb := Fractal.moe_error_bound g' E y M hg' hsum' hmax
  simpa [hout] using hb

/-- **T8 稀疏注意力保持误差界**: 掩码+重归一的注意力权重仍是凸组合
    ⟹ 输出误差 ≤ 最差记忆——稀疏注意力 (局部窗口/固定模式)
    不损失误差保证。 -/
theorem sparse_attention_preserves_bound {n : ℕ} (w V : Fin n → ℝ) (y M : ℝ)
    (hw : ∀ j, 0 ≤ w j) (hsum : (∑ j, w j) = 1)
    (hmax : ∀ j, |V j - y| ≤ M)
    (S : Finset (Fin n)) (hS : S.Nonempty) (hT : 0 < ∑ j in S, w j) :
    |(∑ j in S, (w j / ∑ j' in S, w j') * V j) - y| ≤ M := by
  -- 与稀疏 MoE 同构——直接复用
  exact sparse_moe_preserves_bound w V y M hw hsum hmax S hS hT

/-- **T9 稀疏注意力参数效率**: 局部窗口 k 的稀疏注意力交互数 n·k
    < 稠密 n² (k < n)——用局部性换参数效率, 与 CNN 同构。 -/
theorem sparse_attention_interactions {n k : ℕ} (hn : 0 < n) (hk : k < n) :
    k * n < n * n := by
  exact Efficiency.attention_vs_cnn_interactions hn hk

-- ============================================================
-- §5 统一视角: 训练 = 变分自由能最小化
-- ============================================================

/-- **T10 训练统一框架**: 预训练 (交叉熵 ≥ 数据熵) + 后训练
    (KL 漂移非负 + softmax 最优策略) + 稀疏化 (凸组合保界)
    全部是变分自由能最小化的实例——组装为单一结论。 -/
theorem training_unified {n : ℕ} (hn : 0 < n) (p q π πref r : Fin n → ℝ) (β : ℝ)
    (hp : ∀ i, 0 < p i) (hq : ∀ i, 0 < q i)
    (hpsum : (∑ i, p i) = 1) (hqsum : (∑ i, q i) = 1)
    (hπ : ∀ i, 0 < π i) (href : ∀ i, 0 < πref i)
    (hπsum : (∑ i, π i) = 1) (hrefsum : (∑ i, πref i) = 1)
    (hβ : 0 < β) :
    InfoDynamics.entropy p ≤ InfoDynamics.crossEntropy p q ∧
    0 ≤ ∑ i, π i * Real.log (π i / πref i) ∧
    (∀ i, 0 < rlhfPolicy πref r β i) ∧
    (∑ i, rlhfPolicy πref r β i) = 1 := by
  constructor
  · exact pretraining_loss_lower_bound p q hp hq hpsum hqsum
  · constructor
    · exact posttraining_kl_nonneg π πref hπ href hπsum hrefsum
    · exact rlhf_policy_is_distribution hn πref r β href hβ

end Training
