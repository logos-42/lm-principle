#!/bin/sh
# Pin all mathlib deps to the exact revs from mathlib's own lake-manifest.json (v4.21.0 era)
cd "$(dirname "$0")/.."
mkdir -p .lake/packages
log=pin_deps.log

pin() {
  name=$1; sha=$2
  dir=".lake/packages/$name"
  if [ ! -d "$dir/.git" ]; then
    echo "[$name] MISSING — need clone" | tee -a "$log"
    return 1
  fi
  cur=$(git -C "$dir" rev-parse HEAD 2>/dev/null)
  if [ "$cur" = "$sha" ]; then
    echo "[$name] already at $sha" | tee -a "$log"
    return 0
  fi
  echo "[$name] fetching $sha" | tee -a "$log"
  if git -C "$dir" fetch --depth 1 origin "$sha" >>"$log" 2>&1; then
    git -C "$dir" checkout --detach "$sha" >>"$log" 2>&1 && echo "[$name] pinned $sha" | tee -a "$log"
  else
    echo "[$name] fetch FAILED, will re-clone" | tee -a "$log"
    return 1
  fi
}

clone_pin() {
  name=$1; url=$2; sha=$3
  dir=".lake/packages/$name"
  if [ -d "$dir/.git" ] && [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null)" = "$sha" ]; then
    echo "[$name] already at $sha" | tee -a "$log"
    return 0
  fi
  rm -rf "$dir"
  for i in 1 2 3 4 5; do
    echo "[$name] clone attempt $i" | tee -a "$log"
    if git clone "$url" "$dir" >>"$log" 2>&1; then
      git -C "$dir" checkout --detach "$sha" >>"$log" 2>&1 && { echo "[$name] pinned $sha" | tee -a "$log"; return 0; }
      rm -rf "$dir"
    fi
    sleep $((i * 4))
  done
  echo "[$name] FAILED" | tee -a "$log"
  return 1
}

pin  batteries     9a86b38593ce6411eb26cc53e512392e12cd8939
pin  Qq            3b55e9d00c6b0018e5d984eb011b6f93c09bd163
pin  aesop         c1c4362a130f12e632d252180a6c2a31d8fd4726
pin  proofwidgets  99e8adeea3c3cd86b6b79ba01a1383bf2d31d055
pin  LeanSearchClient 2bc7cf064315b26bc38dac2e9612fb581be9b75f
pin  plausible     38e9c3ce15cbb63c92e90bb9a92e4eb82131f669
clone_pin importGraph  git@github.com:leanprover-community/import-graph.git  978b7ec9fbbf9a535114f1de8fe5b3778b358870
clone_pin Cli       git@github.com:leanprover/lean4-cli.git                   af8bc067a4cc6c6df472a68909a3f40b1c76c43e

echo "=== PIN DONE ==="
for d in batteries Qq aesop proofwidgets importGraph LeanSearchClient plausible Cli; do
  echo "[$d] $(git -C .lake/packages/$d rev-parse --short HEAD 2>/dev/null) | $(cat .lake/packages/$d/lean-toolchain 2>/dev/null)"
done
