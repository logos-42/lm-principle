import Mathlib.Data.Real.Basic
import Mathlib.Data.Complex.Basic
import Mathlib.Data.Nat.Log
import Mathlib.Data.Fintype.Card
import Mathlib.Algebra.MonoidAlgebra.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.BigOperators.Intervals
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Data.Fin.Embedding

-- Smoke test: compiles the import closure so incremental builds are fast.
#check Finset.sum_range_succ
#check Finset.sum_range_reflect
#check Finset.mul_sum
#check Finset.abs_sum_le_sum_abs
#check Equiv.sum_comp
#check Real.exp_pos
#check Fintype.card_le_of_injective
#check Nat.log2
#check AddMonoidAlgebra.single_mul_single
#check Fin.pos_iff_nonempty
