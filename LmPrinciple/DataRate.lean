/- 
# L-data — 缺口 #2 的数据率一侧: 可达率随数据量单调不减（条件性内核）

目标 (`docs/wiki/gap2-rnt-derivation.md` 的 L-data): 解释 E13 反演的经验事实——
可达率被**数据 T 门控**（`R_needed ∝ lnT` 斜率 +0.83 > 0）: 数据越多, 可达率越高。

本文件给**严格方向内核**（条件性, 与项目"条件性定理"风格一致）:
  以 UWS (arXiv:2512.05117) 定理 3.7 的估计地板 `ε(T) ~ c/√T`（谱估计误差随 T 下降,
  来自其 Lemma 3.5 集中性 `‖Ŝ−S‖_op ≤ c/√T`）为**假设输入（不证）**, 推出:
    - `data_rate_mono`: 数据率 `R_data(T) = Σ_{i<n} max(lam_i − ε T) 0` 随 T 单调不减;
    - `usable_modes_mono`: 越过噪声地板的可用谱模数随 T 单调不减。
  即"感知量 T 越多 ⟹ 谱估计越干净 ⟹ 可用谱模越多/信号越强 ⟹ 可达率越高"。

**诚实边界**: 本内核只证"单调不减/数据门控的方向"; 具体幂指数（E13 实测 ~0.83,
以及 `min(R_cap, R_data)·η` 的 `min` 与 `η` 两项）是经验/假设量, 不在此Lean中断言。
UWS 的 `T^{-1/2}` 地板是外部假设（本项目未形式化该前提）; 其具体实例 `ε(T)=c/√T`
满足 `Antitone ε` 是初等事实（c≥0, T>0 ⟹ √T 单调 ⟹ 1/√T 反单调）, 此处不展开以免引入 sqrt 依赖。
-/
import Mathlib.Order.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Data.Finset.Range
import Mathlib.Tactic

noncomputable section

namespace DataRate

/-- 单个谱模在噪声地板之上的"可用信号": `max (lam − ε) 0`。 -/
def usable (lam ε : ℝ) : ℝ := max (lam - ε) 0

/-- **L-data-core 数据率随数据量单调不减**: 频谱值 `lam i ≥ 0`, 噪声地板 `ε` 关于 T 单调不增
    （`Antitone ε`, 如 UWS 的 `ε(T)=c/√T`）, 则数据率 `R_data(T)=Σ_{i<n} max(lam_i − ε T) 0`
    随 T 不减。直观: T 越大 ⟹ `ε T` 越小 ⟹ 每个谱模高出地板的部分越大 ⟹ 可达率越高。
    —— 这是 E13 反演"可达率被数据 T 门控（∂R/∂lnT > 0）"的严格方向内核。 -/
theorem data_rate_mono (lam : ℕ → ℝ) (ε : ℝ → ℝ)
    (hε : Antitone ε) (n : ℕ) {T₁ T₂ : ℝ} (hT : T₁ ≤ T₂) :
    Finset.sum (Finset.range n) (fun i => usable (lam i) (ε T₁)) ≤
      Finset.sum (Finset.range n) (fun i => usable (lam i) (ε T₂)) := by
  have he : ε T₂ ≤ ε T₁ := hε hT
  induction n with
  | zero => simp
  | succ n ih =>
      rw [Finset.sum_range_succ, Finset.sum_range_succ]
      have hpt : usable (lam n) (ε T₁) ≤ usable (lam n) (ε T₂) := by
        simp only [usable]
        exact max_le_max (by linarith) le_rfl
      exact add_le_add ih hpt

/-- **可用谱模数随数据量单调不减**: 噪声地板下降 ⟹ 越过地板（`ε T ≤ lam i`）的谱模只增不减。
    直观: 数据越多, 越多谱模式从"埋在噪声里"变为"可分辨/可用"。 -/
theorem usable_modes_mono (lam : ℕ → ℝ) (ε : ℝ → ℝ)
    (hε : Antitone ε) (n : ℕ) {T₁ T₂ : ℝ} (hT : T₁ ≤ T₂) :
    ((Finset.range n).filter (fun i => ε T₁ ≤ lam i)) ⊆
      ((Finset.range n).filter (fun i => ε T₂ ≤ lam i)) := by
  have hle : ε T₂ ≤ ε T₁ := hε hT
  intro i hi
  simp only [Finset.mem_filter, Finset.mem_range] at hi ⊢
  obtain ⟨hir, hlami⟩ := hi
  exact ⟨hir, by linarith⟩

end DataRate
