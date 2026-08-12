#!/bin/sh
# Deepen mathlib clone via SSH, find the original v4.21.0-era commit + its dep revs
cd "$(dirname "$0")/.."
log=deepen.log
ML=".lake/packages/mathlib"

git -C "$ML" remote set-url origin git@github.com:leanprover-community/mathlib4.git
echo "== unshallow (blob:none filter for speed) =="
git -C "$ML" fetch --unshallow --filter=blob:none origin 2>&1 | tail -2 >>"$log"
echo "FETCH_EXIT=$?" >>"$log"

# walk back from current HEAD (re-tagged v4.21.0) until we find a commit whose
# lean-toolchain is v4.21.0 AND whose lake-manifest exists with 4.21-era dep revs.
# The re-tagged commit itself has lean-toolchain v4.21.0 but pins 4.34 deps;
# we want the commit where the manifest's batteries rev has lean-toolchain v4.21.0.
echo "== searching history =="
found=""
count=0
for c in $(git -C "$ML" rev-list HEAD 2>/dev/null | head -3000); do
  count=$((count+1))
  tc=$(git -C "$ML" show "$c:lean-toolchain" 2>/dev/null)
  case "$tc" in
    *v4.21.0*)
      # check manifest dep revs for 4.21-era batteries
      mrev=$(git -C "$ML" show "$c:lake-manifest.json" 2>/dev/null | grep -o '"name": "batteries"' | head -1)
      if [ -n "$mrev" ]; then
        found="$c"
        break
      fi
      ;;
  esac
  [ $count -ge 3000 ] && break
done
echo "FOUND=$found (after $count commits)" | tee -a "$log"
if [ -n "$found" ]; then
  git -C "$ML" checkout --detach "$found" >>"$log" 2>&1
  echo "CHECKED_OUT $found" | tee -a "$log"
  echo "toolchain: $(cat "$ML/lean-toolchain")"
  /c/Python314/python -c "
import json
m = json.load(open(r'D:/AI/MATH/lm_principle/.lake/packages/mathlib/lake-manifest.json', encoding='utf-8'))
print('manifest:', m.get('version'))
for p in m.get('packages', []):
    print(' ', p.get('name'), '|', p.get('rev','')[:12], '|', p.get('inputRev',''))
"
fi
echo "DEEPEN_DONE"
