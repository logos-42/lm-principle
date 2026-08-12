/-
# LmPrinciple — 大模型的数学第一性原理 (Lean 4 形式化)

项目: D:\AI\MATH\lm_principle
目标: 用 Lean 4 + mathlib 形式化大模型架构的数学第一性原理,
       并以 LMT-twister (反事实表示瓶颈) 为核心案例。

模块:
- LmPrinciple.RNN        — 线性 RNN: 闭式解 = 因果卷积; 稳定性 |w|<1
- LmPrinciple.CNN        — 卷积 = 群代数乘法; 平移等变性 = 结合律
- LmPrinciple.Transformer— softmax 凸组合; 自注意力置换等变
- LmPrinciple.LMT        — 容量计数 (pigeonhole); 复 SSM = RNN; IE/EHS 结构
-/
import LmPrinciple.RNN
import LmPrinciple.CNN
import LmPrinciple.Transformer
import LmPrinciple.LMT
import LmPrinciple.Fractal
import LmPrinciple.ArchCompare
import LmPrinciple.Efficiency
import LmPrinciple.InfoDynamics
import LmPrinciple.Murray
