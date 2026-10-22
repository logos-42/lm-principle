/- 
# WaterFilling — 注水失真函数 D(R) 的 Lean 化 (G2 的 keystone)

之前 `waterfill_D` 只在 Python (`gpu_experiments.py`); 且 `OptEff.loss_mono_in_eta` 里
`hD : Antitone D` 是**假设**。本文件把注水失真搬进 Lean 并**证明**其单调性, 从而
把 `OptEff` 的假设升级为定理, 让 G2 预测式 `L = H_floor + D(R_ach)` 第一次有 Lean 形态。

注水 (逆向注水 / reverse water-filling): 给定谱 {λ_i} 与阈值 θ, 各模保留 min(λ_i, θ),
总失真 `D(θ) = Σ_{i<n} min(λ_i, θ)`。阈值 θ 随率 R 下降 (θ 关于 R 非增), 故:
  - 注水失真关于 θ 单调不减 (`waterfill_D_mono_theta`);
  - 复合后 `D(R) = waterfill_D(θ(R))` 关于 R **非增** (`distortion_antitone_rate`) —— 率越多失真越低;
  - 端点: `waterfill_D(θ) ≤ Σλ` (失真不超总量), `waterfill_D(0)=0` (无限率压到零失真)。

诚实边界: 本文件证 D(R) 的**单调性与端点** (G2 所需); 注水的**KKT 最优性** (θ 精确满足
率约束) 是率-失真定理内容, 此处以 `Antitone θ` 为输入假设 (与项目"条件性定理"风格一致)。
-/
import Mathlib.Order.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Data.Finset.Range
import Mathlib.Tactic

noncomputable section

namespace WaterFilling

/-- 注水失真: 阈值 θ 下各谱模保留 `min(λ_i, θ)`, 总失真 `= Σ_{i<n} min(λ_i, θ)`。 -/
def waterfill_D (lam : ℕ → ℝ) (n : ℕ) (θ : ℝ) : ℝ :=
  Finset.sum (Finset.range n) (fun i => min (lam i) θ)

/-- 注水失真关于阈值 θ **单调不减** (θ↑ → 每模 min(λ_i,θ)↑ → 总失真↑)。 -/
theorem waterfill_D_mono_theta (lam : ℕ → ℝ) (n : ℕ) {θ1 θ2 : ℝ} (h : θ1 ≤ θ2) :
    waterfill_D lam n θ1 ≤ waterfill_D lam n θ2 := by
  unfold waterfill_D
  induction n with
  | zero => simp
  | succ n ih =>
      rw [Finset.sum_range_succ, Finset.sum_range_succ]
      have hpt : min (lam n) θ1 ≤ min (lam n) θ2 := min_le_min (le_refl _) h
      linarith

/-- 注水失真 ≤ 谱总量 (每模 `min(λ_i,θ) ≤ λ_i`): 失真不超过不压缩时的总量。 -/
theorem waterfill_D_le_total (lam : ℕ → ℝ) (n : ℕ) (θ : ℝ) :
    waterfill_D lam n θ ≤ Finset.sum (Finset.range n) lam := by
  unfold waterfill_D
  induction n with
  | zero => simp
  | succ n ih =>
      rw [Finset.sum_range_succ, Finset.sum_range_succ]
      have hpt : min (lam n) θ ≤ lam n := min_le_left _ _
      linarith

/-- 零阈值 (θ=0) ⟹ 注水失真 = 0 (谱非负时每模 `min(λ_i,0)=0`): 无限率压到零失真。 -/
theorem waterfill_D_at_zero (lam : ℕ → ℝ) (hn : ∀ i, 0 ≤ lam i) (n : ℕ) :
    waterfill_D lam n 0 = 0 := by
  unfold waterfill_D
  induction n with
  | zero => simp
  | succ n ih =>
      rw [Finset.sum_range_succ, ih]
      have h0 : min (lam n) (0:ℝ) = 0 := min_eq_right (hn n)
      rw [h0]
      simp

/-- **核心: 失真 D(R) 关于率 R 单调不增**。注水阈值 θ(R) 关于 R 非增 (率越多阈值越低),
    而注水失真关于 θ 单调不减 ⟹ 复合后 `D(R)=waterfill_D(θ(R))` 关于 R 非增。
    这正是 `OptEff.loss_mono_in_eta` 里被当假设的 `hD : Antitone D` —— 此处从注水结构**证明**它。 -/
theorem distortion_antitone_rate (lam : ℕ → ℝ) (n : ℕ) (θ : ℝ → ℝ) (hθ : Antitone θ) :
    Antitone (fun R => waterfill_D lam n (θ R)) := by
  intro R1 R2 hR
  have hθ' : θ R2 ≤ θ R1 := hθ hR
  exact waterfill_D_mono_theta lam n hθ'

end WaterFilling
