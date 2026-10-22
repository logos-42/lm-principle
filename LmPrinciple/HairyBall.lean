/- 
# HB1 — 毛球定理作为 L8 残差的拓扑根（候选定理）

用户直觉（2026-10-22）: 深度的"坑"由毛球定理产生 —— 偶维闭流形上平滑切向量场
必有零点（奇点）; 残差 = 绕开该奇点的法向/恒等路径。E-TOPO-2 已在 S² 上数值验证
（切向动力学坍缩于极点, 加残差法向路径后越极离面）。

本文件把该机制的**初等可证内核**形式化（全部机器验证, 无 sorry / admit / axiom）:

  §1 forced_zero_trapped : 紧致区间上"两端向内"的连续下降流必有零点
      （= 被"困在闭域"无处可逃时, 停滞/坍缩是拓扑强制的 —— "坑"的 1D 版）。
  §2 residual_removes_forced_zero : 一旦允许状态越界（残差 = 离面/恒等路径,
      几何上相当于多一条"法向"自由度）, "两端向内"的困住条件被破坏,
      存在连续且处处无零点的下降流（= 残差打破强制停滞）。
  §3 s1_tangent_nonvanishing : 圆 S¹（奇维闭流形）存在处处非零的切向量场（可梳）,
      反衬该障碍是"维度奇偶/几何"特异的, 与毛球定理的偶维限制吻合。

## HB1 目标（毛球定理全文）—— 本文件**未证**, 也**不**作为 axiom 引入:
  偶维球面 S^{2k} 上不存在处处非零的连续切向量场（Poincaré–Hopf / 阻碍理论）。
  当前 mathlib 无现成结果、需 degree 理论, 超出本次范围, 记为形式化目标;
  §1–§3 是它在"被闭域困住 / 残差越界"这一 L8 相关侧的 1D 可证化身, 已与 E-TOPO-2 对应。
  诚实地: §1–§3 抓牢了"强制零点 + 残差逃逸"的机制, 但不等于证明了偶维闭流形版本。
-/
import Mathlib.Topology.Order.IntermediateValue
import Mathlib.Order.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Mathlib.Tactic

noncomputable section

namespace HairyBall

-- ============================================================
-- §1 强制零点: 被"困在闭域"的下降流必有停滞（L8 的"坑", 1D 版）
-- ============================================================

/-- **HB1-core 强制零点**: 连续下降流 `g : [-1,1] → ℝ` 若在两端都"向内指"
    （左端 `g(-1) ≥ 0` 向右, 右端 `g(1) ≤ 0` 向左）, 则必有 `c ∈ [-1,1]` 使 `g c = 0`
    （停滞/不动点）。直观: 状态被"困"在闭区间无处可逃时, 连续下降必在内部卡住 ——
    这正是无残差时深层表示"坍缩/停滞"的拓扑强制版（"坑"）。 -/
theorem forced_zero_trapped (g : ℝ → ℝ) (hg : ContinuousOn g (Set.Icc (-1 : ℝ) 1))
    (hL : 0 ≤ g (-1)) (hR : g 1 ≤ 0) :
    ∃ c ∈ Set.Icc (-1 : ℝ) 1, g c = 0 := by
  have hab : (-1 : ℝ) ≤ 1 := by norm_num
  -- IVT（反向情形 f b ≤ t ≤ f a）: Icc (g 1) (g (-1)) ⊆ g '' Icc (-1) 1
  have hsub := intermediate_value_Icc' hab hg
  have h0 : (0 : ℝ) ∈ Set.Icc (g 1) (g (-1)) := ⟨hR, hL⟩
  have himg := hsub h0 -- 0 ∈ g '' Icc (-1) 1
  obtain ⟨c, hc, hgc⟩ := (Set.mem_image g (Set.Icc (-1 : ℝ) 1) 0).mp himg
  exact ⟨c, hc, hgc⟩

-- ============================================================
-- §2 残差越界: 打破"两端向内", 强制零点消失（L8 的拓扑根）
-- ============================================================

/-- **HB1-escape 残差打破强制零点**: 一旦允许状态越界（残差 = 离面/恒等路径,
    几何上相当于多一条"法向"自由度）, "两端向内"的困住条件即被破坏 ——
    存在连续且**处处无零点**的下降流 `g(x) = x + 2`（在 `[-1,1]` 上恒正, 右端向外指）。
    说明: 强制停滞只在"被闭域困住"时成立; 残差提供的逃逸通道使其不再成立 ——
    这正是 L8"深度有效当且仅当存在回馈"的拓扑内核。 -/
theorem residual_removes_forced_zero :
    ∃ g : ℝ → ℝ, ContinuousOn g (Set.Icc (-1 : ℝ) 1) ∧
      ∀ c : ℝ, -1 ≤ c → c ≤ 1 → g c ≠ 0 := by
  refine ⟨fun x => x + 2, ?_, ?_⟩
  · -- 连续
    exact (continuous_id.add continuous_const).continuousOn
  · -- 恒 > 0, 故处处非零
    intro c h1 h2
    linarith

-- ============================================================
-- §3 对照: 圆 S¹（奇维闭流形）可梳 —— 障碍是维度奇偶特异的
-- ============================================================

/-- 圆上每点的切向量场（逆时针单位切向）: 位置 `p(θ)=(cos θ, sin θ)` ↦ `(−sin θ, cos θ)`。 -/
def s1_tangent (θ : ℝ) : ℝ × ℝ := (-Real.sin θ, Real.cos θ)

/-- **HB1-contrast S¹ 处处非零切场（可梳）**: 圆的单位切向量场处处非零。
    偶维球面被毛球定理禁止这种场（HB1 目标）, 而奇维 S¹ 允许 —— 反衬
    "强制零点"是维度奇偶/几何特异的, 与毛球定理的偶维限制吻合。 -/
theorem s1_tangent_nonvanishing : ∀ θ : ℝ, s1_tangent θ ≠ (0, 0) := by
  intro θ h
  rw [s1_tangent] at h -- (−sin θ, cos θ) = (0, 0)
  have hs : Real.sin θ = 0 := by
    have := congrArg Prod.fst h; simpa using this
  have hc : Real.cos θ = 0 := by
    have := congrArg Prod.snd h; simpa using this
  have h1 : Real.sin θ ^ 2 + Real.cos θ ^ 2 = 1 := Real.sin_sq_add_cos_sq θ
  simp only [hs, hc] at h1
  norm_num at h1

/-- **S¹ 切向量确与位置正交**: `(cos θ, sin θ)·(−sin θ, cos θ) = 0`
    （确为切向量, 非任意非零向量）。 -/
theorem s1_tangent_orthogonal : ∀ θ : ℝ,
    Real.cos θ * (-Real.sin θ) + Real.sin θ * Real.cos θ = 0 := by
  intro θ
  ring

end HairyBall
