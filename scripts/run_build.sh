#!/bin/sh
# Build with the REAL lake binary (bypass elan shim + default-toolchain issues)
# Project toolchain: leanprover/lean4:v4.21.0 (see lean-toolchain)
cd "$(dirname "$0")/.."
LAKE="$HOME/.elan/toolchains/leanprover--lean4---v4.21.0/bin/lake.exe"
echo "LAKE=$LAKE"
"$LAKE" build "$@" > build.log 2>&1
echo "BUILD_EXIT=$?" >> build.log
