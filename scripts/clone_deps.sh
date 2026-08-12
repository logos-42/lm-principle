#!/bin/sh
# Clone mathlib's dependencies via SSH (https is intermittently blocked)
cd "$(dirname "$0")/.."
mkdir -p .lake/packages
log=clone_deps.log

clone_retry() {
  name=$1; url=$2; branch=$3
  if [ -d ".lake/packages/$name/.git" ]; then
    echo "[$name] already present" | tee -a "$log"
    return 0
  fi
  for i in 1 2 3 4 5; do
    echo "[$name] attempt $i ($branch)" | tee -a "$log"
    if git clone --depth 1 --branch "$branch" "$url" ".lake/packages/$name" >>"$log" 2>&1; then
      echo "[$name] OK" | tee -a "$log"
      return 0
    fi
    rm -rf ".lake/packages/$name"
    sleep $((i * 4))
  done
  echo "[$name] FAILED" | tee -a "$log"
  return 1
}

clone_retry batteries    git@github.com:leanprover-community/batteries.git    main
clone_retry Qq           git@github.com:leanprover-community/quote4.git       master
clone_retry aesop        git@github.com:leanprover-community/aesop.git        master
clone_retry proofwidgets git@github.com:leanprover-community/ProofWidgets4.git main
clone_retry importGraph  git@github.com:leanprover-community/importGraph.git  main
clone_retry LeanSearchClient git@github.com:leanprover-community/LeanSearchClient.git main
clone_retry plausible    git@github.com:leanprover-community/plausible.git    main

echo "=== DEP CLONES DONE ==="
