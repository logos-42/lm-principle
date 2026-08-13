"""诊断 1: 树级成本函数的公式缺陷

shape.md 实验一原公式 (compute_energy_cost):
  resistance  = sum(2^g / r_g^4)   r_g = rho^g
  maintenance = sum(2^g * r_g^2)
缺陷: 阻力项漏了流量因子. 对称树第 g 代每根血管流量 Q_g = Q/2^g,
正确阻力成本每根 ∝ Q_g^2 / r_g^4, 总量 = aQ^2 * sum((2*rho^4)^(-g)).
原公式把 2^g 留在分子 (2/rho^4)^g, 导致阻力随 g 爆炸, 最优被推到 rho->1 边界.

本脚本验证:
A. 原公式 argmin 在边界 (0.9 < 0.79, 最优 ~rho->1)
B. 修正公式 argmin 为内点, 且随代数 G 增大收敛到 2^(-1/3) ~= 0.7937
C. 修正公式的最优对系数比 c = b/(aQ^2) 的依赖 (G 有限时), G->inf 时不依赖
"""
import numpy as np

def original_cost(rho, G=10, c=1.0):
    """shape.md 原公式: resistance + maintenance (无流量因子)"""
    resistance = sum(1.0 / (rho ** (4 * g) + 1e-8) * 2 ** g for g in range(G + 1))
    maintenance = sum(rho ** (2 * g) * 2 ** g for g in range(G + 1))
    return resistance, maintenance, resistance + maintenance

def corrected_cost(rho, G=10, c=1.0):
    """修正公式: 阻力带流量守恒 Q_g = Q/2^g (吸收 aQ^2, c = b/(aQ^2)):
    C(rho) = sum_{g=0}^{G} (2 rho^4)^(-g) + c * sum_{g=0}^{G} (2 rho^2)^g
    """
    resistance = sum((2 * rho ** 4) ** (-g) for g in range(G + 1))
    maintenance = c * sum((2 * rho ** 2) ** g for g in range(G + 1))
    return resistance, maintenance, resistance + maintenance

rho0 = 2 ** (-1 / 3)
print("=== A. 原公式 (shape.md): 缺陷复现 ===")
for r in [0.5, 0.79, 0.9, 0.98]:
    res, maint, tot = original_cost(r)
    print(f"  rho={r}: res={res:.3e} maint={maint:.3e} total={tot:.3e}")
grid = np.arange(0.4, 0.995, 0.005)
best = min(((original_cost(r)[2], r) for r in grid), key=lambda x: x[0])
print(f"  原公式 argmin = {best[1]:.3f} (在扫描边界) — 0.79 不是最优, 与文章结论矛盾")

print("\n=== B. 修正公式 (带流量守恒): 内点最优 + 收敛到 2^(-1/3) ===")
print(f"  理论极限 rho* = 4^(-1/6) = {rho0:.6f}")
for G in [2, 5, 10, 20, 50]:
    best = min(((corrected_cost(r, G)[2], r) for r in grid), key=lambda x: x[0])
    print(f"  G={G:3d}: argmin = {best[1]:.6f}  偏差 = {abs(best[1]-rho0)*100:.3f}%")
print("  → 随代数 G 增大, 最优收敛到 0.7937 — 0.79 被守恒律锁定 (树级公式的精确形式)")

print("\n=== C. 系数比 c = b/(aQ^2) 的依赖 ===")
for c in [0.1, 1.0, 10.0]:
    row = []
    for G in [5, 10, 20, 50]:
        best = min(((corrected_cost(r, G, c)[2], r) for r in grid), key=lambda x: x[0])
        row.append(f"G={G}:{best[1]:.4f}")
    print(f"  c={c:5}: " + "  ".join(row))
print("  → G->inf 时与 c 无关 (因为 (aQ^2/b)^(1/G) -> 1); 有限 G 有 O(1/G) 修正")
