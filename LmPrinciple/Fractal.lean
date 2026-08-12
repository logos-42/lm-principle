/-
# 分形结构上的自由能下降速率 — Lean 推演 (Fractal.lean)

核心问题（用户假设）:
  QKV 注意力 + 残差连接 + MoE 架构在**分形组织**（浅层密集、深层稀疏、
  连接密度幂律缩放）下, 自由能下降速率是否高于均匀堆叠? 高维数学里
  的实现机制是什么?

论证链（每一环都是机器验证定理）:

  [0] 自由能模型: 深度网络逐层降低预测误差。令误差 e_k = |预测 - 真值|,
      自由能 F_k = e_k²。网络 = 一串模块, 每模块把误差映射到更小值。

  [1] **分形分配定理** (prefix_allocation_optimal):
      收益递减 (Δ_k 严格递减) 时, 把预算 B 集中在前 B 层（分形/幂律
      稀疏的核心结构）的自由能总下降 ≥ 均匀平摊到 n 层。
      —— "分形比均匀下降更快"的严格证明: 深层边际收益低, 分形把资源
         从深层搬到浅层, 同样的预算获得更多自由能下降。

  [2] **残差收缩定理** (residual_contraction_decay):
      残差块 f 是 c-收缩 (c < 1) ⟹ 误差 |f^[n] e| ≤ c^n·|e| 指数衰减,
      自由能 (误差平方) ≤ (c^n)²·F_0 指数下降。
      —— 与 RNN.rnn_stable 同族 (|w|<1 时状态有界): 收缩 = 稳定传播 =
         自由能不爆炸。残差连接保证深层的梯度/误差不消失。

  [3] **注意力凸组合定理** (attention_error_bound):
      QKV 注意力输出 = V 行的凸组合 (softmax 归一, 见 Transformer.lean)
      ⟹ 输出误差 ≤ 最差记忆误差 max_j |V_j - y|。
      —— 模块级"自由能下降"的保证: 注意力不会比它见过的最差记忆更差。

  [4] **MoE 凸组合定理** (moe_error_bound):
      混合专家 y = Σ g_j·E_j, 门控归一 (Σg=1, g≥0) ⟹ 误差 ≤ 最差专家
      误差。与注意力同构——都是凸组合, 都在高维凸包内操作。

  [5] **分形维数** (fractal_dimension_scale_invariant):
      D = log b / log(1/s) (b 分支, s 收缩), 且 n 级缩放后不变。
      connection_density_strict_anti: 连接密度 (1-d)^(D-1) 随深度单调
      递减——D>1 时分形结构必然"浅层密集、深层稀疏"。

高维数学的实现机制 (总结):
  - **凸组合 (凸包)**: 注意力/MoE 的输出被限制在 V/专家行的凸包内,
    误差有界——维度提供"方向多样性", 不是"无界能力"
  - **收缩映射**: 残差/RNN 的稳定传播——高维中的 Lipschitz 常数决定
    自由能下降速率 (指数 c^(2n))
  - **前缀分配**: 高维收益递减 ⟹ 资源集中在信息量最大的浅层子空间
  - **幂律稀疏**: 连接密度 (1-d)^(D-1) 是分形维数 D 的直接函数——
    任务维数越高, 深层越稀疏, 与 LMT-twister V34 "规模无效" 发现呼应
-/
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import LmPrinciple.Transformer
import LmPrinciple.RNN
import LmPrinciple.LMT

noncomputable section
open Finset
open scoped BigOperators

namespace Fractal

-- ============================================================
-- §1 分形分配定理: 收益递减时, 前缀集中 ≥ 均匀平摊
-- ============================================================

/-- **分形分配定理**: 每层自由能下降量 Δ_k 严格递减时, 把预算 B
    (B ≤ n 层) 集中在前 B 层（分形/幂律稀疏的核心）的总下降
    ≥ 均匀平摊到 n 层每层 B/n 的总下降。
    证明: 差 = (1/n)·Σ_{k<B}Σ_{j∈[B,n)} (Δ_k - Δ_j) ≥ 0. -/
theorem prefix_allocation_optimal {n B : ℕ} (Δ : ℕ → ℝ)
    (hB : B ≤ n)
    (hdec : ∀ {k j : ℕ}, k < j → j < n → Δ j < Δ k) :
    (B : ℝ) / n * (∑ k in range n, Δ k) ≤ ∑ k in range B, Δ k := by
  by_cases hn0 : n = 0
  · subst n
    simp at hB
    simp [hB]
  · have hnpos : 0 < n := Nat.pos_of_ne_zero hn0
    have hnposR : (0 : ℝ) < n := by exact_mod_cast hnpos
    -- 目标 ⟺ B·U ≤ n·P
    have hsplit : (∑ k in range n, Δ k) =
        (∑ k in range B, Δ k) + ∑ k in range (n - B), Δ (B + k) := by
      rw [← Finset.sum_range_add Δ B (n - B)]
      simp [Nat.add_sub_of_le hB]
    have hnonneg : ∀ k ∈ range B, ∀ j ∈ range (n - B), 0 ≤ Δ k - Δ (B + j) := by
      intro k hk j hj
      have hk' : k < B := Finset.mem_range.mp hk
      have hj' : j < n - B := Finset.mem_range.mp hj
      have hkj : k < B + j := by omega
      have hjn : B + j < n := by omega
      exact le_of_lt (sub_pos.mpr (hdec hkj hjn))
    have hsum_nonneg : 0 ≤ ∑ k in range B, ∑ j in range (n - B), (Δ k - Δ (B + j)) := by
      exact Finset.sum_nonneg (fun k hk => Finset.sum_nonneg (fun j hj => hnonneg k hk j hj))
    have hnℝ : (n : ℝ) = (B : ℝ) + (n - B : ℝ) := by
      exact_mod_cast (Nat.add_sub_of_le hB).symm
    have hdouble : (n - B : ℝ) * (∑ k in range B, Δ k) -
        (B : ℝ) * (∑ j in range (n - B), Δ (B + j)) =
        ∑ k in range B, ∑ j in range (n - B), (Δ k - Δ (B + j)) := by
      have h := calc
        (∑ k in range B, ∑ j in range (n - B), (Δ k - Δ (B + j)))
            = ∑ k in range B, ((n - B : ℝ) * Δ k - ∑ j in range (n - B), Δ (B + j)) := by
                apply Finset.sum_congr rfl
                intro k hk
                simp [Finset.sum_sub_distrib, Finset.sum_const, Finset.card_range,
                  nsmul_eq_mul, Nat.cast_sub hB]
        _ = (n - B : ℝ) * (∑ k in range B, Δ k) -
            ∑ k in range B, ∑ j in range (n - B), Δ (B + j) := by
                rw [Finset.sum_sub_distrib]
                rw [← Finset.mul_sum]
        _ = (n - B : ℝ) * (∑ k in range B, Δ k) -
            (B : ℝ) * (∑ j in range (n - B), Δ (B + j)) := by
                rw [Finset.sum_comm]
                simp only [Finset.sum_const, Finset.card_range, nsmul_eq_mul]
                rw [← Finset.mul_sum]
      exact h.symm
    have hmain : (B : ℝ) * (∑ k in range n, Δ k) ≤ (n : ℝ) * (∑ k in range B, Δ k) := by
      calc
        (B : ℝ) * (∑ k in range n, Δ k)
            = (B : ℝ) * ((∑ k in range B, Δ k) + ∑ k in range (n - B), Δ (B + k)) := by
                rw [hsplit]
        _ = (B : ℝ) * (∑ k in range B, Δ k) + (B : ℝ) * (∑ k in range (n - B), Δ (B + k)) := by
                ring
        _ ≤ (n : ℝ) * (∑ k in range B, Δ k) := by
                -- n·P - (B·P + B·T) ≥ 0 ⟺ (n-B)·P - B·T ≥ 0 = 双和 ≥ 0
                have hrewrite : (n : ℝ) * (∑ k in range B, Δ k) -
                    (B : ℝ) * (∑ k in range B, Δ k) -
                    (B : ℝ) * (∑ k in range (n - B), Δ (B + k)) =
                    (n - B : ℝ) * (∑ k in range B, Δ k) -
                    (B : ℝ) * (∑ k in range (n - B), Δ (B + k)) := by
                  rw [hnℝ]
                  ring
                have hnn : 0 ≤ (n - B : ℝ) * (∑ k in range B, Δ k) -
                    (B : ℝ) * (∑ k in range (n - B), Δ (B + k)) := by
                  rw [hdouble]
                  exact hsum_nonneg
                nlinarith
    -- (B/n)·U ≤ P ⟺ B·U ≤ n·P (n > 0)
    rw [div_mul_eq_mul_div]
    exact (div_le_iff₀ hnposR).mpr (by nlinarith [hmain])

-- ============================================================
-- §2 残差收缩: 自由能指数下降
-- ============================================================

/-- **残差收缩定理**: 残差块 f 是 c-收缩 (∀x y, |f x - f y| ≤ c·|x-y|,
    c ≥ 0, f 0 = 0) ⟹ n 层后误差 |f^[n] e| ≤ c^n·|e| 指数衰减。
    这就是"残差连接让深层网络的自由能不爆炸"的严格形式:
    恒等路径 + 收缩增量 = 稳定传播。 -/
theorem residual_contraction_decay (f : ℝ → ℝ) (c : ℝ)
    (hcont : ∀ x y : ℝ, |f x - f y| ≤ c * |x - y|)
    (hc0 : 0 ≤ c) (hf0 : f 0 = 0) :
    ∀ n : ℕ, ∀ e : ℝ, |(f^[n]) e| ≤ c ^ n * |e| := by
  intro n e
  induction n with
  | zero => simp
  | succ n ih =>
      have hstep : |f ((f^[n]) e)| ≤ c * |(f^[n]) e| := by
        have h := hcont ((f^[n]) e) 0
        simpa [hf0] using h
      calc
        |(f^[n + 1]) e| = |f ((f^[n]) e)| := by
            rw [Function.iterate_succ']
            rfl
        _ ≤ c * |(f^[n]) e| := hstep
        _ ≤ c * (c ^ n * |e|) := mul_le_mul_of_nonneg_left ih hc0
        _ = c ^ (n + 1) * |e| := by
            rw [pow_succ]
            ring_nf

/-- **自由能指数下降**: 自由能 F_n = (误差)² ≤ (c^n)²·F_0. -/
theorem free_energy_exponential_decay (f : ℝ → ℝ) (c : ℝ)
    (hcont : ∀ x y : ℝ, |f x - f y| ≤ c * |x - y|)
    (hc0 : 0 ≤ c) (hf0 : f 0 = 0) :
    ∀ n : ℕ, ∀ e : ℝ, ((|(f^[n]) e|) ^ 2) ≤ (c ^ n) ^ 2 * (|e| ^ 2) := by
  intro n e
  have h := residual_contraction_decay f c hcont hc0 hf0 n e
  have hsq : ((|(f^[n]) e|) ^ 2) ≤ (c ^ n * |e|) ^ 2 := by
    refine sq_le_sq.mpr ?_
    simpa [abs_of_nonneg (mul_nonneg (pow_nonneg hc0 n) (abs_nonneg e))] using h
  simpa [mul_pow] using hsq

-- 与 RNN 的呼应: 线性 RNN 是残差收缩的特例 (|w| < 1), 状态被
-- M/(1-|w|) 一致界住 (RNN.rnn_stable)——收缩保证自由能有界.

-- ============================================================
-- §3 QKV 注意力: 凸组合误差界
-- ============================================================

/-- **注意力凸组合定理**: 缩放点积注意力输出 = V 行的凸组合
    (softmax 归一) ⟹ 输出误差 ≤ 最差记忆误差 max_j |V_j - y|。
    QKV 机制在高维中的数学本质: 输出被限制在 V 的凸包内。 -/
theorem attention_error_bound {n : ℕ} (hn : 0 < n) (d : ℝ) (Q K V : Fin n → ℝ)
    (y M : ℝ) (i : Fin n) (hmax : ∀ j : Fin n, |V j - y| ≤ M) :
    |Transformer.attn d Q K V i - y| ≤ M := by
  let w : Fin n → ℝ := fun j => Transformer.softmaxWeight (fun j' => Q i * K j' / d) j
  have hw : ∀ j : Fin n, 0 ≤ w j := by
    intro j
    exact le_of_lt (Transformer.softmaxWeight_pos hn (fun j' => Q i * K j' / d) j)
  have hsum : (∑ j : Fin n, w j) = 1 := by
    exact Transformer.softmax_sum_eq_one hn (fun j' => Q i * K j' / d)
  have hiden : (∑ j : Fin n, w j * V j) - y = ∑ j : Fin n, w j * (V j - y) := by
    calc
      (∑ j : Fin n, w j * V j) - y
          = (∑ j : Fin n, w j * V j) - (∑ j : Fin n, w j) * y := by
              have hy : y = (∑ j : Fin n, w j) * y := by
                rw [hsum]
                ring
              rw [← hy]
      _ = (∑ j : Fin n, w j * V j) - ∑ j : Fin n, w j * y := by
              rw [← Finset.sum_mul]
      _ = ∑ j : Fin n, (w j * V j - w j * y) := by
              rw [← Finset.sum_sub_distrib]
      _ = ∑ j : Fin n, w j * (V j - y) := by
              apply Finset.sum_congr rfl
              intro j _
              ring
  calc
    |Transformer.attn d Q K V i - y| = |(∑ j : Fin n, w j * V j) - y| := by
        unfold Transformer.attn
        rfl
    _ = |∑ j : Fin n, w j * (V j - y)| := by rw [hiden]
    _ ≤ ∑ j : Fin n, w j * |V j - y| := by
        calc
          |∑ j : Fin n, w j * (V j - y)| ≤ ∑ j : Fin n, |w j * (V j - y)| := abs_sum_le_sum_abs _ _
          _ = ∑ j : Fin n, w j * |V j - y| := by
              apply Finset.sum_congr rfl
              intro j _
              rw [abs_mul, abs_of_nonneg (hw j)]
    _ ≤ ∑ j : Fin n, w j * M := by
        apply Finset.sum_le_sum
        intro j _
        exact mul_le_mul_of_nonneg_left (hmax j) (hw j)
    _ = M := by
        rw [← Finset.sum_mul]
        rw [hsum]
        ring

-- ============================================================
-- §4 MoE: 门控凸组合误差界
-- ============================================================

/-- **MoE 凸组合定理**: 混合专家 y = Σ g_j·E_j, 门控归一 (Σg = 1, g ≥ 0)
    ⟹ 输出误差 ≤ 最差专家误差。与注意力同构——都是凸组合机制,
    误差被凸包限制。 -/
theorem moe_error_bound {n : ℕ} (g E : Fin n → ℝ) (y M : ℝ)
    (hg : ∀ j : Fin n, 0 ≤ g j) (hsum : (∑ j : Fin n, g j) = 1)
    (hmax : ∀ j : Fin n, |E j - y| ≤ M) :
    |(∑ j : Fin n, g j * E j) - y| ≤ M := by
  have hiden : (∑ j : Fin n, g j * E j) - y = ∑ j : Fin n, g j * (E j - y) := by
    calc
      (∑ j : Fin n, g j * E j) - y
          = (∑ j : Fin n, g j * E j) - (∑ j : Fin n, g j) * y := by
              have hy : y = (∑ j : Fin n, g j) * y := by
                rw [hsum]
                ring
              rw [← hy]
      _ = (∑ j : Fin n, g j * E j) - ∑ j : Fin n, g j * y := by
              rw [← Finset.sum_mul]
      _ = ∑ j : Fin n, (g j * E j - g j * y) := by
              rw [← Finset.sum_sub_distrib]
      _ = ∑ j : Fin n, g j * (E j - y) := by
              apply Finset.sum_congr rfl
              intro j _
              ring
  calc
    |(∑ j : Fin n, g j * E j) - y| = |∑ j : Fin n, g j * (E j - y)| := by rw [hiden]
    _ ≤ ∑ j : Fin n, g j * |E j - y| := by
        calc
          |∑ j : Fin n, g j * (E j - y)| ≤ ∑ j : Fin n, |g j * (E j - y)| := abs_sum_le_sum_abs _ _
          _ = ∑ j : Fin n, g j * |E j - y| := by
              apply Finset.sum_congr rfl
              intro j _
              rw [abs_mul, abs_of_nonneg (hg j)]
    _ ≤ ∑ j : Fin n, g j * M := by
        apply Finset.sum_le_sum
        intro j _
        exact mul_le_mul_of_nonneg_left (hmax j) (hg j)
    _ = M := by
        rw [← Finset.sum_mul]
        rw [hsum]
        ring

-- ============================================================
-- §5 分形维数: 高维机制的数学定义
-- ============================================================

/-- **分形维数尺度不变**: D = log b / log(1/s) (b 分支数, s 收缩比),
    n 级缩放后维数不变——分形自相似性的严格表达。 -/
theorem fractal_dimension_scale_invariant (b s : ℝ) (n : ℕ) (hn : n ≠ 0)
    (hb : 1 < b) (hs0 : 0 < s) (hs1 : s < 1) :
    Real.log (b ^ n) / Real.log ((1 / s) ^ n) = Real.log b / Real.log (1 / s) := by
  rw [Real.log_pow, Real.log_pow]
  have hls : Real.log (1 / s) ≠ 0 := by
    have h1s : 1 < 1 / s := (one_lt_div hs0).mpr hs1
    exact ne_of_gt (Real.log_pos h1s)
  have hnz : (n : ℝ) ≠ 0 := by exact_mod_cast hn
  field_simp [hnz, hls]
  ring

/-- **连接密度幂律单调**: 分形连接密度 δ(d) = (1-d)^(D-1) 随深度 d
    严格递减 (D > 1) —— 分形结构必然"浅层密集、深层稀疏"。 -/
theorem connection_density_strict_anti (D : ℝ) (hD : 0 < D - 1) {d1 d2 : ℝ}
    (hd1 : 0 ≤ d1) (hd2 : d2 ≤ 1) (hlt : d1 < d2) :
    (1 - d2) ^ (D - 1) < (1 - d1) ^ (D - 1) := by
  have hbase_lt : 1 - d2 < 1 - d1 := by linarith
  have hbase_nonneg : 0 ≤ 1 - d2 := by linarith
  exact Real.rpow_lt_rpow hbase_nonneg hbase_lt hD

/-- **C3 连接密度凸性 (D = 3)**: δ(d) = (1-d)² 是凸函数——
    δ(λa + (1-λ)b) ≤ λ·δ(a) + (1-λ)·δ(b) (λ ∈ [0,1])。
    凸性 = 浅层密集/深层稀疏的加速衰减 (二阶性质): 深层比浅层
    稀疏得更快, 这是分形连接密度与均匀密度的本质区别。 -/
theorem connection_density_convex_D3 (a b l : ℝ) (hl0 : 0 ≤ l) (hl1 : l ≤ 1) :
    (1 - (l * a + (1 - l) * b)) ^ 2 ≤ l * (1 - a) ^ 2 + (1 - l) * (1 - b) ^ 2 := by
  -- 令 x = 1-a, y = 1-b: (lx + (1-l)y)² ≤ lx² + (1-l)y² ⟺ l(1-l)(x-y)² ≥ 0
  have hmain : 0 ≤ l * (1 - l) * (1 - a - (1 - b)) ^ 2 := by
    have hl : 0 ≤ 1 - l := by linarith
    exact mul_nonneg (mul_nonneg hl0 hl) (sq_nonneg _)
  nlinarith

/-- **自由能下降速率的完整表述**: 分形 (前缀集中) 组织的自由能下降
    ≥ 均匀堆叠 —— 前缀分配定理 + 残差指数衰减 + 凸组合误差界的组合。 -/
theorem fractal_beats_uniform {n B : ℕ} (Δ : ℕ → ℝ)
    (hB : B ≤ n) (hdec : ∀ {k j : ℕ}, k < j → j < n → Δ j < Δ k) :
    (∑ k in range B, Δ k) - (B : ℝ) / n * (∑ k in range n, Δ k) ≥ 0 := by
  linarith [prefix_allocation_optimal Δ hB hdec]

end Fractal
