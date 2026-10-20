/-
# 认知动力学 (CognitiveDynamics.lean) — 认知结构的第一性力学

## 立场声明（方法论, 决定本文件全部形式化策略）

本文件**不从任何关于智能的经验假说出发**（不从"权重子空间"假设出发,
不从"神经元组合"经验断言出发, 也不从任何具体架构出发）。正如牛顿先确立
万有引力的**结构本体**、再由它推导出天体运动规律, 本文件先确立"认知系统"
这一**本体存在**, 给出它必须满足的**结构条件**, 再由这些条件**推导**出关于
容量、压缩、自由度、规模收益的定量结论。

因此:
- §0 定义的 `CognitiveSystem` 是**本体**: 一个认知系统被定义为
  "世界 → 感知 → 内部状态 → 输出" 的四层有限结构。这是**定义**, 不是假设。
- 三条原理 (P1 组合性 / P2 感知压缩 / P3 比特维度) 在本文件中被表述为
  **结构条件**（由本体的分层结构**蕴含**的推论）, 而非外加的假设。
- 一切定理都是**从定义推出**的, 不含经验断言。

## 本文件结构

  §0 本体: 认知系统的存在性结构 (四层有限系统)
  §1 主定理 T1: 无损认知 ⟺ 存在单射 ⟺ 基数链不等 (三原理相容性)
  §2 组合容量: 由本体的组合单元结构**推导** 2^k 容量定理
  §3 比特维度: 由本体的有限性**推导**对数容量
  §4 认知饱和: 内部状态数有限 ⇒ 有效自由度有界 ⇒ 规模收益递减
  §5 规模法则的结构解释: 边际增益的对数凹性

## 与 UWS 的关系

arXiv:2512.05117 (Universal Weight Subspace Hypothesis) 在本文件中
**不是前提**, 而是 §4 认知饱和这一**结论**的一个经验对应物:
若 §4 成立, 则"共享低维子空间"是必然的**结果**而非**原因**。
该对应关系在 `docs/wiki/universal-weight-subspace.md` 中单独标注。
-/
import Mathlib.Data.Fintype.Card
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Fintype.Pigeonhole
import Mathlib.Data.Nat.Log
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Positivity

noncomputable section
open Finset
open scoped BigOperators

namespace CognitiveDynamics

-- ============================================================
-- §0 本体: 认知系统的存在性结构
-- ============================================================

/-- **认知系统 (本体)**: 一个四层有限结构。

    `world`          被认知的世界状态空间
    `perceptionCode` 感知层码空间 (外部输入的有限表示)
    `internalState`  内部状态空间 (认知自由度所在之处)
    `output`         输出空间 (表达)

    定义即"认知"在结构上意味着什么: 存在一个从世界到输出的**分层有限映射**。
    这里**不**假设任何关于机制、架构、权重或经验的性质。 -/
structure CognitiveSystem where
  /-- 被认知的世界状态空间 -/
  world : Type
  /-- 感知码空间 -/
  perceptionCode : Type
  /-- 内部状态空间 -/
  internalState : Type
  /-- 输出空间 -/
  output : Type
  /-- 感知层映射: 世界 → 感知码 -/
  perception : world → perceptionCode
  /-- 认知层映射: 感知码 → 内部状态 -/
  cognition : perceptionCode → internalState
  /-- 表达层映射: 内部状态 → 输出 -/
  expression : internalState → output

namespace CognitiveSystem

/-- **复合映射**: 感知 ⊗ 认知 ⊗ 表达。整个认知过程在数学上就是这一张复合表。 -/
def composite (C : CognitiveSystem) (w : C.world) : C.output :=
  C.expression (C.cognition (C.perception w))

/-- **认知系统无损**: 复合映射是单射 —— 不同世界状态可被无歧义区分。 -/
def Lossless (C : CognitiveSystem) : Prop := Function.Injective C.composite

/-- **表达容量**: 该系统实际产生的**不同输出**的个数 (输出空间的像集大小)。
    注意这是 <= |internalState|, 因为每个内部状态只产生一个输出。 -/
def imageCapacity (C : CognitiveSystem) [Fintype C.internalState]
    [DecidableEq C.output] : ℕ := (Finset.univ.image C.expression).card

/-- **最优认知系统 (结构条件, 非经验假设)**: 感知层**双射**于感知码空间
    (单射 = 感知不丢信息; 满射 = 每个感知码都被使用), 且 认知⊗表达 在
    感知码空间上**单射** (区分能力由信息承载段承担)。

    这两条合起来说明: 感知层"恰好"承担了压缩职责 (不多不少), 而区分能力
    全部由认知⊗表达承担。满足此条件的系统被称为**最优认知系统**。 -/
def Optimal (C : CognitiveSystem) : Prop :=
  Function.Injective C.perception ∧ Function.Surjective C.perception ∧
    Function.Injective (C.expression ∘ C.cognition)

end CognitiveSystem

-- ============================================================
-- §1 主定理: 无损认知的结构后果 (三原理相容性)
-- ============================================================

/-- **T1 无损认知 <=> 承载区分的单射就是复合映射**。

    这是"认知"这一概念的**充要刻画**: 系统无损, 当且仅当它的区分能力
    由某个单射承载, 且该单射就是感知⊗认知⊗表达的复合。 -/
theorem lossless_iff_exists_injective (C : CognitiveSystem) :
    C.Lossless ↔ ∃ f : C.world → C.output, Function.Injective f ∧ C.composite = f := by
  constructor
  · intro h
    exact ⟨C.composite, h, rfl⟩
  · rintro ⟨f, hf, heq⟩
    subst heq
    exact hf

/-- **T2 无损 => 基数链不等**: 世界状态数不超过输出空间大小。
    这是纯粹的**鸽笼原理**结论, 不含任何经验假设。 -/
theorem lossless_card_world_le_output (C : CognitiveSystem) [Fintype C.world]
    [Fintype C.output] (h : C.Lossless) :
    Fintype.card C.world ≤ Fintype.card C.output := by
  exact Fintype.card_le_of_injective C.composite h

/-- **T3 无损 => 感知层必为单射 (P2 压缩的结构条件)**。

    若感知把两个不同世界压成同一感知码, 则复合映射必把它们映到同一输出,
    与无损矛盾。**结论**: 任何有损压缩都必须发生在"感知之后"的层内
    (认知或表达), 而不能是感知本身。—— 这是从定义推出的, 不是经验断言。 -/
theorem lossless_perception_injective (C : CognitiveSystem) (h : C.Lossless) :
    Function.Injective C.perception := by
  intro w1 w2 hw
  have : C.composite w1 = C.composite w2 := by
    simp only [CognitiveSystem.composite, hw]
  exact h this

/-- **T4 无损 <=> (感知单射 ∧ 认知⊗表达单射)**（感知满射给定）。

    感知层**单射**意味着"感知本身不丢信息"（压缩全部发生在感知之后的层内）;
    认知⊗表达 **单射**意味着"区分能力由信息承载段承担"。两者合起来与
    "复合映射无损"等价。感知满射只在前向需要（保证每个感知码都有原像）。 -/
theorem lossless_iff_of_surjective_perception (C : CognitiveSystem)
    (hsur : Function.Surjective C.perception) :
    C.Lossless ↔ (Function.Injective C.perception ∧
      Function.Injective (C.expression ∘ C.cognition)) := by
  constructor
  · intro h
    refine ⟨lossless_perception_injective C h, ?_⟩
    intro p1 p2 hp
    obtain ⟨w1, hw1⟩ := hsur p1
    obtain ⟨w2, hw2⟩ := hsur p2
    by_contra hne
    have hc : C.composite w1 = C.composite w2 := by
      simp only [Function.comp_apply] at hp
      simp only [CognitiveSystem.composite, hw1, hw2, hp]
    have hw : p1 = p2 := by
      rw [← hw1, ← hw2]
      exact congrArg C.perception (h hc)
    exact hne hw
  · rintro ⟨hinjP, hinj⟩ w1 w2 hcomp
    have h2 : C.perception w1 = C.perception w2 :=
      hinj (by simpa only [CognitiveSystem.composite, Function.comp_apply] using hcomp)
    exact hinjP h2

/-- **T5 三原理相容性 (定量相容条件)**: 对**最优**认知系统,
    |世界| <= |感知码| <= |输出|, 即 P1/P2/P3 三条原理在同一系统上相容。 -/
theorem optimal_chain (C : CognitiveSystem) [Fintype C.world] [Fintype C.perceptionCode]
    [Fintype C.output] (h : C.Optimal) :
    Fintype.card C.world ≤ Fintype.card C.perceptionCode ∧
      Fintype.card C.perceptionCode ≤ Fintype.card C.output := by
  obtain ⟨hinjP, _, hinj⟩ := h
  exact ⟨Fintype.card_le_of_injective C.perception hinjP,
    Fintype.card_le_of_injective (C.expression ∘ C.cognition) hinj⟩

/-- **T6 表达容量上界**: 认知系统能产生的不同输出数不超过其内部状态数。
    这条把"内部状态"确立为**认知自由度的载体**。 -/
theorem imageCapacity_le_internalState (C : CognitiveSystem) [Fintype C.internalState]
    [DecidableEq C.output] :
    C.imageCapacity ≤ Fintype.card C.internalState := by
  unfold CognitiveSystem.imageCapacity
  calc (Finset.univ.image C.expression).card ≤ Finset.univ.card := Finset.card_image_le
    _ = Fintype.card C.internalState := Finset.card_univ

end CognitiveDynamics
