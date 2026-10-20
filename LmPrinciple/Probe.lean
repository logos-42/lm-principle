import Mathlib.Data.Fintype.Card
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Fintype.Pigeonhole
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Positivity

example (k : ℕ) : Fintype.card (Fin k → Bool) = 2 ^ k := by
  simp

structure Foo (w p i o : Type*) [Fintype w] [Fintype p] [Fintype i] [Fintype o] where
  perception : w → p
  cognition : p → i
  expression : i → o

example {w p i o : Type*} [Fintype w] [Fintype p] [Fintype i] [Fintype o]
    (C : Foo w p i o) :
    Function.Injective C.perception → True := by trivial


example {k j : ℕ} (h : k < j) :
    Fintype.card (Fin k → Bool) < Fintype.card (Fin j → Bool) := by
  simp only [Fintype.card_fun, Fintype.card_bool, Fintype.card_fin]
  exact Nat.pow_lt_pow_right (by norm_num : (2 : ℕ) > 1) h

-- 单射 -> 基数不等
example {α β : Type} [Fintype α] [Fintype β] (f : α → β) (hf : Function.Injective f) :
    Fintype.card α ≤ Fintype.card β := by
  exact Fintype.card_le_of_injective f hf

-- Fin V 嵌入 Fin W (V ≤ W)
example {V W : ℕ} (h : V ≤ W) (f : Fin V → Fin W) (hf : Function.Injective f) :
    Fintype.card (Fin V) ≤ Fintype.card (Fin W) := by
  exact Fintype.card_le_of_injective f hf
