# lm_principle

> Formalizing the *mathematical first principles of large models* as machine-checked
> Lean 4 theorems — instead of heuristic arguments in papers.
>
> 用 **Lean 4 + mathlib** 把"大模型的数学第一性原理"写成可机器验证的定理，
> 而不是论文里的启发式论证。

This repository turns the core mathematical claims behind modern neural
architectures (RNN, CNN, Transformer) into formally verified proofs. The flagship
case study is **LMT-twister** — the *counterfactual representation bottleneck* —
covering capacity counting and the IE / EHS model structures.

---

## Why it exists

Neural architectures are usually justified by intuition or empirical curves.
This project insists on something stronger: a claim is accepted only when
`lake build` is green and the proof contains **no `sorry`, no `admit`, no `axiom`**.

核心主张（**第一性原理 / first principles**）：

1. **RNN = causal convolution** — a linear recurrence expands to
   `h(n+1) = Σ w^(n-k) x(k)`, sharing the group-algebra structure of a CNN.
   *线性递归展开后 h(n+1) = Σ wⁿ⁻ᵏ x(k)，与 CNN 共享群代数结构。*
2. **CNN = group-algebra multiplication** — translation equivariance *is* the
   associative law of multiplication; no analysis required.
   *平移等变性是乘法的结合律，不需要分析。*
3. **Transformer attention = convex combination** — `softmax` normalization
   implies the output lies inside the convex hull; permutation equivariance
   implies positional information must be injected externally.
   *softmax 归一 ⟹ 输出在凸包内；置换等变 ⟹ 位置信息必须外部注入。*
4. **Capacity = counting** — `R` bits hold at most `2^R` states; distinguishing
   `V` actions needs `≥ log₂V` bits. This is the discrete skeleton of the
   LMT-twister Main Theorem 2.1.
   *容量 = 计数：R 比特最多 2^R 个状态，区分 V 个动作需 ≥ log₂V 比特。*

---

## What is formalized

All proven in `LmPrinciple/` and verified by `lake build`:

| Module | Content |
|---|---|
| `LmPrinciple/RNN.lean` | Closed-form linear RNN = causal convolution (over any `CommSemiring`); stability `|w|<1 ⟹` bounded state `≤ M/(1-|w|)` |
| `LmPrinciple/CNN.lean` | Convolution = group-algebra multiplication (`AddMonoidAlgebra ℝ ℤ`); translation equivariance = associativity; impulse-response formula |
| `LmPrinciple/Transformer.lean` | `softmax` weights positive + normalized (convex combination); self-attention permutation equivariant |
| `LmPrinciple/LMT.lean` | Capacity counting (pigeonhole); complex SSM = complexified RNN; IE / EHS model structures (paper eq. 1/2) |
| `LmPrinciple.Fractal` | Fractal necessity (from `docs/wiki/shape.md`) |

> 截至 2026-08-12：`lake build` 全绿，16 条定理全部机器验证
> （mathlib 闭包 1758 模块源码编译）。

---

## Repository layout

```
lm_principle/
├── LmPrinciple/          # Lean 4 formalization (the verified layer)
│   ├── Basic.lean
│   ├── RNN.lean
│   ├── CNN.lean
│   ├── Transformer.lean
│   ├── LMT.lean
│   └── Fractal.lean
├── docs/wiki/            # Wiki-knowledge system (LLM Wiki v2 schema)
│   ├── index.md
│   ├── project-overview.md
│   ├── current-status.md
│   └── SCHEMA.md
├── scripts/              # Wiki lint/compile + environment bootstrap
├── manifests/            # Raw-source registry (raw_sources.csv)
├── lakefile.toml         # Local (offline) mathlib pin
├── lean-toolchain        # leanprover/lean4:v4.21.0
└── README.md
```

Knowledge is layered as **raw → wiki → code**:

- **raw** — original sources (registered in `manifests/raw_sources.csv`)
- **wiki** — compiled current consensus (`docs/wiki/`, v2 schema)
- **code** — the executable verification layer (`LmPrinciple/`)

> 只改代码不回写 wiki，算没做完。*Changing code without writing back to the
> wiki is considered unfinished.*

---

## Building

Requirements:

- [elan](https://github.com/leanprover/elan) with Lean **4.21.0**
- mathlib **v4.21.0** (rev `308445d`, 2025-06-30)

This repo pins mathlib and its 8 dependencies via **local `path` requires**
(`lakefile.toml`), so no network access is needed at build time. After cloning:

```bash
lake build            # real lake binary; see scripts/run_build.sh on Windows
lake build LmPrinciple  # build just the formalization
```

To set up a fresh environment, see `scripts/setup_mathlib.sh` (Windows-oriented)
and `docs/wiki/current-status.md` → "环境搭建流程".

> ⚠️ Do not bump `lean-toolchain` to `v4.34.0-rc1` — Batteries syntax is
> incompatible and the build breaks. *lean-toolchain 别改回 v4.34.0-rc1。*

---

## Wiki system (wiki-first)

Conclusions are written back into `docs/wiki/` using the **LLM Wiki v2 schema**
(see `docs/wiki/SCHEMA.md`). Lint and compile scripts live in `scripts/`:

```bash
python3 scripts/wiki_lint.py --strict=v2   # schema check
python3 scripts/wiki_check.py              # integrity check
python3 scripts/delta_compile.py --write-drafts
```

Raw files (PDF, Excel, images, archives, …) must be registered before use:

```bash
python3 scripts/ingest_raw.py              # register new raw sources
python3 scripts/untracked_raw_check.py     # find unregistered raw
```

> 凡是提到、收到、引用、保存的任何非代码文件 → 第一件事查
> `manifests/raw_sources.csv`。*Any non-code file must be registered in the
> manifest before use.*

---

## Status & roadmap

**Done**

- ✅ Lean 4.21.0 + mathlib v4.21.0 environment, fully offline-pinned
- ✅ 16 theorems machine-verified across RNN / CNN / Transformer / LMT
- ✅ Wiki-first knowledge system (v2 bootstrap, lint green)

**TODO**

- ⏳ LMT-twister Main Theorem 2.1 information-theoretic proof (lemmas A.1–A.4:
  IE capacity via DPI → Fano → EHS). Mathlib weapons confirmed present:
  `Mathlib/InformationTheory/Hamming.lean` (Fano) and
  `Mathlib/InformationTheory/KullbackLeibler/`.
- ⏳ General pointwise convolution formula `(f⋆g)(n) = Σ f(k)g(n-k)`
- ⏳ On-demand `.olean` caching to replace full source compilation

---

## Source

- LMT-twister paper `head-en.tex` / `head-zh.tex` (Appendix A, lemmas A.1–A.4)
- Architecture overview: `docs/wiki/project-overview.md`
- Live status: `docs/wiki/current-status.md`

Remote: `git@github.com:logos-42/lm-principle.git`
