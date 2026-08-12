/-
# CNN 的数学第一性原理

卷积不是"滑窗", 而是**群代数中的乘法**:

1. 定义域 ℤ 上有限支撑函数 f, g 的卷积 = AddMonoidAlgebra ℝ ℤ 中的乘法
   (f ⋆ g)(n) = Σ_k f(k)·g(n-k);
2. **平移等变性**是乘法的结合律: 平移算子 τ_a 是乘以单项式 X^a,
   于是 τ_a (f ⋆ g) = (τ_a f) ⋆ g = f ⋆ (τ_a g) —— 不需要任何分析, 纯代数恒等式;
3. 在交换群 ℤ 上左右平移一致 (单项式是中心元).

这就是"CNN 为什么共享权重还能识别平移目标"的数学根因.
-/
import Mathlib.Algebra.MonoidAlgebra.Basic

noncomputable section
open scoped BigOperators

namespace CNN

/-- 卷积代数: 定义在 ℤ 上的群代数 (乘法即卷积) -/
abbrev Conv (R : Type*) [Semiring R] := AddMonoidAlgebra R ℤ

/-- 左平移: τ_a f := X^a · f -/
def translate (a : ℤ) {R : Type*} [Semiring R] (f : Conv R) : Conv R :=
  AddMonoidAlgebra.single a (1 : R) * f

/-- 右平移: f ↦ f · X^a -/
def translateR (a : ℤ) {R : Type*} [Semiring R] (f : Conv R) : Conv R :=
  f * AddMonoidAlgebra.single a (1 : R)

/-- **平移等变性 (左)**: τ_a (f ⋆ g) = (τ_a f) ⋆ g —— 纯结合律 -/
theorem translate_mul (a : ℤ) {R : Type*} [Semiring R] (f g : Conv R) :
    translate a (f * g) = translate a f * g := by
  unfold translate
  rw [mul_assoc]

/-- **平移等变性 (右)**: τ_a (f ⋆ g) = f ⋆ (τ_a g) —— 纯结合律 -/
theorem mul_translateR (a : ℤ) {R : Type*} [Semiring R] (f g : Conv R) :
    translateR a (f * g) = f * translateR a g := by
  unfold translateR
  rw [mul_assoc]

/-- 在交换群 ℤ 上, 左右平移等价 (X^a 是中心元) -/
theorem translate_eq_translateR (a : ℤ) {R : Type*} [CommSemiring R] (f : Conv R) :
    translate a f = translateR a f := by
  unfold translate translateR
  rw [mul_comm]

/-- 脉冲响应: 单点核卷积 = 平移 (X^a ⋆ g)(n) = r·g(n-a) -/
theorem single_mul_apply {R : Type*} [Semiring R] (a : ℤ) (r : R) (g : Conv R) (n : ℤ) :
    (AddMonoidAlgebra.single a r * g) n = r * g (n - a) := by
  rw [AddMonoidAlgebra.single_mul_apply]
  apply congrArg (fun z : ℤ => r * g z)
  omega

/- TODO(下次): 一般卷积逐点公式 (f ⋆ g)(n) = Σ_{k ∈ supp f} f(k)·g(n-k)
   需要 Finsupp 双层和展开 (mul_def + sum_apply), 非第一性原理必需 -/

end CNN
