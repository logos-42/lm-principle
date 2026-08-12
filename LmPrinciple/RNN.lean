/-
# RNN 的数学第一性原理

线性循环网络 h_{t+1} = W·h_t + x_t 的本质:

1. **闭式解 = 因果卷积**: 展开后 h(n+1) = Σ_{k=0}^{n} w^{n-k}·x(k),
   即输出是输入序列与状态转移核 (w^0, w^1, w^2, ...) 的因果卷积
   —— RNN 与 CNN/卷积共享同一数学结构 (Toeplitz 矩阵 / 群代数乘法).

2. **稳定性**: |w| < 1 时状态被 M/(1-|w|) 一致界住
   (记忆指数衰减, 无界长依赖需要门控/残差结构).

定理均在任意交换半环 R 上证明 (ℝ/ℂ 都是实例).
-/
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

noncomputable section
open Finset
open scoped BigOperators

namespace RNN

/-- 线性 RNN 一步: h ↦ w·h + x -/
def step {R : Type*} [Semiring R] (w x h : R) : R := w * h + x

/-- 线性 RNN: h(0) = 0, h(n+1) = w·h(n) + x(n) -/
def rnn {R : Type*} [Semiring R] (w : R) (x : ℕ → R) : ℕ → R
  | 0 => 0
  | n + 1 => step w (x n) (rnn w x n)

/-- **闭式解**: RNN 输出 = 输入与核 w^(·) 的因果卷积 -/
theorem rnn_closed_form {R : Type*} [CommSemiring R] (w : R) (x : ℕ → R) :
    ∀ n : ℕ, rnn w x (n + 1) = ∑ k in range (n + 1), w ^ (n - k) * x k := by
  intro n
  induction n with
  | zero =>
      simp [rnn, step]
  | succ n ih =>
      rw [rnn, step, ih]
      have hmul : ∀ k ∈ range (n + 1), w * w ^ (n - k) = w ^ (n + 1 - k) := by
        intro k hk
        have hk' : k < n + 1 := Finset.mem_range.mp hk
        have hsub : n - k + 1 = n + 1 - k := by omega
        rw [← hsub, pow_succ, mul_comm]
      calc
        w * (∑ k in range (n + 1), w ^ (n - k) * x k) + x (n + 1)
            = ∑ k in range (n + 1), w ^ (n + 1 - k) * x k + x (n + 1) := by
                rw [Finset.mul_sum]
                congr 1
                apply Finset.sum_congr rfl
                intro k hk
                rw [← mul_assoc, hmul k hk]
        _ = ∑ k in range (n + 2), w ^ (n + 1 - k) * x k := by
                rw [Finset.sum_range_succ (fun k : ℕ => w ^ (n + 1 - k) * x k) (n + 1)]
                simp

/-- **稳定性**: |w| < 1 且 |x| 有界 ⟹ 状态一致有界 (记忆指数衰减) -/
theorem rnn_stable (w : ℝ) (x : ℕ → ℝ) (M : ℝ)
    (hw : |w| < 1) (hb : ∀ n : ℕ, |x n| ≤ M) :
    ∀ n : ℕ, |rnn w x (n + 1)| ≤ M / (1 - |w|) := by
  intro n
  have hM : 0 ≤ M := le_trans (abs_nonneg (x 0)) (hb 0)
  have hpos : 0 < 1 - |w| := by linarith
  have hle : M ≤ M / (1 - |w|) := by
    rw [le_div_iff₀ hpos]
    nlinarith [abs_nonneg w]
  induction n with
  | zero =>
      calc
        |rnn w x 1| = |x 0| := by simp [rnn, step]
        _ ≤ M := hb 0
        _ ≤ M / (1 - |w|) := hle
  | succ n ih =>
      calc
        |rnn w x (n + 2)| ≤ |w| * |rnn w x (n + 1)| + |x (n + 1)| := by
            rw [rnn, step]
            calc
              |w * rnn w x (n + 1) + x (n + 1)| ≤ |w * rnn w x (n + 1)| + |x (n + 1)| := abs_add _ _
              _ = |w| * |rnn w x (n + 1)| + |x (n + 1)| := by rw [abs_mul]
        _ ≤ |w| * (M / (1 - |w|)) + M := by
            nlinarith [mul_le_mul_of_nonneg_left ih (abs_nonneg w), hb (n + 1)]
        _ = M / (1 - |w|) := by
            have hden : 1 - |w| ≠ 0 := by linarith
            field_simp [hden]
            ring

end RNN
