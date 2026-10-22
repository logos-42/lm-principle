/- 
# L-eta — 缺口 #2 的优化效率一侧: 损失随优化效率单调不增（条件性方向内核）

目标 (`docs/wiki/gap2-rnt-derivation.md` 的 L-eta): G2 的可达率
`R_ach = min(R_cap(N), R_data(T)) · η(N,T)`, 其中 `η ∈ [0,1]` 是**优化效率**
（梯度下降多接近率-失真最优）。E13 旧版曾测到"训练损失可低于熵地板（记忆化）⟹ 优化
非绑定项, η 在部分 regime ≈1", 但 η 的一般值是项目最空白处（无优化理论）。

本文件只给**严格方向内核**（条件性, 不碰 η 的具体数值）:
  以率-失真函数 `D(R)` 关于率**非增**（率越多失真越低, 注水基本事实）为假设输入, 推出:
    - `loss_mono_in_eta`: 损失 `L(η) = H_floor + D(η·R₀)` 随优化效率 η **单调不增**;
    - `eff_rate_mono`: 有效可达率 `η·R₀` 随 η 单调不减。
  即"优化越充分 (η→1), 损失越低逼近率-失真下界; η=0 则完全没优化、损失最高"。

**诚实边界**: 本内核只证"损失随 η 下降的方向"; η 的**具体值/上界**（= 优化缺口③,
需收敛率/Lyapunov/临界性理论）是真正困难处, 不在此Lean中断言, 记为开放。
`D(R)` 非增是外部假设（注水的率-失真单调性, 本项目未形式化 water-filling 本身）。
-/
import Mathlib.Order.Basic
import Mathlib.Tactic

noncomputable section

namespace OptEff

/-- **L-eta-core 损失随优化效率单调不增**: 率-失真函数 `D(R)` 非增（率越多失真越低）,
    不可约地板 `H_floor ≥ 0` 意义上的总损失 `L(η) = H_floor + D(η·R₀)`, 基率 `R₀ ≥ 0`。
    则优化效率越高（`η₁ ≤ η₂`）, 损失越低。直观: 优化越充分, 越逼近率-失真下界;
    η=0（完全没优化）时损失最高。这是 L-eta 的严格方向内核, 与 `DataRate.data_rate_mono`
    （数据率随 T 增）共同给出 G2 的单调结构。 -/
theorem loss_mono_in_eta (D : ℝ → ℝ) (hD : Antitone D) (H_floor R0 : ℝ) (hR0 : 0 ≤ R0)
    {eta1 eta2 : ℝ} (_h0 : 0 ≤ eta1) (h : eta1 ≤ eta2) :
    H_floor + D (eta2 * R0) ≤ H_floor + D (eta1 * R0) := by
  have hr : eta1 * R0 ≤ eta2 * R0 := mul_le_mul_of_nonneg_right h hR0
  have hd : D (eta2 * R0) ≤ D (eta1 * R0) := hD hr
  linarith

/-- **有效可达率随优化效率单调不减**: `η·R₀` 随 η 不减（`R₀ ≥ 0`）。
    优化效率直接线性放大有效可达率。 -/
theorem eff_rate_mono (R0 : ℝ) (hR0 : 0 ≤ R0) {eta1 eta2 : ℝ} (h : eta1 ≤ eta2) :
    eta1 * R0 ≤ eta2 * R0 :=
  mul_le_mul_of_nonneg_right h hR0

/-- **G2 方向合成 (L-eta × L-data)**: 对同一非增失真函数 `D`, 若把"更多数据/更充分优化"
    都体现为有效可达率的提升（`R₁ ≤ R₂`）, 则损失单调不增:
    `H_floor + D(R₂) ≤ H_floor + D(R₁)`。—— 数据量 T↑（L-data）与优化效率 η↑（L-eta）
    都朝同一方向压低损失, 这是 G2 = `min(R_cap, R_data)·η` 的单调性底座。 -/
theorem loss_mono_in_rate (D : ℝ → ℝ) (hD : Antitone D) (H_floor : ℝ)
    {R1 R2 : ℝ} (h : R1 ≤ R2) :
    H_floor + D R2 ≤ H_floor + D R1 := by
  have hd : D R2 ≤ D R1 := hD h
  linarith

end OptEff
