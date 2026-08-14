/-
# Hopfield 能量最小化 — Lean 推演 (Hopfield.lean)

hopfile.md 的核心第一性原理: 神经网络 = 动力系统, 能量函数 E(s),
更新使 ΔE < 0, 收敛到吸引子 (= 记忆); 现代 Hopfield 更新
x_new = X·softmax(βXᵀx) 等价于 Transformer 注意力。

## 定理结构

[1] **能量差分恒等式** (energy_difference):
    E(s') - E(s) = (s_i - s'_i)·net_i, 其中 s' 只在神经元 i 处与 s 不同,
    net_i = Σ_j w_ij·s_j (对称权重 w_ij = w_ji, 无自环 w_ii = 0)。
    这是 Hopfield 能量论证的核心代数: 能量变化只取决于被更新神经元
    的输入场 net_i。

[2] **翻转严格下降** (flip_energy_strictly_decreases):
    若 s_i·net_i < 0 (神经元 i 的当前状态与输入场反向), 翻转 s'_i = -s_i
    ⟹ E(s') < E(s)。⟹ 异步更新动力学严格单调下降, 必然收敛
    (能量有下界 + 单调 ⟹ 吸引子)。

[3] **现代 Hopfield 更新 = 凸组合检索** (hopfield_update_convex_combination):
    x_new = Σ_j softmax(β·x·X_j)·X_j 是存储模式 X_j 的凸组合
    (softmax 权重 > 0 且归一) —— Attention 的数学本质, 复用
    Transformer.softmaxWeight_pos / softmax_sum_eq_one。

与现有体系的关系: Transformer.lean 已证 softmax 凸组合 (注意力输出在
V 凸包内); 本文件把同一结构明确映射到 Hopfield 能量框架, 并补上
离散 Hopfield 的能量下降定理 (能量最小化的机器验证)。
-/
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import LmPrinciple.Transformer

noncomputable section
open Finset
open scoped BigOperators

namespace Hopfield

/-- 离散 Hopfield 能量 E(s) = -1/2·Σ_a Σ_b w_ab·s_a·s_b -/
def hopfieldEnergy {N : ℕ} (w : Fin N → Fin N → ℝ) (s : Fin N → ℝ) : ℝ :=
  -1 / 2 * (∑ a, ∑ b, w a b * s a * s b)

/-- 集合恒等式: univ \ {i} = univ.erase i -/
lemma univ_diff_singleton_erase {N : ℕ} (i : Fin N) :
    (Finset.univ : Finset (Fin N)) \ {i} = Finset.univ.erase i := by
  ext b
  simp [Finset.mem_erase]

/-- **能量差分恒等式**: s' 只在神经元 i 处与 s 不同 (对称权重, 无自环)
    ⟹ E(s') - E(s) = (s_i - s'_i)·net_i, net_i = Σ_j w_ij·s_j。
    证明: 双和展开, 按 a=i / b=i 分类; 只有含 i 的项变化,
    对称性把两项合并为 2·(s'_i - s_i)·net_i, 能量差 = -1/2·2·… -/
theorem energy_difference {N : ℕ} (w : Fin N → Fin N → ℝ) (s s' : Fin N → ℝ) (i : Fin N)
    (hsym : ∀ a b : Fin N, w a b = w b a)
    (hii : w i i = 0)
    (hrest : ∀ j : Fin N, j ≠ i → s' j = s j) :
    hopfieldEnergy w s' - hopfieldEnergy w s = (s i - s' i) * (∑ j, w i j * s j) := by
  unfold hopfieldEnergy
  let inner : Fin N → ℝ := fun a => ∑ b, w a b * (s' a * s' b - s a * s b)
  -- 核心: ΣΣ(w·s's' - w·ss) = 2·(s'_i - s_i)·net_i
  have hcore : (∑ a, ∑ b, w a b * s' a * s' b) - (∑ a, ∑ b, w a b * s a * s b)
      = 2 * (s' i - s i) * (∑ j, w i j * s j) := by
    calc
      (∑ a, ∑ b, w a b * s' a * s' b) - (∑ a, ∑ b, w a b * s a * s b)
          = ∑ a, (∑ b, w a b * s' a * s' b - ∑ b, w a b * s a * s b) := by
              rw [← Finset.sum_sub_distrib]
      _ = ∑ a, (∑ b, w a b * (s' a * s' b - s a * s b)) := by
              apply Finset.sum_congr rfl
              intro a ha
              rw [← Finset.sum_sub_distrib]
              apply Finset.sum_congr rfl
              intro b hb
              ring
      _ = 2 * (s' i - s i) * (∑ j, w i j * s j) := by
              -- inner i = (s'_i - s_i)·net_i (b=i 项为零, b≠i 时 s'_b = s_b)
              have hinner_i : inner i = (s' i - s i) * (∑ b, w i b * s b) := by
                dsimp [inner]
                have hsplit : (∑ b, w i b * (s' i * s' b - s i * s b))
                    = w i i * (s' i * s' i - s i * s i)
                      + (∑ b in Finset.univ.erase i, w i b * (s' i * s' b - s i * s b)) := by
                  rw [Finset.sum_eq_add_sum_diff_singleton (Finset.mem_univ i)
                    (fun b => w i b * (s' i * s' b - s i * s b)),
                    univ_diff_singleton_erase i]
                calc
                  (∑ b, w i b * (s' i * s' b - s i * s b))
                      = w i i * (s' i * s' i - s i * s i)
                          + (∑ b in Finset.univ.erase i, w i b * (s' i * s' b - s i * s b)) := hsplit
                  _ = (∑ b in Finset.univ.erase i, w i b * (s' i * s' b - s i * s b)) := by
                          rw [hii]
                          ring
                  _ = (∑ b in Finset.univ.erase i, w i b * (s' i - s i) * s b) := by
                          apply Finset.sum_congr rfl
                          intro b hb
                          have hbne : b ≠ i := (Finset.mem_erase.mp hb).1
                          rw [hrest b hbne]
                          ring
                  _ = (s' i - s i) * (∑ b in Finset.univ.erase i, w i b * s b) := by
                          have hre : (∑ b in Finset.univ.erase i, w i b * (s' i - s i) * s b)
                              = ∑ b in Finset.univ.erase i, (s' i - s i) * (w i b * s b) := by
                            apply Finset.sum_congr rfl
                            intro b hb
                            ring
                          rw [hre, ← Finset.mul_sum]
                  _ = (s' i - s i) * (∑ b, w i b * s b) := by
                          have hdrop : (∑ b in Finset.univ.erase i, w i b * s b) = ∑ b, w i b * s b := by
                            rw [Finset.sum_eq_add_sum_diff_singleton (Finset.mem_univ i)
                              (fun b => w i b * s b)]
                            rw [univ_diff_singleton_erase i, hii]
                            ring
                          rw [hdrop]
              -- 对 a ≠ i: inner a = w_ai·s_a·(s'_i - s_i) (只有 b=i 项非零)
              have hinner_ne : ∀ a : Fin N, a ≠ i → inner a = w a i * s a * (s' i - s i) := by
                intro a ha
                dsimp [inner]
                calc
                  (∑ b, w a b * (s' a * s' b - s a * s b))
                      = ∑ b, w a b * (s a * s' b - s a * s b) := by
                          apply Finset.sum_congr rfl
                          intro b hb
                          rw [hrest a ha]
                      _ = ∑ b, w a b * s a * (s' b - s b) := by
                          apply Finset.sum_congr rfl
                          intro b hb
                          ring
                      _ = w a i * s a * (s' i - s i) := by
                          apply Finset.sum_eq_single i
                          · intro b hb hbne
                            rw [hrest b hbne]
                            ring
                          · intro hnotin
                            exfalso
                            exact hnotin (Finset.mem_univ i)
              -- 外层拆 a = i
              have houter : (∑ a, inner a) = inner i + (∑ a in Finset.univ.erase i, inner a) := by
                rw [Finset.sum_eq_add_sum_diff_singleton (Finset.mem_univ i) inner,
                    univ_diff_singleton_erase i]
              have hne_sum : (∑ a in Finset.univ.erase i, inner a)
                  = (s' i - s i) * (∑ a, w i a * s a) := by
                calc
                  (∑ a in Finset.univ.erase i, inner a)
                      = (∑ a in Finset.univ.erase i, w a i * s a * (s' i - s i)) := by
                          apply Finset.sum_congr rfl
                          intro a ha
                          exact hinner_ne a (Finset.mem_erase.mp ha).1
                  _ = (s' i - s i) * (∑ a in Finset.univ.erase i, w a i * s a) := by
                          have hre : (∑ a in Finset.univ.erase i, w a i * s a * (s' i - s i))
                              = ∑ a in Finset.univ.erase i, (s' i - s i) * (w a i * s a) := by
                            apply Finset.sum_congr rfl
                            intro a ha
                            ring
                          rw [hre, ← Finset.mul_sum]
                  _ = (s' i - s i) * (∑ a, w i a * s a) := by
                          have hdrop : (∑ a in Finset.univ.erase i, w a i * s a) = ∑ a, w a i * s a := by
                            rw [Finset.sum_eq_add_sum_diff_singleton (Finset.mem_univ i)
                              (fun a => w a i * s a)]
                            rw [univ_diff_singleton_erase i, hii]
                            ring
                          rw [hdrop]
                          -- Σ_a w_ai·s_a = Σ_a w_ia·s_a (对称)
                          have hswap : (∑ a, w a i * s a) = ∑ a, w i a * s a := by
                            apply Finset.sum_congr rfl
                            intro a ha
                            rw [hsym i a]
                          rw [hswap]
              calc
                (∑ a, inner a) = inner i + (∑ a in Finset.univ.erase i, inner a) := houter
                _ = (s' i - s i) * (∑ b, w i b * s b) + (s' i - s i) * (∑ a, w i a * s a) := by
                        rw [hinner_i, hne_sum]
                _ = 2 * (s' i - s i) * (∑ j, w i j * s j) := by
                        -- 两个和定义相同 (绑定变量名不同), 直接 ring
                        ring
  -- 从 hcore 推出目标: E' - E = -1/2·hcore = (s_i - s'_i)·net
  have hgoal : (-1 / 2 * (∑ a, ∑ b, w a b * s' a * s' b))
      - (-1 / 2 * (∑ a, ∑ b, w a b * s a * s b))
      = (s i - s' i) * (∑ j, w i j * s j) := by
    nlinarith [hcore]
  simpa [hopfieldEnergy] using hgoal

/-- **翻转严格下降**: s_i·net_i < 0 时翻转 s'_i = -s_i (其余不变)
    ⟹ E(s') < E(s)。这是 Hopfield 异步更新的收敛保证:
    每步能量严格下降, 能量有下界 ⟹ 动力学收敛到吸引子。 -/
theorem flip_energy_strictly_decreases {N : ℕ} (w : Fin N → Fin N → ℝ) (s s' : Fin N → ℝ) (i : Fin N)
    (hsym : ∀ a b : Fin N, w a b = w b a)
    (hii : w i i = 0)
    (hflip : s' i = - s i)
    (hrest : ∀ j : Fin N, j ≠ i → s' j = s j)
    (hnet : s i * (∑ j, w i j * s j) < 0) :
    hopfieldEnergy w s' < hopfieldEnergy w s := by
  have hdiff := energy_difference w s s' i hsym hii hrest
  have hlt : hopfieldEnergy w s' - hopfieldEnergy w s < 0 := by
    rw [hdiff]
    rw [hflip]
    nlinarith [hnet]
  linarith

/-- **现代 Hopfield 更新**: x_new = Σ_j softmax(β·x·X_j)·X_j
    (存储模式 X_j, inverse temperature β) -/
def hopfieldUpdate {n : ℕ} (β : ℝ) (X : Fin n → ℝ) (x : ℝ) : ℝ :=
  ∑ j : Fin n, Transformer.softmaxWeight (fun j' => β * x * X j') j * X j

/-- **现代 Hopfield 更新 = 凸组合检索**: 输出是存储模式 X_j 的凸组合
    (权重 > 0 且归一) —— Attention 的数学本质 (hopfile.md:
    "Transformer 是高速连续 Hopfield 网络")。 -/
theorem hopfield_update_convex_combination {n : ℕ} (hn : 0 < n) (β : ℝ) (hβ : 0 < β)
    (X : Fin n → ℝ) (x : ℝ) :
    ∃ w : Fin n → ℝ, (∀ j : Fin n, 0 ≤ w j) ∧ (∑ j, w j) = 1 ∧
      hopfieldUpdate β X x = ∑ j, w j * X j := by
  refine ⟨fun j => Transformer.softmaxWeight (fun j' => β * x * X j') j, ?_, ?_, ?_⟩
  · intro j
    exact le_of_lt (Transformer.softmaxWeight_pos hn (fun j' => β * x * X j') j)
  · exact Transformer.softmax_sum_eq_one hn (fun j' => β * x * X j')
  · unfold hopfieldUpdate
    rfl

/-- **现代 Hopfield 更新 = Transformer 注意力 (同构)**: hopfieldUpdate 与
    Transformer.attn 是同一个数学对象——检索即注意力, 能量下降即前向传播。 -/
theorem hopfield_update_eq_attn {n : ℕ} (hn : 0 < n) (β : ℝ) (hβ : β ≠ 0)
    (X : Fin n → ℝ) (x : ℝ) :
    hopfieldUpdate β X x = Transformer.attn (1 / β) (fun _ => x) X X ⟨0, hn⟩ := by
  unfold hopfieldUpdate
  unfold Transformer.attn
  apply Finset.sum_congr rfl
  intro j hj
  unfold Transformer.softmaxWeight
  -- 内层: β·x·X_j' = x·X_j'/(1/β)
  have hinner : (fun j' : Fin n => β * x * X j') = fun j' : Fin n => x * X j' / (1 / β) := by
    funext j'
    field_simp [hβ]
    ring
  rw [← hinner]

/-- **softmax 权重集中性 (β 分岔的定量形式)**: 若模式 i 与所有其他模式的
    得分差 ≥ Δ (唯一最对齐, hgap), 则非目标权重指数小:
    w_j ≤ e^{-Δ} (∀ j ≠ i)。这是 E3 实验 (β 增大 → 重叠锁定 1.000) 的
    数学核心: 得分差越大权重越集中, 无需极限论证——对任意有限得分
    都成立。证明: w_j = e^{s_j}/D ≤ e^{s_j}/e^{s_i} = e^{-(s_i-s_j)} ≤ e^{-Δ}。 -/
theorem softmax_weight_concentration {n : ℕ} (hn : 0 < n) (Δ : ℝ) (s : Fin n → ℝ) (i : Fin n)
    (hΔ : 0 < Δ)
    (hgap : ∀ j : Fin n, j ≠ i → s i - s j ≥ Δ) :
    ∀ j : Fin n, j ≠ i → Transformer.softmaxWeight s j ≤ Real.exp (-Δ) := by
  intro j hj
  unfold Transformer.softmaxWeight
  let D : ℝ := ∑ j', Real.exp (s j')
  have hD : 0 < D := by
    haveI : Nonempty (Fin n) := (Fin.pos_iff_nonempty).mp hn
    exact Finset.sum_pos (fun _ _ => Real.exp_pos _) Finset.univ_nonempty
  -- e^{s_j} ≤ e^{-Δ}·e^{s_i} (hgap: s_i - s_j ≥ Δ)
  have hnum : Real.exp (s j) ≤ Real.exp (-Δ) * Real.exp (s i) := by
    have hle : s j ≤ -Δ + s i := by linarith [hgap j hj]
    have hmid : Real.exp (s j) ≤ Real.exp (-Δ + s i) := (Real.exp_le_exp).mpr hle
    rw [Real.exp_add] at hmid
    simpa using hmid
  -- e^{s_i} ≤ D (单项 ≤ 全和, 其他项 ≥ 0)
  have hsingle : Real.exp (s i) ≤ D := by
    simpa [D] using (Finset.single_le_sum (fun j' hj' => le_of_lt (Real.exp_pos (s j')))
      (Finset.mem_univ i))
  -- e^{s_j} ≤ e^{-Δ}·D
  have hnum2 : Real.exp (s j) ≤ Real.exp (-Δ) * D := by
    have he1 : Real.exp (-Δ) * Real.exp (s i) ≤ Real.exp (-Δ) * D :=
      mul_le_mul_of_nonneg_left hsingle (le_of_lt (Real.exp_pos (-Δ)))
    nlinarith [hnum, he1]
  -- w_j = e^{s_j}/D ≤ e^{-Δ}·D/D = e^{-Δ}
  have hdiv : Real.exp (s j) / D ≤ Real.exp (-Δ) := by
    have hd' : Real.exp (s j) / D ≤ (Real.exp (-Δ) * D) / D :=
      div_le_div_of_nonneg_right hnum2 (le_of_lt hD)
    have hcancel : (Real.exp (-Δ) * D) / D = Real.exp (-Δ) := by
      field_simp [ne_of_gt hD]
    rwa [hcancel] at hd'
  simpa [D] using hdiv

/-- **Hopfield 检索锁定误差界 (β 分岔定理)**: 若模式 i 唯一最对齐且差距 ≥ Δ
    (x·X_i - x·X_j ≥ Δ), 则 Hopfield 更新输出指数逼近 X_i:
    |x_new - X_i| ≤ n·e^{-βΔ}·M, 其中 M 是存储模式的直径上界
    (∀j, |X_j - X_i| ≤ M)。β 或 Δ 增大 ⟹ 误差指数衰减 ⟹ 检索锁定
    (E3 实验: β ≥ 9.6 时重叠 = 1.000 的理论形式)。
    证明: 凸组合权重集中 (softmax_weight_concentration) + 三角不等式。 -/
theorem hopfield_retrieval_error_bound {n : ℕ} (hn : 0 < n) (β Δ M : ℝ) (X : Fin n → ℝ) (x : ℝ) (i : Fin n)
    (hβ : 0 < β) (hΔ : 0 < Δ) (hM : 0 ≤ M)
    (hgap : ∀ j : Fin n, j ≠ i → x * X i - x * X j ≥ Δ)
    (hbound : ∀ j : Fin n, |X j - X i| ≤ M) :
    |hopfieldUpdate β X x - X i| ≤ (n : ℝ) * Real.exp (-β * Δ) * M := by
  let w : Fin n → ℝ := fun j => Transformer.softmaxWeight (fun j' => β * x * X j') j
  have hw0 : ∀ j : Fin n, 0 ≤ w j := fun j =>
    le_of_lt (Transformer.softmaxWeight_pos hn (fun j' => β * x * X j') j)
  have hwsum : (∑ j, w j) = 1 := Transformer.softmax_sum_eq_one hn (fun j' => β * x * X j')
  -- 用 w_j ≤ e^{-βΔ} (j ≠ i): score = fun j => β*x*X_j, 差 ≥ βΔ
  have hconc := softmax_weight_concentration hn (β * Δ) (fun j' => β * x * X j') i
    (mul_pos hβ hΔ) (by
      intro j hj
      have hd : Δ ≤ x * X i - x * X j := hgap j hj
      have hb0 : β * Δ ≤ β * (x * X i - x * X j) :=
        mul_le_mul_of_nonneg_left hd (le_of_lt hβ)
      have hb : β * Δ ≤ β * x * X i - β * x * X j := by
        nlinarith [hb0]
      -- 目标: β*x*X i - β*x*X j ≥ β*Δ (concentration 的 s i - s j)
      nlinarith)
  -- 恒等式: hopfieldUpdate - X_i = Σ_j w_j (X_j - X_i)
  have hiden : hopfieldUpdate β X x - X i = ∑ j, w j * (X j - X i) := by
    calc
      hopfieldUpdate β X x - X i
          = (∑ j, w j * X j) - X i := by
              unfold hopfieldUpdate
              rfl
      _ = (∑ j, w j * X j) - (∑ j, w j) * X i := by
              rw [hwsum]
              ring
      _ = ∑ j, (w j * X j - w j * X i) := by
              rw [Finset.sum_mul]
              rw [← Finset.sum_sub_distrib]
      _ = ∑ j, w j * (X j - X i) := by
              apply Finset.sum_congr rfl
              intro j hj
              ring
  -- |Σ w_j (X_j - X_i)| ≤ Σ w_j |X_j - X_i| ≤ Σ w_j M ≤ n·e^{-βΔ}·M
  have htri : |∑ j, w j * (X j - X i)| ≤ ∑ j, w j * |X j - X i| := by
    calc
      |∑ j, w j * (X j - X i)| ≤ ∑ j, |w j * (X j - X i)| := abs_sum_le_sum_abs _ _
      _ = ∑ j, w j * |X j - X i| := by
              apply Finset.sum_congr rfl
              intro j hj
              rw [abs_mul, abs_of_nonneg (hw0 j)]
  have hb2 : (∑ j, w j * |X j - X i|) ≤ (∑ j, w j * M) := by
    apply Finset.sum_le_sum
    intro j hj
    exact mul_le_mul_of_nonneg_left (hbound j) (hw0 j)
  have hb3 : (∑ j, w j * M) = M := by
    rw [← Finset.sum_mul]
    rw [hwsum]
    ring
  -- Σ_{j≠i} w_j ≤ (n-1)·e^{-βΔ} ≤ n·e^{-βΔ}: 用于 Σ_j w_j |X_j - X_i| 中 i 项为零
  have hsplit : (∑ j, w j * |X j - X i|) = ∑ j in Finset.univ.erase i, w j * |X j - X i| := by
    -- i 项: w_i * |X_i - X_i| = 0
    calc
      (∑ j, w j * |X j - X i|) = w i * |X i - X i| + ∑ j in Finset.univ.erase i, w j * |X j - X i| := by
          rw [Finset.sum_eq_add_sum_diff_singleton (Finset.mem_univ i) (fun j => w j * |X j - X i|),
              univ_diff_singleton_erase i]
      _ = ∑ j in Finset.univ.erase i, w j * |X j - X i| := by simp
  have hne_le : (∑ j in Finset.univ.erase i, w j * |X j - X i|)
      ≤ (n : ℝ) * Real.exp (-β * Δ) * M := by
    calc
      (∑ j in Finset.univ.erase i, w j * |X j - X i|)
          ≤ (∑ j in Finset.univ.erase i, w j * M) := by
              apply Finset.sum_le_sum
              intro j hj
              have hjn : j ≠ i := (Finset.mem_erase.mp hj).1
              exact mul_le_mul_of_nonneg_left (hbound j) (hw0 j)
      _ = (∑ j in Finset.univ.erase i, w j) * M := by
              rw [← Finset.sum_mul]
      _ ≤ (∑ j in Finset.univ.erase i, Real.exp (-β * Δ)) * M := by
              have hsumle : (∑ j in Finset.univ.erase i, w j) ≤ ∑ j in Finset.univ.erase i, Real.exp (-β * Δ) := by
                apply Finset.sum_le_sum
                intro j hj
                have hjn : j ≠ i := (Finset.mem_erase.mp hj).1
                simpa [neg_mul] using hconc j hjn
              exact mul_le_mul_of_nonneg_right hsumle hM
      _ = ((Finset.univ.erase i).card : ℝ) * Real.exp (-β * Δ) * M := by
              simp [Finset.sum_const, nsmul_eq_mul]
      _ ≤ (n : ℝ) * Real.exp (-β * Δ) * M := by
              have hcard : (Finset.univ.erase i).card ≤ n := by
                simpa using (Finset.card_le_univ (Finset.univ.erase i) :
                  (Finset.univ.erase i).card ≤ Fintype.card (Fin n))
              have hc : ((Finset.univ.erase i).card : ℝ) ≤ (n : ℝ) := by exact_mod_cast hcard
              have he : 0 ≤ Real.exp (-β * Δ) * M := mul_nonneg (le_of_lt (Real.exp_pos (-β * Δ))) hM
              nlinarith
  -- 组装
  rw [hiden]
  calc
    |∑ j, w j * (X j - X i)| ≤ ∑ j, w j * |X j - X i| := htri
    _ = ∑ j in Finset.univ.erase i, w j * |X j - X i| := hsplit
    _ ≤ (n : ℝ) * Real.exp (-β * Δ) * M := hne_le

end Hopfield
