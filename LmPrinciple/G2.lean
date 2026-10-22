/-
# G2 — 可达率与预测损失的组装定理 (缺口 #2 目标式的 Lean 形态)

组装 `docs/wiki/gap2-rnt-derivation.md` 的目标式:
    R_ach(N,T) = min(R_cap(N), R_data(T)) · η(N,T)
    L(N,T)     = H_floor + D(R_ach)          (D = 注水失真)

本文件证**单调结构** (给定 D 非增):
  - `r_ach`                : R_ach = min(R_cap, R_data)·η
  - `r_ach_mono_data`      : R_ach 随数据率 R_data 不减   (更多数据 → 更高可达率)
  - `r_ach_mono_eta`       : R_ach 随折叠效率 η 不减      (折得越深 → 更高可达率)
  - `g2_loss_mono_data`    : 损失随 R_data 不增           (数据↑ → 损失↓)
  - `g2_loss_mono_eta`     : 损失随 η 不增                (折叠↑ → 损失↓)
  - `g2_loss_mono_both`    : 数据↑ 且折叠↑ ⟹ 损失↓       (合成)

**依赖关系**: `hD : Antitone D` 是输入假设, 现由 `WaterFilling.distortion_antitone_rate`
(注水结构) **证明**, 不再是无来源的假设。`R_cap`(Efficiency)/`R_data`(DataRate)/`η`(Folding)
的具体形式在各自模块; 本文件只管 `min·η` 与 `H+D` 的组装单调性。

诚实边界: 本文件给 G2 的**方向/单调骨架**; `min` 的切换点 (L-switch, crossover N*(T))
与 D 的 KKT 最优性是更深内容, 分别留待 L-switch 与率-失真定理。
-/
import Mathlib.Order.Basic
import Mathlib.Tactic

noncomputable section

namespace G2

/-- G2 可达率: `R_ach = min(R_cap(N), R_data(T)) · η` (容量率、数据率取小, 再乘折叠效率)。 -/
def r_ach (R_cap R_data eta : ℝ) : ℝ := min R_cap R_data * eta

/-- G2 预测损失: `L = H_floor + D(R_ach)` (不可约地板 + 可达率处的注水失真)。 -/
def g2_loss (H_floor : ℝ) (D : ℝ → ℝ) (Rach : ℝ) : ℝ := H_floor + D Rach

/-- `R_ach` 关于数据率 `R_data` 单调不减 (min 单调, η ≥ 0): 更多数据 → 更高可达率。 -/
theorem r_ach_mono_data (R_cap eta : ℝ) (heta : 0 ≤ eta) {d1 d2 : ℝ} (h : d1 ≤ d2) :
    r_ach R_cap d1 eta ≤ r_ach R_cap d2 eta := by
  unfold r_ach
  exact mul_le_mul_of_nonneg_right (min_le_min (le_refl R_cap) h) heta

/-- `R_ach` 关于折叠效率 `η` 单调不减 (min ≥ 0 因 R_cap, R_data ≥ 0): 折得越深 → 更高可达率。 -/
theorem r_ach_mono_eta (R_cap R_data : ℝ) (hcap : 0 ≤ R_cap) (hRD : 0 ≤ R_data)
    {e1 e2 : ℝ} (h : e1 ≤ e2) :
    r_ach R_cap R_data e1 ≤ r_ach R_cap R_data e2 := by
  unfold r_ach
  have hmin : 0 ≤ min R_cap R_data := by
    rcases le_total R_cap R_data with hc | hc
    · rw [min_eq_left hc]; exact hcap
    · rw [min_eq_right hc]; exact hRD
  exact mul_le_mul_of_nonneg_left h hmin

/-- **G2: 损失关于数据率 R_data 单调不增** (D 非增)。更多数据 → R_data↑ → R_ach↑ → 失真↓ → 损失↓。 -/
theorem g2_loss_mono_data (H_floor : ℝ) (D : ℝ → ℝ) (hD : Antitone D) (R_cap eta : ℝ)
    (heta : 0 ≤ eta) {d1 d2 : ℝ} (h : d1 ≤ d2) :
    g2_loss H_floor D (r_ach R_cap d2 eta) ≤ g2_loss H_floor D (r_ach R_cap d1 eta) := by
  have h1 : r_ach R_cap d1 eta ≤ r_ach R_cap d2 eta := r_ach_mono_data R_cap eta heta h
  have h2 : D (r_ach R_cap d2 eta) ≤ D (r_ach R_cap d1 eta) := hD h1
  show H_floor + D (r_ach R_cap d2 eta) ≤ H_floor + D (r_ach R_cap d1 eta)
  linarith

/-- **G2: 损失关于折叠效率 η 单调不增** (D 非增)。折得越深 → R_ach↑ → 失真↓ → 损失↓。 -/
theorem g2_loss_mono_eta (H_floor : ℝ) (D : ℝ → ℝ) (hD : Antitone D) (R_cap R_data : ℝ)
    (hcap : 0 ≤ R_cap) (hRD : 0 ≤ R_data) {e1 e2 : ℝ} (h : e1 ≤ e2) :
    g2_loss H_floor D (r_ach R_cap R_data e2) ≤ g2_loss H_floor D (r_ach R_cap R_data e1) := by
  have h1 : r_ach R_cap R_data e1 ≤ r_ach R_cap R_data e2 := r_ach_mono_eta R_cap R_data hcap hRD h
  have h2 : D (r_ach R_cap R_data e2) ≤ D (r_ach R_cap R_data e1) := hD h1
  show H_floor + D (r_ach R_cap R_data e2) ≤ H_floor + D (r_ach R_cap R_data e1)
  linarith

/-- **G2 合成: 数据↑ 且折叠↑ ⟹ 损失↓** (两个方向都压低损失, 合成 G2 的完整单调性)。 -/
theorem g2_loss_mono_both (H_floor : ℝ) (D : ℝ → ℝ) (hD : Antitone D) (R_cap : ℝ)
    (hcap : 0 ≤ R_cap) {d1 d2 e1 e2 : ℝ} (hd2 : 0 ≤ d2) (he1 : 0 ≤ e1)
    (hd : d1 ≤ d2) (he : e1 ≤ e2) :
    g2_loss H_floor D (r_ach R_cap d2 e2) ≤ g2_loss H_floor D (r_ach R_cap d1 e1) := by
  have s1 : r_ach R_cap d1 e1 ≤ r_ach R_cap d2 e1 := r_ach_mono_data R_cap e1 he1 hd
  have s2 : r_ach R_cap d2 e1 ≤ r_ach R_cap d2 e2 := r_ach_mono_eta R_cap d2 hcap hd2 he
  have h1 : r_ach R_cap d1 e1 ≤ r_ach R_cap d2 e2 := le_trans s1 s2
  have h2 : D (r_ach R_cap d2 e2) ≤ D (r_ach R_cap d1 e1) := hD h1
  show H_floor + D (r_ach R_cap d2 e2) ≤ H_floor + D (r_ach R_cap d1 e1)
  linarith

end G2
