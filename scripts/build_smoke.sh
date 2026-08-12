#!/bin/sh
# Build smoke (import closure) with logging
export PATH="$HOME/.elan/bin:$PATH"
cd "D:/AI/MATH/lm_principle"
lake build LmPrinciple.Smoke > build_smoke.log 2>&1
echo "BUILD_EXIT=$?" >> build_smoke.log
