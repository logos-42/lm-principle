/- 
# Folding — "毛球向内折叠" = 优化效率 η 的几何形式化（用户直觉 → Lean）

用户直觉 (2026-10-22): "梯度下降是，找这个毛球怎么向内折叠" —— 优化 = 把表示流形
(毛球) 往低失真方向折叠; "深度的坑是毛球定理产生的结构"; 残差让它越过奇点继续折。

本文件把这个直觉形式化为**折叠深度 η ∈ [0,1]** (优化效率的几何化身), 全部机器验证:
  - `residual_excess E0 η = E0·(1−η)`      : 折叠后**还没折掉**的可约失真 (超额)
  - `loss_after_fold H E0 η = H + E0·(1−η)` : 折叠后总损失 = 不可约地板 + 剩余可约超额
  - `loss_after_fold_mono`   : 折叠越深 (η↑) 损失越低          —— "向内折叠 ⟹ 损失下降"
  - `full_fold_reaches_floor`: η=1 (折到底) ⟹ 损失 = 地板       —— 对应实测"训练记忆化、loss 压到地板下"
  - `no_fold_full_excess`    : η=0 (没折)   ⟹ 损失 = 地板 + E0
  - `capped_fold_above_floor`: 折叠被封顶在 η_max<1 ⟹ 损失 > 地板 (下不去)

**HB1 桥 (与 HairyBall.lean 的连接, 建模桥非拓扑等价)**:
  "纯切向折叠必在强制零点卡住 ⟹ 被封顶 η_max<1" 这一拓扑前提来自
  `HairyBall.forced_zero_trapped`; "残差 (法向逃逸) 解封 ⟹ 可达 η=1" 来自
  `HairyBall.residual_removes_forced_zero`。本文件只证**标量算术** (给定 η 的损失结构);
  "标量 η ↔ 拓扑零点" 的对应是建模假设, 诚实标注, 不当成已证的拓扑等价。

**在 G2 中的位置**: `R_ach = min(R_cap(N), R_data(T))·η`, 其中 η = 折叠深度。
  L-data (DataRate.lean: R_data 随 T↑) + 本文件 (损失随 η↑↓) 合成"更多数据/更深折叠都压低损失"。
-/
import Mathlib.Order.Basic
import Mathlib.Tactic

noncomputable section

namespace Folding

/-- 折叠后**剩余的可约失真** (还没折掉的超额): `E(η) = E₀·(1−η)`。
    `E₀ ≥ 0` 是谱给出的可约失真总量 (如 D0); `η ∈ [0,1]` 是折叠深度。 -/
def residual_excess (E0 η : ℝ) : ℝ := E0 * (1 - η)

/-- 折叠后的**总损失**: `L(η) = H_floor + E₀·(1−η)` = 不可约地板 + 剩余可约超额。 -/
def loss_after_fold (H_floor E0 η : ℝ) : ℝ := H_floor + residual_excess E0 η

/-- 折叠越深, 剩余超额越少 (η₁ ≤ η₂ ⟹ E(η₂) ≤ E(η₁))。 -/
theorem residual_excess_mono (E0 : ℝ) (hE0 : 0 ≤ E0) {η1 η2 : ℝ}
    (_h1 : 0 ≤ η1) (_h2 : η2 ≤ 1) (h : η1 ≤ η2) :
    residual_excess E0 η2 ≤ residual_excess E0 η1 := by
  simp only [residual_excess]
  have hle : 1 - η2 ≤ 1 - η1 := by linarith
  exact mul_le_mul_of_nonneg_left hle hE0

/-- **折叠越深, 损失越低** ("毛球向内折叠" ⟹ 损失下降)。 -/
theorem loss_after_fold_mono (H_floor E0 : ℝ) (hE0 : 0 ≤ E0) {η1 η2 : ℝ}
    (h1 : 0 ≤ η1) (h2 : η2 ≤ 1) (h : η1 ≤ η2) :
    loss_after_fold H_floor E0 η2 ≤ loss_after_fold H_floor E0 η1 := by
  have hre := residual_excess_mono E0 hE0 h1 h2 h
  simp only [loss_after_fold]
  linarith

/-- **完全折叠 (η=1) ⟹ 损失降到不可约地板**。对应实测"训练能记忆化、loss 压到地板下"
    (E13: dim192/T160K 训练损失 1.556 < xz 地板 1.628)。 -/
theorem full_fold_reaches_floor (H_floor E0 : ℝ) :
    loss_after_fold H_floor E0 1 = H_floor := by
  simp [loss_after_fold, residual_excess]

/-- **不折叠 (η=0) ⟹ 损失 = 地板 + 全部可约超额 E₀** (完全没优化)。 -/
theorem no_fold_full_excess (H_floor E0 : ℝ) :
    loss_after_fold H_floor E0 0 = H_floor + E0 := by
  simp [loss_after_fold, residual_excess]

/-- **HB1 桥 (算术下界)**: 折叠被封顶在 `η_max < 1` ⟹ 损失 `> H_floor` (下不去地板)。
    拓扑前提"纯切向折叠必被封顶"来自 `HairyBall.forced_zero_trapped` (强制零点),
    "残差解封" 来自 `HairyBall.residual_removes_forced_zero`; 标量 η ↔ 拓扑零点是建模桥。 -/
theorem capped_fold_above_floor (H_floor E0 η_max : ℝ) (hE0 : 0 < E0) (hcap : η_max < 1) :
    H_floor < loss_after_fold H_floor E0 η_max := by
  simp only [loss_after_fold, residual_excess]
  have h : 0 < E0 * (1 - η_max) := mul_pos hE0 (by linarith)
  linarith

/-- **残差解封 ⟹ 完全折叠可达 ⟹ 损失降到地板** (接 `full_fold_reaches_floor`;
    拓扑上由 `HairyBall.residual_removes_forced_zero` 保证折叠不被奇点卡死)。 -/
theorem residual_enables_full_fold (H_floor E0 : ℝ) :
    loss_after_fold H_floor E0 1 = H_floor :=
  full_fold_reaches_floor H_floor E0

end Folding
