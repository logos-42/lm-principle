"""验证幂律临界点定理 (CriticalPoint.power_law_critical_pair) 的数值实例:
Δ_k = c/(k+1)^2, kstar = min{k : Δ_k < λ} 满足 Δ_kstar < λ ≤ Δ_kstar-1,
且闭式 kstar = ceil(sqrt(c/λ)) - 1 (c/λ 非平方时) 或 = sqrt(c/λ) (平方时)。

同时验证 general α 的闭式: kstar = ceil((c/λ)^(1/α)) - 1 (非整数时)。
"""
import math


def find_kstar(c, lam, alpha=2.0):
    """枚举: 第一个 Δ_k < λ 的 k"""
    k = 0
    while True:
        if c / (k + 1) ** alpha < lam:
            return k
        k += 1


def closed_form_kstar(c, lam, alpha=2.0):
    """闭式: min{k : (k+1)^alpha > c/lam}"""
    x = (c / lam) ** (1.0 / alpha)   # x = 临界 (k+1) 值
    # k+1 > x 的最小整数 k+1 = ceil(x)（x 整数时 = x+1? 不: k+1 > x 严格, x=m 整数时 k+1 ≥ m+1 ⟹ k ≥ m）
    if abs(x - round(x)) < 1e-9:
        return int(round(x))          # x 是整数 m: kstar = m
    return math.ceil(x) - 1           # 非整数: kstar = ceil(x) - 1


print("=== 幂律临界点: 枚举 vs 闭式公式 ===")
ok = True
for c, lam in [(1, 0.1), (1, 0.5), (2, 0.3), (0.5, 0.05), (3, 1.0), (10, 0.01), (1, 1.0), (4, 1.0)]:
    k_enum = find_kstar(c, lam)
    k_form = closed_form_kstar(c, lam)
    dk = c / (k_enum + 1) ** 2
    dk_prev = c / k_enum ** 2 if k_enum > 0 else float('inf')
    crit_pair = (dk < lam) and (k_enum == 0 or lam <= dk_prev)
    match = (k_enum == k_form)
    ok = ok and match and crit_pair
    print(f"  c={c:4}, λ={lam:5}: kstar={k_enum:3d} (闭式 {k_form:3d} {'✓' if match else '✗'})  "
          f"Δ_kstar={dk:.5f} < λ={lam} ≤ Δ_prev={dk_prev if k_enum else '—'}: 临界对{'✓' if crit_pair else '✗'}")

print("\n=== 一般 α 的闭式 (验证 α = 1, 1.5, 3) ===")
for alpha in [1.0, 1.5, 3.0]:
    ok2 = True
    for c, lam in [(1, 0.1), (2, 0.05), (5, 0.5)]:
        k_enum = find_kstar(c, lam, alpha)
        k_form = closed_form_kstar(c, lam, alpha)
        ok2 = ok2 and (k_enum == k_form)
    print(f"  α={alpha}: 闭式 {'✓ 全部一致' if ok2 else '✗ 不一致'}")

print(f"\n总体: {'全部通过 ✓' if ok else '存在不一致 ✗'}")