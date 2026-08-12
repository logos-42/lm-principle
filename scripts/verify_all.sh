#!/bin/sh
cd "D:/AI/MATH/lm_principle"
export MATHLIB_NO_CACHE_ON_UPDATE=1
LAKE="$HOME/.elan/toolchains/leanprover--lean4---v4.21.0/bin/lake.exe"
echo "=== 全量构建 ==="
"$LAKE" build LmPrinciple 2>&1 | tail -2
echo "=== sorry/admit/axiom 检查 ==="
if grep -rn "sorry\|admit\|axiom" LmPrinciple/RNN.lean LmPrinciple/CNN.lean LmPrinciple/Transformer.lean LmPrinciple/LMT.lean LmPrinciple/Fractal.lean; then
  echo "FAIL: 有未证明漏洞"
else
  echo "PASS: 无 sorry/admit/axiom"
fi
echo "=== 定理统计 ==="
for f in RNN CNN Transformer LMT Fractal; do
  echo "$f: $(grep -c '^theorem' LmPrinciple/$f.lean) 条"
done
echo "TOTAL: $(grep -h '^theorem' LmPrinciple/RNN.lean LmPrinciple/CNN.lean LmPrinciple/Transformer.lean LmPrinciple/LMT.lean LmPrinciple/Fractal.lean | wc -l) 条"
