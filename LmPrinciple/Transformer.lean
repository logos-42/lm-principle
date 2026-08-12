/-
# Transformer 的数学第一性原理

注意力机制的三个本质性质:

1. **softmax 是凸组合权重**: 每个权重 > 0 且 Σ 权重 = 1
   —— 注意力输出必落在 V 行的凸包内 (无外推, 这是 Transformer 的归纳偏置);
2. **置换等变性**: 输入 (Q, K, V) 按同一置换 π 重排,
   输出按 π 重排 —— 自注意力不知道"位置", 位置信息必须由外部注入
   (为什么需要位置编码的数学证明);
3. 缩放因子 d 不影响上述结构性质 (证明对任意 d 成立).

证明全部是有限和重排 (Equiv.sum_comp), 不需要任何分析.
-/
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Algebra.BigOperators.Group.Finset.Defs
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Data.Fin.Embedding

noncomputable section
open Finset
open scoped BigOperators

namespace Transformer

/-- softmax 权重: w_i = exp(s_i) / Σ_j exp(s_j) -/
def softmaxWeight {n : ℕ} (s : Fin n → ℝ) (i : Fin n) : ℝ :=
  Real.exp (s i) / ∑ j : Fin n, Real.exp (s j)

/-- **softmax 权重恒正**: 每个权重 > 0 -/
theorem softmaxWeight_pos {n : ℕ} (hn : 0 < n) (s : Fin n → ℝ) (i : Fin n) :
    0 < softmaxWeight s i := by
  haveI : Nonempty (Fin n) := (Fin.pos_iff_nonempty).mp hn
  unfold softmaxWeight
  exact div_pos (Real.exp_pos _)
    (Finset.sum_pos (fun _ _ => Real.exp_pos _) Finset.univ_nonempty)

/-- **softmax 归一**: Σ_i w_i = 1 (凸组合) -/
theorem softmax_sum_eq_one {n : ℕ} (hn : 0 < n) (s : Fin n → ℝ) :
    (∑ i : Fin n, softmaxWeight s i) = 1 := by
  haveI : Nonempty (Fin n) := (Fin.pos_iff_nonempty).mp hn
  let D : ℝ := ∑ j : Fin n, Real.exp (s j)
  have hD : D ≠ 0 := ne_of_gt (Finset.sum_pos (fun _ _ => Real.exp_pos _) Finset.univ_nonempty)
  calc
    (∑ i : Fin n, softmaxWeight s i) = ∑ i : Fin n, Real.exp (s i) * D⁻¹ := by
      unfold softmaxWeight
      dsimp [D]
      apply Finset.sum_congr rfl
      intro i _
      rw [div_eq_mul_inv]
    _ = (∑ i : Fin n, Real.exp (s i)) * D⁻¹ := by
      rw [← Finset.sum_mul]
    _ = 1 := by
      dsimp [D]
      exact mul_inv_cancel₀ hD

/-- 缩放点积注意力: attn(Q,K,V)_i = Σ_j softmax(Q_i·K_j/d)·V_j -/
def attn {n : ℕ} (d : ℝ) (Q K V : Fin n → ℝ) (i : Fin n) : ℝ :=
  ∑ j : Fin n, softmaxWeight (fun j' => Q i * K j' / d) j * V j

/-- **自注意力置换等变**: 输入按 π 置换, 输出按 π 置换
    (证明: 求和重排 + softmax 分母的置换不变性) -/
theorem attn_perm_equivariant {n : ℕ} (d : ℝ) (π : Equiv.Perm (Fin n))
    (Q K V : Fin n → ℝ) :
    (fun i : Fin n => attn d (fun i => Q (π i)) (fun i => K (π i))
        (fun i => V (π i)) i)
      = fun i : Fin n => attn d Q K V (π i) := by
  funext i
  unfold attn
  have hden :
      (∑ j' : Fin n, Real.exp (Q (π i) * K (π j') / d)) =
        (∑ j' : Fin n, Real.exp (Q (π i) * K j' / d)) := by
    exact Equiv.sum_comp π (fun j' => Real.exp (Q (π i) * K j' / d))
  rw [← Equiv.sum_comp π
    (fun j => softmaxWeight (fun j' => Q (π i) * K j' / d) j * V j)]
  apply Finset.sum_congr rfl
  intro j _
  unfold softmaxWeight
  rw [hden]

end Transformer
