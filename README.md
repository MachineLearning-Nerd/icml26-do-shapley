# Exactly Computing do-Shapley Values — ICML 2026 Reproduction

Reproduction of **Á. Parafita et al., "Exactly Computing do-Shapley Values"**
(arXiv [2602.07203](https://arxiv.org/abs/2602.07203), ICML 2026,
OpenReview [`Peim0KY6ty`](https://openreview.net/forum?id=Peim0KY6ty)).

The paper shows that **do-Shapley values** — the Shapley value of the
interventional value function `ν(S) = E[Y | do(S = x_S)]` of a Structural
Causal Model — can be computed **exactly in time linear in the number `r` of
irreducible sets** of the SCM, instead of the naive `O(2^d)`. The key idea is a
reformulation of Shapley's `2^d`-term sum into a sum over `r` equivalence
classes (the *irreducible sets* / *closed sets* of the causal lattice), where
`d ≤ r ≤ 2^d`.

## Claims reproduced

| # | Claim (paraphrased) | Status |
|---|---|---|
| **C1** | do-Shapley values can be **exactly computed in time linear in `r`** (Prop. 3.2: `O(r(d+e+T))`), not `2^d`. | ✅ Verified |
| **C2** | As the query budget `m → r`, the boundary-sampling estimator reaches **machine-precision exactness**, beating value-function-agnostic estimators **by orders of magnitude**. | ✅ Verified |

## Method (clean-room, from the PDF — no official code is released)

* `repro/src/doshapley.py` — Definitions 2.1/2.2 (basis, closure), **Algorithm 1
  FindClass**, **Algorithm 2 AllClasses** (descend the closed-set lattice via
  Lemma 3.1), **Equation 4** (`ϕ_i = Σ_j ν(c_j)·w_i(c_j)` with the closed-form
  weights of Eq. 5), and an independent **brute-force Shapley over all `2^d`
  coalitions** as ground truth.
* `repro/src/scm.py` — a linear-Gaussian SCM with a *faithful* do-intervention
  `ν(S) = E[Y | do(S=0)]` computed by graph mutilation + topological
  propagation, plus DAG generators that sweep `r` from `~d+1` (chain) to `2^d`
  (all-variables-directly-to-`Y`).
* `repro/src/estimator.py` — the **boundary sampler** (Algorithm 3) and a
  value-function-agnostic **blind baseline**.
* `repro/src/run_claims.py` — evidence orchestrator → `outputs/`.
* `repro/tests/test_doshapley.py` — 28 pytest tests (claims, lemmas, controls).

## How to run

```bash
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install numpy scipy pytest
python -m pytest repro/tests/test_doshapley.py -q     # 28 tests, <1s
python repro/src/run_claims.py                         # writes outputs/*.csv, summary.json
```

## Headline results (full scale, CPU)

**C1 — exact == brute, machine precision, linear in `r`.**
Across **60 SCMs** (d∈{6..10}, densities, seeds) the exact `r`-class algorithm
matches exhaustive `2^d`-coalition Shapley with **worst error 1.6e-14**
(efficiency axiom `Σϕ_i = ν([d])−ν(∅)` to <1e-13). Exact runtime vs `r`:
**Pearson correlation 0.9995** (genuinely linear), while brute force scales as
`2^d` (up to **73×** slower at equal `d`). The exact algorithm solves `d=25`
(`r`≈ thousands) in ~19s, where brute force (`2^25`≈33M coalitions) is
infeasible. `r` verified to span `[d, 2^d]`.

**C2 — estimator: exact at `m=r`, orders of magnitude over the blind baseline.**
The boundary sampler recovers **every** class at budget `m ≥ r` → Shapley values
to **machine precision (≤3.7e-15)**. Against a value-function-agnostic (random
coalition) baseline at the same budget, the gap reaches **15.5 orders of
magnitude** at `m = r`, with the advantage growing monotonically as `m → r`.

## Independent verification & negative controls

* Two code paths agree: closed-form class weights (Eq. 5) vs direct enumeration
  over class members — identical (≤4e-16).
* Shapley axioms checked independently: efficiency, symmetry.
* **Control A (sham value function):** if `ν` is *not* constant on classes
  (violating the do-calculus reduction the method depends on), exact ≠ brute
  (correctly detected).
* **Control B (drop the empty-set class):** removing one class breaks the
  partition → exact ≠ brute (correctly detected; this was a real dev bug).

## Scope & cost

| | This reproduction | Full replication |
|---|---|---|
| Scope | Both claims, full algorithmic scale (`d` to 25; `r` to thousands; `2^d` to 262k brute) | same |
| Hardware | 4 vCPU / GTX 1050 (CPU only) | any CPU |
| Time | ~2 min (tests <1s) | — |
| Cost | $0 | — |
| Outcome | Both claims verified at machine precision | — |

Trackio logbook: `DineshAI/Peim0KY6ty` (publish queued behind HF daily Space quota).
