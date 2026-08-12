/-
# 参数利用效率对比 — Lean 推演 (Efficiency.lean)

用户问题: 对比 Transformer 的参数利用效率与其他模型 (RNN/CNN/LSTM),
结合假设 (分形自由能下降 / 不坍缩 / 信息流动高效)。

**参数利用效率 = 每单位参数的信息处理量**, 分两个可验证维度:

  维度一: 每参数交互率 (组合计数, 静态架构)
  ┌────────────┬────────────┬──────────────┬──────────────────────┐
  │ 架构        │ 交互对数    │ 参数数        │ 每参数交互率          │
  ├────────────┼────────────┼──────────────┼──────────────────────┤
  │ RNN        │ n (转移)    │ 1 (标量 w)    │ n                     │
  │ CNN        │ n·k (核窗)  │ k (核支持)    │ n (核复用)            │
  │ LSTM       │ n (门控)    │ 2 (α, 门权)   │ n/2                   │
  │ Transformer│ n² (全两两) │ 3d² (Q,K,V)  │ n²/(3d²) (与 n 无关)   │
  └────────────┴────────────┴──────────────┴──────────────────────┘
  → 注意力参数**与序列长度 n 无关** (跨位置共享), 交互数 O(n²):
    序列足够长 (3d² < n) 时, 注意力每参数交互率反超 RNN (定理 1-3)。

  维度二: 每参数信息保留率 (动态, 结合 ArchCompare/Fractal 定理)
  ┌────────────┬──────────────────────┬───────────────────────────┐
  │ 架构        │ 信息保留 (每步乘数)   │ 参数利用效率解读           │
  ├────────────┼──────────────────────┼───────────────────────────┤
  │ RNN        │ |w| < 1 固定衰减      │ 唯一参数 w 同时负责计算和   │
  │            │ (rnn_memory_decay)   │ 记忆——效率被稳定性锁死     │
  │ LSTM       │ α 可学到 1           │ 遗忘门参数把"保留多少"     │
  │            │ (lstm_memory_retention│ 变成可学习——同样参数预算   │
  │            │ + forget_gate_upper) │ 下信息保留率可任意接近 100%│
  │ 残差块     │ 1-c, c 可小          │ 恒等路径参数效率 = 保底     │
  │            │ (residual_no_collapse│ (不坍缩定理)               │
  │ Transformer│ 凸组合 + 残差         │ 参数买"方向多样性"(凸包),  │
  │            │ (attention_error_    │ 误差有界 = 不浪费参数       │
  │            │ bound)               │                            │
  └────────────┴──────────────────────┴───────────────────────────┘

**结合用户假设的结论**:
  [1] 长序列 (n > 3d²): Transformer 每参数交互率最高——全局交互的
      规模经济; 但参数买的是凸包内的"方向", 不是无限能力
      (attention_error_bound: 误差 ≤ 最差记忆——参数效率有上界)。
  [2] 记忆任务: LSTM/残差的参数利用效率 > RNN——同样的 1-2 个参数,
      门控/恒等路径把信息保留率从指数衰减 (|w|^t) 提升到可学习
      (α^t → 1, 定理 5 对比)。
  [3] 分形组织 (Fractal.lean): 在参数预算 B 下, 把参数集中在收益递减
      序列的前缀 (浅层) = 参数利用效率最高的分配 (prefix_allocation_
      optimal)——"每参数的边际自由能下降"最大化。
-/
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Positivity
import LmPrinciple.ArchCompare
import LmPrinciple.Fractal

noncomputable section
open Finset
open scoped BigOperators

namespace Efficiency

-- ============================================================
-- §1 每参数交互率 (组合计数)
-- ============================================================

/-- **自注意力交互对数**: n 个 token 两两交互 (含自身) = n²。
    RNN/CNN/LSTM 的交互数 = O(n) (每步/每位置一次) —— 注意力的
    交互数超线性。 -/
theorem attention_interaction_count (n : ℕ) :
    (Finset.univ : Finset (Fin n × Fin n)).card = n ^ 2 := by
  simp [Fintype.card_prod, pow_two]

/-- **每参数交互率反超条件**: 注意力每参数交互率 n²/(3d²) > RNN 的 n
    ⟺ 3d² < n——序列长度超过参数量规模时, 注意力的全局交互
    每参数效率反超 RNN。 -/
theorem attention_more_interactions_per_param (n d : ℝ) (hn : 0 < n) (hd : 0 < d) :
    n ^ 2 / (3 * d ^ 2) > n ↔ 3 * d ^ 2 < n := by
  have hden : (0 : ℝ) < 3 * d ^ 2 := by positivity
  constructor
  · intro h
    -- h : n < n²/(3d²) ⟹ n·(3d²) < n² ⟹ 3d² < n (除以 n > 0)
    have h1 : n * (3 * d ^ 2) < n ^ 2 := by
      have hh := mul_lt_mul_of_pos_right h hden
      -- hh : n·(3d²) < (n²/(3d²))·(3d²)
      field_simp [ne_of_gt hden] at hh
      exact hh
    have hnz : n ≠ 0 := ne_of_gt hn
    calc
      3 * d ^ 2 = (n * (3 * d ^ 2)) / n := by field_simp [hnz]
      _ < n ^ 2 / n := by exact div_lt_div_of_pos_right h1 hn
      _ = n := by
          rw [pow_two]
          field_simp [hnz]
  · intro h
    -- 3d² < n ⟹ n·(3d²) < n·n = n² ⟹ n < n²/(3d²) (除以 3d² > 0)
    have h1 : n * (3 * d ^ 2) < n ^ 2 := by
      calc
        n * (3 * d ^ 2) < n * n := by exact (mul_lt_mul_left hn).mpr h
        _ = n ^ 2 := by rw [← pow_two]
    have hdenz : 3 * d ^ 2 ≠ 0 := ne_of_gt hden
    calc
      n = (n * (3 * d ^ 2)) / (3 * d ^ 2) := by field_simp [hdenz]
      _ < n ^ 2 / (3 * d ^ 2) := by exact div_lt_div_of_pos_right h1 hden

/-- **注意力 vs CNN 交互数**: 核支持 k < 序列长 n 时,
    注意力交互数 n² > CNN 的 n·k——全局交互 > 局部窗口。 -/
theorem attention_vs_cnn_interactions {n k : ℕ} (hn : 0 < n) (hk : k < n) :
    k * n < n * n := by
  have hkn : (k : ℝ) < (n : ℝ) := by exact_mod_cast hk
  have hn0 : (0 : ℝ) < (n : ℝ) := by exact_mod_cast hn
  have hmul : (k : ℝ) * n < n * n := mul_lt_mul_of_pos_right hkn hn0
  exact_mod_cast hmul

/-- **注意力参数效率实例化**: 序列长度 n 超过 3d² 时,
    注意力每参数交互率 > RNN (每参数交互率: attention n²/(3d²) vs rnn n)。 -/
theorem attention_param_efficiency_beats_rnn (n d : ℝ) (hn : 0 < n) (hd : 0 < d)
    (hlong : 3 * d ^ 2 < n) :
    n ^ 2 / (3 * d ^ 2) > n := by
  exact (attention_more_interactions_per_param n d hn hd).mpr hlong

-- ============================================================
-- §2 每参数信息保留率 (动态)
-- ============================================================

/-- **LSTM 遗忘门保留率上界**: 0 ≤ α ≤ 1 ⟹ α^t ≤ 1——
    门控记忆的信息保留率最多 100% (不可能超过初值)。 -/
theorem forget_gate_retention_upper (α : ℝ) (t : ℕ) (hα0 : 0 ≤ α) (hα1 : α ≤ 1) :
    α ^ t ≤ 1 := by
  exact pow_le_one₀ hα0 hα1

/-- **参数效率对比总定理 (信息保留维度)**:
    同一参数预算 (c0, 每步一个乘数) 下——
    RNN (乘性, 参数 w): 信息 ≤ |w|^t·c0 指数衰减 (上界, 稳定性锁死);
    LSTM (门控, 参数 α): 信息 ≥ α^t·c0 指数保留 (下界, α 可学到 1)。
    门控参数把"保留多少"变成可学习的——参数利用效率更高。 -/
theorem param_retention_compare (w α : ℝ) (g : ℕ → ℝ) (c0 : ℝ)
    (hα0 : 0 ≤ α) (hg : ∀ t : ℕ, 0 ≤ g t) (hc0 : 0 ≤ c0) :
    (∀ t : ℕ, |(fun z : ℝ => w * z)^[t] c0| ≤ |w| ^ t * |c0|) ∧
    (∀ t : ℕ, α ^ t * c0 ≤ ArchCompare.lstmCell α g c0 t) := by
  constructor
  · intro t
    exact ArchCompare.rnn_memory_decay w t c0
  · intro t
    exact ArchCompare.lstm_memory_retention α g c0 hα0 hg hc0 t

/-- **残差参数效率**: 每层残差块用 (1-c) 的比例保底距离
    (不坍缩)——恒等路径是"免费"的参数效率: 不加参数, 但保证
    信息不消失 (对比 RNN 纯乘性: 每层损失 |w| 固定)。 -/
theorem residual_param_retention (f : ℝ → ℝ) (c : ℝ)
    (hcont : ∀ x y : ℝ, |f x - f y| ≤ c * |x - y|) (hc1 : c < 1) (hc0 : 0 ≤ c) :
    ∀ n : ℕ, ∀ x y : ℝ, (1 - c) ^ n * |x - y| ≤
      |(fun z : ℝ => z + f z)^[n] x - (fun z : ℝ => z + f z)^[n] y| := by
  exact ArchCompare.residual_no_collapse_n f c hcont hc1 hc0

/-- **分形参数分配效率**: 收益递减 (Δ_k 严格递减) 时, 把参数预算 B
    集中在前 B 层 (分形组织) 的自由能下降 ≥ 均匀平摊——"每参数的
    边际自由能下降"最大化, 这是参数利用效率的分配维度。 -/
theorem fractal_param_allocation (n B : ℕ) (Δ : ℕ → ℝ)
    (hB : B ≤ n) (hdec : ∀ {k j : ℕ}, k < j → j < n → Δ j < Δ k) :
    (∑ k in range B, Δ k) - (B : ℝ) / n * (∑ k in range n, Δ k) ≥ 0 := by
  exact Fractal.fractal_beats_uniform Δ hB hdec

end Efficiency
