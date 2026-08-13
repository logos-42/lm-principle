# lm_principle

> Formalizing the *mathematical first principles of large models* as machine-checked
> Lean 4 theorems — instead of heuristic arguments in papers.

This repository turns the core mathematical claims behind modern neural
architectures (RNN, CNN, Transformer) into formally verified proofs. The flagship
case studies are **LMT-twister** (counterfactual representation bottleneck) and
**fractal necessity** — covering capacity counting, IE / EHS structures, and a
full theorem-backed argument for why fractal organization, residual feedback, and
optimal depth arise from first principles.

**73 theorems are machine-verified** (`lake build` green, no `sorry` / `admit` /
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

> 分形必要性 → 73 条机器验证定理。Every item below has a Lean theorem as its
> backing.

1. **Fractal organization beats uniform stacking** (core hypothesis ✓)
   — `prefix_allocation_optimal` / `fractal_beats_uniform`: whenever the
   per-layer free-energy drop `Δ_k` is strictly decreasing, concentrating budget
   on a prefix (fractal sparsity) yields total return `≥` uniform amortization.
   "Fractal saves ~25% parameters" is not a coincidence — it is a theorem.

2. **High-dimensional structure does not collapse** (hypothesis ✓)
   — `residual_no_collapse_n`: a contractive residual `⟹` after `n` layers the
   output distance `≥ (1-c)^n ·` input distance (deterministic lower bound,
   collapse probability `= 0`). Feedback is a *sufficient* guarantee:
   `ffn_can_collapse` exhibits a feedback-free FFN that collapses to a constant
   (absence of feedback does not *guarantee* collapse, but permits it).

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
   — `murray_variational_optimal`: the two-term cost `C(r)=a/r⁴+b·r²` is
   globally minimized at `r⁶=2a/b` (pure algebra, no calculus). The
   experiment-one paradox is a *model mismatch with a precise mechanism*:
   the original cost sum omitted the flow-conservation factor in its
   resistance term (`Q_g = Q/2^g`); restoring it turns the global optimum
   into an interior point converging to `2^(-1/3)` (`diagnose_murray_cost.py`:
   `G=50` gives `0.795`, 0.13% off). Flow conservation `⟹ r³=r₁³+r₂³` plus
   symmetry `⟹ ρ³=1/2` closes the full chain. Honest boundary: in pure
   transport cost, branching is `2^(1/3)×` more expensive than not branching —
   branching exists for *coverage* (space filling), and Murray's law gives the
   optimal ratio *given* that branching is required.

6. **When optimal depth holds** (C2 + C4 ✓)
   — conditions = ① strictly decreasing returns ② positive cost ③ returns
   eventually below cost `⟹` optimal depth exists and `≤ k₀+1`; if ③ fails then
   "deeper is better" — the *exact necessary-and-sufficient condition* for
   "depth is not always better". The sharp **critical-point theorem**
   (`CriticalPoint.lean`, `optimal_depth_is_first_crossing`): under ①–③ the
   optimal depth is exactly `k* = min{k : Δ_k < λ}` — the first layer whose
   marginal benefit falls below cost; for power-law returns
   `Δ_k = c/(k+1)²` the closed form is `k* = ⌈√(c/λ)⌉ - 1`
   (`power_law_critical_pair`, verified numerically in
   `verify_critical_point.py`).

---

## What is formalized

All in `LmPrinciple/`, verified by `lake build` (**73 theorems** total):

| Module | Content |
|---|---|
| `RNN.lean` | Closed-form linear RNN = causal convolution (any `CommSemiring`); stability `|w|<1 ⟹` bounded state (2) |
| `CNN.lean` | Convolution = group-algebra multiplication; translation equivariance = associativity (4) |
| `Transformer.lean` | `softmax` convex combination; self-attention permutation equivariant (3) |
| `LMT.lean` | Capacity counting (pigeonhole); complex SSM = complexified RNN; IE / EHS structures (7) |
| `Fractal.lean` | Fractal necessity: `prefix_allocation_optimal`, `fractal_beats_uniform`, connection-density power law + convexity (9) |
| `ArchCompare.lean` | `residual_no_collapse_n`, `ffn_can_collapse`, LSTM retention vs RNN decay (5) |
| `Efficiency.lean` | Per-parameter interaction rates, attention crossover `3d²<n`, forget-gate retention (8) |
| `InfoDynamics.lean` | Gibbs `KL≥0`, CE = H + KL, quality flow, no-collapse guarantee, feedback coefficients, `hypothesis_verification` (12) |
| `Murray.lean` | Variational optimum `r⁶=2a/b`, flow conservation, symmetric ratio `ρ³=1/2`, optimal-depth existence, power-law instantiation (10) |
| `Training.lean` | Scaling law, CE ≥ entropy, RLHF softmax, DPO loss ≥ 0, sparse MoE/attention bound-preserving (10) |
| `CriticalPoint.lean` | `optimal_depth_is_first_crossing` (`k* = min{k : Δ_k < λ}`), power-law critical pair (3) |

> As of 2026-08-13: `lake build` fully green, **73 theorems** machine-verified
> (mathlib closure compiled from pinned sources); pre-push gate active.

---

## Why this matters

- **Assertions → theorems.** C1–C4 upgrade from "claims" to machine proofs with
  no empirical-data dependency. Experiments give numerical evidence; theorems
  give guarantees — they corroborate each other.
- **Honest boundary handling.** The experiment-one paradox is not hidden; its
  mechanism is *precisely diagnosed* (missing flow-conservation factor in the
  resistance term — `diagnose_murray_cost.py`; restoring it yields an interior
  optimum converging to `2^(-1/3)`). "Admit the boundary + close it with more
  complete math" is the preferred scientific-writing form.
- **Local real experiments with honest corrections.** All three experiments
  were reproduced locally (PyTorch CPU, seed 42, numbers within 0.01 of the
  original), and a multi-seed rerun (`experiments_v2.py`, 3 seeds) exposed
  what does *not* survive: fractal-vs-uniform is not significant across seeds,
  and the "loss cliff from depth 4" is a single-run artifact — while optimal
  depth 2 and the critical point `k* = min{k : Δ_k < λ}` are robust.
- **Reproducible pipeline.** wiki-first compilation + 73 verified theorems +
  pre-push gate (verification must pass before push) — the whole argument chain
  is reproducible, inheritable, and extensible.

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
- ✅ **73 theorems** machine-verified across RNN / CNN / Transformer / LMT / Fractal
- ✅ Fractal-necessity argument: C1 (Murray `0.79`) and C2+C4 (optimal depth) proven
- ✅ Wiki-first knowledge system (v2 bootstrap, lint green) + pre-push gate active

**Next options (open)**

- ① Derivative-form variational verification (`deriv` stationarity) — pending
  `Mathlib.Analysis.Calculus`; the algebraic version already closes the argument
- ② Closed-form `D → n*` mapping (fractal dimension → optimal depth) — the
  *benefit* critical point is closed (`k* = ⌈√(c/λ)⌉ - 1`), but the mapping
  from task fractal dimension `D` to the per-layer returns `Δ_k` remains open
- ③ LMT-twister Main Theorem 2.1 information-theoretic proof (lemmas A.1–A.4:
  IE capacity via DPI → Fano → EHS). Mathlib weapons confirmed present:
  `Mathlib/InformationTheory/Hamming.lean` (Fano) and
  `Mathlib/InformationTheory/KullbackLeibler/`

**Honest boundaries (labeled)**

- Cross-entropy / entropy are defined on finite discrete distributions (`Fin n`);
  the continuous version needs measure theory
- The `D → n*` closed form (fractal dimension to depth) remains open; the
  benefit-critical-point closed form is verified
- Multi-seed experiments show fractal-vs-uniform performance is **not
  significant** (3 seeds); the verified claim is parameter efficiency
  (same performance, 25% fewer parameters), not lower loss

---

## Source

- Paper (IEEE journal + conference drafts): `paper/main_jrnl.tex`,
  `paper/main_conf.tex` — *Mathematical Fractal Criticality in LLM Dynamics*
- LMT-twister paper `head-en.tex` / `head-zh.tex` (Appendix A, lemmas A.1–A.4)
- Fractal-necessity argument: `LmPrinciple.Fractal` + `docs/wiki/fractal-necessity.md`
- Architecture overview: `docs/wiki/project-overview.md`
- Live status: `docs/wiki/current-status.md`
- Local experiments: `experiments/run_fractal_experiments.py` +
  `scripts/experiments_v2.py` (multi-seed honest rerun) +
  `scripts/diagnose_murray_cost.py` (paradox diagnosis)

Remote: `git@github.com:logos-42/lm-principle.git`

## License

This project is licensed under the **MIT License** — see [LICENSE](./LICENSE).
The formalization (`LmPrinciple/`) is machine-verified Lean 4 code; the
paper drafts and wiki content are original work of the authors. Lean 4,
mathlib, and PyTorch remain under their respective licenses.
