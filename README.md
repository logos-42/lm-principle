# lm_principle

> Formalizing the *mathematical first principles of large models* as machine-checked
> Lean 4 theorems — instead of heuristic arguments in papers.

This repository turns the core mathematical claims behind modern neural
architectures (RNN, CNN, Transformer) into formally verified proofs. The flagship
case study is **LMT-twister** — the *counterfactual representation bottleneck* —
covering capacity counting and the IE / EHS model structures.

中文文档（Chinese documentation）：[README.zh.md](./README.zh.md)

---

## Why it exists

Neural architectures are usually justified by intuition or empirical curves.
This project insists on something stronger: a claim is accepted only when
`lake build` is green and the proof contains **no `sorry`, no `admit`, no `axiom`**.

Core claims (**first principles**):

1. **RNN = causal convolution** — a linear recurrence expands to
   `h(n+1) = Σ w^(n-k) x(k)`, sharing the group-algebra structure of a CNN.
2. **CNN = group-algebra multiplication** — translation equivariance *is* the
   associative law of multiplication; no analysis required.
3. **Transformer attention = convex combination** — `softmax` normalization
   implies the output lies inside the convex hull; permutation equivariance
   implies positional information must be injected externally.
4. **Capacity = counting** — `R` bits hold at most `2^R` states; distinguishing
   `V` actions needs `≥ log₂V` bits. This is the discrete skeleton of the
   LMT-twister Main Theorem 2.1.

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

> As of 2026-08-12: `lake build` is fully green, all 16 theorems machine-verified
> (mathlib closure compiled from 1758 module sources).

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
and `docs/wiki/current-status.md` → "Environment setup" section.

> ⚠️ Do not bump `lean-toolchain` to `v4.34.0-rc1` — Batteries syntax is
> incompatible and the build breaks.

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
