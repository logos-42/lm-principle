#!/bin/sh
# lm_principle mathlib setup — run from repo root
# Workaround: curl schannel revocation check fails (CRYPT_E_REVOCATION_OFFLINE) on this Windows box.
set -e
cd "$(dirname "$0")/.."

# curl wrapper dir first in PATH so lake/elan use it
mkdir -p .lake/bin
cat > .lake/bin/curl <<'EOF'
#!/bin/sh
exec /mingw64/bin/curl --ssl-no-revoke "$@"
EOF
chmod +x .lake/bin/curl

export PATH="$HOME/.elan/bin:$PWD/.lake/bin:$PATH"
echo "leanprover/lean4:v4.21.0" > lean-toolchain

echo "== lean =="
lean --version

echo "== lake update =="
lake update mathlib 2>&1 | tail -3

echo "== cache get =="
lake exe cache get 2>&1 | tail -3

echo "== verify =="
ls .lake/packages/mathlib/Mathlib/InformationTheory 2>/dev/null | head -5 || echo "no info theory dir yet"
echo "SETUP_DONE"
