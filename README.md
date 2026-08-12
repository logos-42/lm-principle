# lm_principle

> Formalizing the *mathematical first principles of large models* as machine-checked
> Lean 4 theorems — instead of heuristic arguments in papers.

This repository turns the core mathematical claims behind modern neural
architectures (RNN, CNN, Transformer) into formally verified proofs. The flagship
case studies are **LMT-twister** (counterfactual representation bottleneck) and
**fractal necessity** — covering capacity counting, IE / EHS structures, and a
full theorem-backed argument for why fractal organization, residual feedback, and
optimal depth arise from first principles.

**60 theorems are machine-verified** (`lake build` green, no `sorry` / `admit` /
`axiom`), guarded by a **pre-push gate** (verification must pass before any push).

中文文档（Chinese documentation）：[README.zh.md](./README.zh.md)

---

## Why it exists

Neural architectures are usually justified by intuition or empirical curves.
This project insists on something stronger: a claim is accepted only when
`lake build` is green and the proof contains **no `sorry`, no `admit`, no `axiom`**.

The four architectural first principles (formalized in `LmPrinciple/`):

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

On top of these, the **fractal-necessity** track upgrades a set of intuitive
claims (fractal saves parameters, high-dimensional representations don't
collapse, optimal depth is finite, Murray's law `0.79` is physically locked) from
assertions into unconditional, data-independent machine proofs.

---

## Verified conclusions (each backed by a Lean theorem)

> 分形必要性 → 60 条机器验证定理。Every item below has a Lean theorem as its
> backing.

1. **Fractal organization beats uniform stacking** (core hypothesis ✓)
   — `prefix_allocation_optimal` / `fractal_beats_uniform`: whenever the
   per-layer free-energy drop `Δ_k` is strictly decreasing, concentrating budget
   on a prefix (fractal sparsity) yields total return `≥` uniform amortization.
   "Fractal saves ~25% parameters" is not a coincidence — it is a theorem.

2. **High-dimensional structure does not collapse** (hypothesis ✓)
   — `residual_no_collapse_n`: a contractive residual `⟹` after `n` layers the
   output distance `≥ (1-c)^n ·` input distance (deterministic lower bound,
   collapse probability `= 0`); `ffn_can_collapse`: a feedback-free FFN admits an
   implementation that collapses to a constant — feedback (identity / gated path)
   is *necessary* to prevent collapse.

3. **Information-flow efficiency** (hypothesis ✓)
   — RNN multiplicative memory decays `≤ |w|^t` while LSTM gated memory is
   retained `≥ α^t` (with learnable `α → 1`): gating is more parameter-efficient;
   attention's per-parameter interaction rate `n²/(3d²)` overtakes RNN when
   `3d² < n` — economies of scale for long sequences.

4. **Free-energy minimization depends on a specific information structure**
   (hypothesis ✓)
   — Gibbs inequality `KL ≥ 0` (variational free energy non-negative) and
   cross-entropy `= entropy + KL ≥ entropy`; `hypothesis_verification` assembles
   all structural theorems: the required structure = ① identity / gated feedback
   (anti-collapse + retention) ② convex combination (bounded error) ③ prefix
   parameter concentration (fractal allocation) ④ cross-entropy lower bound.

5. **Murray's law `0.79` — full derivation** (C1 ✓)
   — `murray_variational_optimal`: the three-term cost `C(r)=a/r⁴+b·r²` is
   globally minimized at `r⁶=2a/b` (pure algebra, no calculus) — this *explains*
   the experiment-one paradox: `0.79` is the variational optimum of three costs;
   a simplified model (missing the work term) naturally fails. Flow conservation
   `⟹ r³=r₁³+r₂³` plus symmetry `⟹ ρ³=1/2` closes the full chain.

6. **When optimal depth holds** (C2 + C4 ✓)
   — conditions = ① strictly decreasing returns ② positive cost ③ returns
   eventually below cost `⟹` optimal depth exists and `≤ k₀+1`; if ③ fails then
   "deeper is better" — this is the *exact necessary-and-sufficient condition* for
   "depth is not always better". Power-law returns `Δ_k = c/(k+1)²` satisfy the
   conditions `⟹` a finite optimal depth exists (C4 instantiated).

---

## What is formalized

All in `LmPrinciple/`, verified by `lake build` (60 theorems total):

| Module | Content |
|---|---|
| `LmPrinciple/RNN.lean` | Closed-form linear RNN = causal convolution (any `CommSemiring`); stability `|w|<1 ⟹` bounded state |
| `LmPrinciple/CNN.lean` | Convolution = group-algebra multiplication; translation equivariance = associativity |
| `LmPrinciple/Transformer.lean` | `softmax` convex combination; self-attention permutation equivariant |
| `LmPrinciple/LMT.lean` | Capacity counting (pigeonhole); complex SSM = complexified RNN; IE / EHS structures |
| `LmPrinciple.Fractal` | Fractal necessity: `prefix_allocation_optimal`, `residual_no_collapse_n`, `ffn_can_collapse`, `murray_variational_optimal`, optimal-depth conditions, `hypothesis_verification` |

> As of 2026-08-12: `lake build` fully green, **60 theorems** machine-verified
> (mathlib closure compiled from 1758 module sources); pre-push gate active.

---

## Why this matters

- **Assertions → theorems.** C1–C4 upgrade from "claims" to machine proofs with
  no empirical-data dependency. Experiments give numerical evidence; theorems
  give guarantees — they corroborate each other.
- **Honest boundary handling.** The experiment-one paradox is not hidden; it is
  *precisely explained* by the variational theorem (simplified model missing the
  work term ⟹ `0.79` fails; three-cost model ⟹ global optimum). "Admit the
  boundary + close it with more complete math" is the preferred scientific-writing
  form.
- **Reproducible pipeline.** wiki-first compilation + 54→60 verified theorems +
  pre-push gate (verification must pass before push) — the whole argument chain is
  reproducible, inheritable, and extensible.

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
├── scripts/              # Wiki lint/compile + environment bootstrap + pre-push gate
├── manifests/            # Raw-source registry (raw_sources.csv)
├── lakefile.toml         # Local (offline) mathlib pin
├── lean-toolchain        # leanprover/lean4:v4.21.0
├── README.md
└── README.zh.md
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

mathlib and its 8 dependencies are pinned via local `path` requires
(`lakefile.toml`), so no network is needed at build time:

```bash
lake build              # real lake binary; see scripts/run_build.sh on Windows
lake build LmPrinciple  # build just the formalization
```

To set up a fresh environment, see `scripts/setup_mathlib.sh` (Windows-oriented)
and `docs/wiki/current-status.md` → "Environment setup" section.

> ⚠️ Do not bump `lean-toolchain` to `v4.34.0-rc1` — Batteries syntax is
> incompatible and the build breaks.

---

## Wiki system (wiki-first) and the pre-push gate

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

A **pre-push gate** ensures `lake build` is green (no `sorry` / `admit` /
`axiom`) before any push — verification is a hard prerequisite, not a suggestion.

---

## Status & roadmap

**Done**

- ✅ Lean 4.21.0 + mathlib v4.21.0 environment, fully offline-pinned
- ✅ **60 theorems** machine-verified across RNN / CNN / Transformer / LMT / Fractal
- ✅ Fractal-necessity argument: C1 (Murray `0.79`) and C2+C4 (optimal depth) proven
- ✅ Wiki-first knowledge system (v2 bootstrap, lint green) + pre-push gate active

**Next options (open)**

- ① Derivative-form variational verification (`deriv` stationarity) — pending
  `Mathlib.Analysis.Calculus`; the algebraic version already closes the argument
- ② Closed-form `D → n*` mapping (fractal dimension → optimal depth) — current
  theorems give *existence*, not a closed formula (open problem)
- ③ LMT-twister Main Theorem 2.1 information-theoretic proof (lemmas A.1–A.4:
  IE capacity via DPI → Fano → EHS). Mathlib weapons confirmed present:
  `Mathlib/InformationTheory/Hamming.lean` (Fano) and
  `Mathlib/InformationTheory/KullbackLeibler/`

**Honest boundaries (labeled)**

- Cross-entropy / entropy are defined on finite discrete distributions (`Fin n`);
  the continuous version needs measure theory
- C2's `D → n*` closed form remains open

---

## Source

- LMT-twister paper `head-en.tex` / `head-zh.tex` (Appendix A, lemmas A.1–A.4)
- Fractal-necessity argument: `LmPrinciple.Fractal` + `docs/wiki/fractal-necessity.md`
- Architecture overview: `docs/wiki/project-overview.md`
- Live status: `docs/wiki/current-status.md`

Remote: `git@github.com:logos-42/lm-principle.git`
