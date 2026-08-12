#!/bin/sh
# Pin mathlib to the ORIGINAL v4.21.0 commit (308445d, 2025-06-30) and
# all deps to the revs in ITS lake-manifest.json (4.21-era, NOT master tip)
cd "$(dirname "$0")/.."
log=pin_v421.log

ML=.lake/packages/mathlib
git -C "$ML" checkout --detach 308445d7985027f538e281e18df29ca16ede2ba3 >>"$log" 2>&1
echo "[mathlib] pinned $(git -C "$ML" rev-parse --short HEAD) | $(cat "$ML/lean-toolchain")" | tee -a "$log"

pin() {
  name=$1; sha=$2
  dir=".lake/packages/$name"
  cur=$(git -C "$dir" rev-parse HEAD 2>/dev/null)
  if [ "$cur" = "$sha" ]; then
    echo "[$name] already at $sha" | tee -a "$log"
    return 0
  fi
  echo "[$name] fetching $sha" | tee -a "$log"
  if git -C "$dir" fetch --depth 1 origin "$sha" >>"$log" 2>&1 && git -C "$dir" checkout --detach "$sha" >>"$log" 2>&1; then
    echo "[$name] pinned $sha" | tee -a "$log"
  else
    echo "[$name] FETCH FAILED" | tee -a "$log"
  fi
}

pin plausible         c4aa78186d388e50a436e8362b947bae125a2933
pin LeanSearchClient  6c62474116f525d2814f0157bb468bf3a4f9f120
pin importGraph       d07bd64f1910f1cc5e4cc87b6b9c590080e7a457
pin proofwidgets      6980f6ca164de593cb77cd03d8eac549cc444156
pin aesop             8ff27701d003456fd59f13a9212431239d902aef
pin Qq                e9c65db4823976353cd0bb03199a172719efbeb7
pin batteries         8d2067bf518731a70a255d4a61b5c103922c772e
pin Cli               7c6aef5f75a43ebbba763b44d535175a1b04c9e0

echo "=== FINAL STATE ==="
for d in mathlib batteries Qq aesop proofwidgets importGraph LeanSearchClient plausible Cli; do
  echo "[$d] $(git -C .lake/packages/$d rev-parse --short HEAD 2>/dev/null) | $(cat .lake/packages/$d/lean-toolchain 2>/dev/null)"
done
echo "PIN421_DONE"
