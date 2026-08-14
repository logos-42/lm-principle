#!/bin/sh
# 推送门禁: lake build 全绿 + 无 sorry/admit/axiom + 定理计数
# 用法: sh scripts/verify_all.sh   (在 repo 根目录)
cd "$(dirname "$0")/.." || exit 1
export MATHLIB_NO_CACHE_ON_UPDATE=1
echo "=== 全量构建 ==="
lake build LmPrinciple 2>&1 | tail -2 || { echo "FAIL: lake build 失败"; exit 1; }
echo "=== sorry/admit/axiom 检查 ==="
FILES="RNN CNN Transformer LMT Fractal ArchCompare Efficiency InfoDynamics Murray Training CriticalPoint Hopfield"
if grep -rn "sorry\|admit\|axiom" $(echo "$FILES" | sed 's/\([^ ]*\)/LmPrinciple\/\1.lean/g'); then
  echo "FAIL: 有未证明漏洞"
  exit 1
else
  echo "PASS: 无 sorry/admit/axiom"
fi
echo "=== 定理统计 ==="
TOTAL=0
for f in $FILES; do
  c=$(grep -c '^theorem' "LmPrinciple/$f.lean")
  echo "$f: $c 条"
  TOTAL=$((TOTAL + c))
done
echo "TOTAL: $TOTAL 条"
[ "$TOTAL" -ge 79 ] && echo "RESULT: ALL-PASS" && exit 0 || { echo "RESULT: 定理数异常"; exit 1; }
