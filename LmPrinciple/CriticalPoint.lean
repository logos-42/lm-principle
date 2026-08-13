/-
# 临界点定理: 收益成本不等式的精确位置 (CriticalPoint.lean)

C2 (最优深度存在) 的开放问题: "分形维数 D ⟹ 具体最优深度公式" 只给存在性,
不给闭式解。本文件补齐: **最优深度 = 第一个边际收益跌破边际成本的层**。

## 定理结构

[0] 模型: 净收益 N(L) = Σ_{k<L} Δ_k - λ·L (Δ_k = 第 k 层边际收益,
    λ = 每层成本)。

[1] **临界点定理** (optimal_depth_is_first_crossing):
    假设 Δ 严格递减 + λ > 0 + 收益最终跌破成本 (∃k₀, ∀k≥k₀, Δ_k < λ)
    ⟹ 最优深度 kstar = Nat.find (fun k => Δ k < λ) —— **第一个跌破点**,
    且 ∀L, N(L) ≤ N(kstar)。这是"深度不是越深越好"的精确位置:
    在 kstar 之前每层净收益上升 (Δ_k ≥ λ), 在 kstar 之后每层净收益下降
    (Δ_k < λ), 所以临界点就是全局最优。

[2] **幂律临界点对** (power_law_critical_pair):
    Δ_k = c/(k+1)² (c > 0) 时, 跌破点 kstar 满足
    Δ_{kstar} < λ ≤ Δ_{kstar-1} (kstar > 0) —— 收益成本不等式的两侧夹逼。
    (闭式: kstar = ⌈(c/λ)^(1/2)⌉-1 或 = (c/λ)^(1/2), 数值验证见
    scripts/diagnose_murray_cost.py 同族脚本)

与 Murray.lean 的关系: 那里的 optimal_depth_exists 证明存在性 (L* ≤ k₀+1,
不需要单调性); 本文件给出**精确临界点** (需要单调性保证跌破点唯一)。
-/
import Mathlib.Data.Nat.Find
import LmPrinciple.Murray

noncomputable section
open Finset
open scoped BigOperators

namespace CriticalPoint

/-- 净收益 N(L) = Σ_{k<L} Δ_k - λ·L -/
def netBenefit (Δ : ℕ → ℝ) (mc : ℝ) (L : ℕ) : ℝ :=
  (∑ k in range L, Δ k) - mc * L

/-- **临界点定理**: 边际收益 Δ_k 严格递减 (hdec) + 成本为正 (hmc)
    + 收益最终跌破成本 (hcross) ⟹
    最优深度恰为第一个跌破点 kstar = Nat.find (fun k => Δ k < mc),
    即 ∀L, N(L) ≤ N(kstar)。kstar 前每层 Δ ≥ mc (净收益上升),
    kstar 后每层 Δ < mc (净收益下降) —— 收益成本不等式的临界位置。
    证明: kstar = Nat.find 给出 Δ kstar < mc (find_spec) 且
    ∀m < kstar, mc ≤ Δ m (find_min); 链式上升/下降闭合。 -/
theorem optimal_depth_is_first_crossing (Δ : ℕ → ℝ) (mc : ℝ)
    (hdec : ∀ {k j : ℕ}, k < j → Δ j < Δ k)
    (hmc : 0 < mc) (hcross : ∃ k₀ : ℕ, ∀ k ≥ k₀, Δ k < mc) :
    let kstar : ℕ := Nat.find (p := fun k => Δ k < mc)
        (by rcases hcross with ⟨k₀, hk₀⟩; exact ⟨k₀, hk₀ k₀ (le_refl k₀)⟩)
    ∀ L : ℕ, netBenefit Δ mc L ≤ netBenefit Δ mc kstar := by
  have hfind : ∃ n : ℕ, Δ n < mc := by
    rcases hcross with ⟨k₀, hk₀⟩
    exact ⟨k₀, hk₀ k₀ (le_refl k₀)⟩
  let kstar : ℕ := Nat.find hfind
  change ∀ L : ℕ, netBenefit Δ mc L ≤ netBenefit Δ mc kstar
  have hstep : ∀ m : ℕ, netBenefit Δ mc (m + 1) - netBenefit Δ mc m = Δ m - mc := by
    intro m
    unfold netBenefit
    rw [sum_range_succ]
    rw [Nat.cast_add]
    ring
  have hspec : Δ kstar < mc := Nat.find_spec hfind
  have hmin : ∀ m : ℕ, m < kstar → ¬ Δ m < mc :=
    fun m hm => Nat.find_min hfind hm
  have hge : ∀ m : ℕ, m < kstar → mc ≤ Δ m := by
    intro m hm
    exact le_of_not_gt (hmin m hm)
  -- kstar 之前: 每步净收益上升 (Δ_m ≥ mc ⟹ N(m+1) ≥ N(m))
  have hmono : ∀ m : ℕ, m < kstar → netBenefit Δ mc m ≤ netBenefit Δ mc (m + 1) := by
    intro m hm
    have hd : netBenefit Δ mc (m + 1) - netBenefit Δ mc m = Δ m - mc := hstep m
    have hnonneg : 0 ≤ netBenefit Δ mc (m + 1) - netBenefit Δ mc m := by
      rw [hd]
      linarith [hge m hm]
    linarith
  have hle1 : ∀ {a b : ℕ}, a ≤ b → b ≤ kstar → netBenefit Δ mc a ≤ netBenefit Δ mc b := by
    intro a b hab hbk
    let d : ℕ := b - a
    have hb : a + d = b := by omega
    have hmain : ∀ d : ℕ, a + d ≤ kstar → netBenefit Δ mc a ≤ netBenefit Δ mc (a + d) := by
      intro d
      induction d with
      | zero => simp
      | succ d ih =>
          intro hle
          have hlt : a + d < kstar := by omega
          exact le_trans (ih (by omega)) (hmono (a + d) hlt)
    have hres := hmain d (by omega)
    simpa [hb] using hres
  -- kstar 之后: 严格递减 (Δ 严格递减 + Δ kstar < mc ⟹ 每步净收益下降)
  have hlt_ge : ∀ m : ℕ, kstar ≤ m → Δ m < mc := by
    intro m hm
    by_cases h : m = kstar
    · simpa [h] using hspec
    · have hlt : kstar < m := lt_of_le_of_ne hm (Ne.symm h)
      exact lt_trans (hdec hlt) hspec
  have hmono' : ∀ m : ℕ, kstar ≤ m → netBenefit Δ mc (m + 1) ≤ netBenefit Δ mc m := by
    intro m hm
    have hd : netBenefit Δ mc (m + 1) - netBenefit Δ mc m = Δ m - mc := hstep m
    have hle0 : netBenefit Δ mc (m + 1) - netBenefit Δ mc m ≤ 0 := by
      rw [hd]
      linarith [hlt_ge m hm]
    linarith
  have hle2 : ∀ {a b : ℕ}, kstar ≤ a → a ≤ b → netBenefit Δ mc b ≤ netBenefit Δ mc a := by
    intro a b hka hab
    let d : ℕ := b - a
    have hb : a + d = b := by omega
    have hmain : ∀ d : ℕ, kstar ≤ a → netBenefit Δ mc (a + d) ≤ netBenefit Δ mc a := by
      intro d
      induction d with
      | zero => simp
      | succ d ih =>
          intro hk
          exact le_trans (hmono' (a + d) (by omega)) (ih hk)
    have hres := hmain d hka
    simpa [hb] using hres
  -- 结论: L ≤ kstar 用上升链, L ≥ kstar 用下降链
  intro L
  by_cases hL : L ≤ kstar
  · exact hle1 hL (le_rfl)
  · have hkL : kstar ≤ L := le_of_not_ge hL
    exact hle2 (le_rfl) hkL

/-- **幂律临界点对**: Δ_k = c/(k+1)² (c > 0) 的跌破点 kstar 满足
    Δ_{kstar} < λ ≤ Δ_{kstar-1} (kstar > 0 时) —— 收益成本不等式的两侧夹逼,
    即临界层 kstar 是最后一个 Δ ≥ λ 与第一个 Δ < λ 之间的分界。
    (闭式: kstar = ⌈(c/λ)^(1/2)⌉-1; 数值验证见 scripts/) -/
theorem power_law_critical_pair (c mc : ℝ) (hc : 0 < c) (hmc : 0 < mc) :
    let kstar : ℕ := Nat.find (p := fun k => c / (k + 1 : ℝ) ^ 2 < mc)
        (by
          rcases (Murray.power_law_marginal_decays c hc).2 mc hmc with ⟨k₀, hk₀⟩
          exact ⟨k₀, hk₀ k₀ (le_refl k₀)⟩)
    c / (kstar + 1 : ℝ) ^ 2 < mc ∧ (kstar = 0 ∨ mc ≤ c / kstar ^ 2) := by
  have hfind : ∃ n : ℕ, c / (n + 1 : ℝ) ^ 2 < mc := by
    rcases (Murray.power_law_marginal_decays c hc).2 mc hmc with ⟨k₀, hk₀⟩
    exact ⟨k₀, hk₀ k₀ (le_refl k₀)⟩
  let kstar : ℕ := Nat.find hfind
  change c / (kstar + 1 : ℝ) ^ 2 < mc ∧ (kstar = 0 ∨ mc ≤ c / kstar ^ 2)
  constructor
  · exact Nat.find_spec hfind
  · by_cases hk0 : kstar = 0
    · exact Or.inl hk0
    · apply Or.inr
      have hpos : 0 < kstar := Nat.pos_of_ne_zero hk0
      have hlt : kstar - 1 < kstar := Nat.sub_lt hpos (by decide : 0 < 1)
      have hmin : ¬ c / (↑(kstar - 1) + 1) ^ 2 < mc :=
        Nat.find_min hfind hlt
      have hcast : (kstar - 1 : ℕ) + 1 = kstar := Nat.sub_add_cancel (Nat.succ_le_of_lt hpos)
      have hcast' : (↑(kstar - 1) + 1 : ℝ) = (kstar : ℝ) := by
        have h := congrArg (fun n : ℕ => (n : ℝ)) hcast
        simpa [Nat.cast_add] using h
      have hnot : ¬ c / (kstar : ℝ) ^ 2 < mc := by
        rw [← hcast']
        exact hmin
      exact le_of_not_gt hnot

/-- **组合: 幂律收益 ⟹ 临界点即最优深度** —— 把临界点定理实例化到
    Δ_k = c/(k+1)²: 第一个跌破点 kstar 是最优深度, 且两侧不等式闭合
    (Δ_{kstar} < λ ≤ Δ_{kstar-1}), 收益成本不等式的位置被精确锁定。 -/
theorem power_law_optimal_depth_is_critical (c mc : ℝ) (hc : 0 < c) (hmc : 0 < mc) :
    let kstar : ℕ := Nat.find (p := fun k => c / (k + 1 : ℝ) ^ 2 < mc)
        (by
          rcases (Murray.power_law_marginal_decays c hc).2 mc hmc with ⟨k₀, hk₀⟩
          exact ⟨k₀, hk₀ k₀ (le_refl k₀)⟩)
    (∀ L : ℕ, netBenefit (fun k => c / (k + 1 : ℝ) ^ 2) mc L ≤
      netBenefit (fun k => c / (k + 1 : ℝ) ^ 2) mc kstar) ∧
    (c / (kstar + 1 : ℝ) ^ 2 < mc ∧ (kstar = 0 ∨ mc ≤ c / kstar ^ 2)) := by
  constructor
  · -- 单调性: 幂律严格递减 (Murray.power_law_marginal_decays.1)
    have hdec : ∀ {k j : ℕ}, k < j → c / (j + 1 : ℝ) ^ 2 < c / (k + 1 : ℝ) ^ 2 :=
      fun {k j} hkj => (Murray.power_law_marginal_decays c hc).1 hkj
    have hcross : ∃ k₀ : ℕ, ∀ k ≥ k₀, c / (k + 1 : ℝ) ^ 2 < mc :=
      (Murray.power_law_marginal_decays c hc).2 mc hmc
    exact optimal_depth_is_first_crossing (fun k => c / (k + 1 : ℝ) ^ 2) mc hdec hmc hcross
  · exact power_law_critical_pair c mc hc hmc

end CriticalPoint
