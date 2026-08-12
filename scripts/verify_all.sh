#!/bin/sh
cd "D:/AI/MATH/lm_principle"
export MATHLIB_NO_CACHE_ON_UPDATE=1
LAKE="$HOME/.elan/toolchains/leanprover--lean4---v4.21.0/bin/lake.exe"
echo "=== 全量构建 ==="
"$LAKE" build LmPrinciple 2>&1 | tail -2
echo "=== sorry/admit/axiom 检查 ==="
if grep -rn "sorry\|admit\|axiom" LmPrinciple/RNN.lean LmPrinciple/CNN.lean LmPrinciple/Transformer.lean LmPrinciple/LMT.lean LmPrinciple/Fractal.lean LmPrinciple/ArchCompare.lean LmPrinciple/Efficiency.lean LmPrinciple/InfoDynamics.lean; then
  echo "FAIL: 有未证明漏洞"
  exit 1
else
  echo "PASS: 无 sorry/admit/axiom"
fi
echo "=== 定理统计 ==="
for f in RNN CNN Transformer LMT Fractal ArchCompare Efficiency InfoDynamics; do
  echo "$f: $(grep -c '^theorem' LmPrinciple/$f.lean) 条"
done
TOTAL=$(grep -h '^theorem' LmPrinciple/RNN.lean LmPrinciple/CNN.lean LmPrinciple/Transformer.lean LmPrinciple/LMT.lean LmPrinciple/Fractal.lean LmPrinciple/ArchCompare.lean LmPrinciple/Efficiency.lean LmPrinciple/InfoDynamics.lean | wc -l)
echo "TOTAL: $TOTAL 条"
[ "$TOTAL" -ge 45 ] && echo "RESULT: ALL-PASS" && exit 0 || echo "RESULT: 定理数异常" && exit 1
