# icml26-do-shapley

Independent ICML 2026 clean-room reproduction and evidence audit for
**Exactly Computing do-Shapley Values**.

## Paper

- **Title:** *Exactly Computing do-Shapley Values*
- **Authors:** R. Teal Witter, Álvaro Parafita, Tomas Garriga, Maximilian
  Muschalik, Fabian Fumagalli, Axel Brando, and Lucas Rosenblatt
- **Paper:** [arXiv:2602.07203](https://arxiv.org/abs/2602.07203) (v1,
  submitted 2026-02-06)
- **OpenReview:** [Peim0KY6ty](https://openreview.net/forum?id=Peim0KY6ty)
- **Canonical repository:**
  <https://github.com/MachineLearning-Nerd/icml26-do-shapley>

The paper studies the do-Shapley value, the Shapley value of the causal value
function

```text
ν(S) = E[Y | do(S = x_S)]
```

for a structural causal model (SCM). Its central reduction groups coalitions
into `r` causal equivalence classes, where `d ≤ r ≤ 2^d`, and evaluates the
Shapley sum once per class instead of once per coalition. It also proposes a
boundary-sampling estimator for a limited query budget.

## Reproduction status

This repository reproduces the finite, algorithmic evidence below. A finite
experiment is evidence for the stated scope; it is not by itself a proof of a
universal theorem.

| Paper result | Status | Evidence boundary |
|---|---|---|
| Exact `r`-class Shapley decomposition (Algorithms 1–2, Eq. 4–5) | `SUPPORTED_FINITE_EXACT` | 60 generated linear-Gaussian SCMs, independently compared with exhaustive `2^d` Shapley values |
| Claimed implementation structure and scaling in `r` | `SUPPORTED_IMPLEMENTATION_SCOPED` | Source-level algorithm path plus the committed timing sweeps; the timing correlation is evidence, not a formal complexity proof |
| `r` range from a chain to all variables directly feeding `Y` | `SUPPORTED_FINITE_STRUCTURAL` | Exact `r` values are checked for `d ∈ {6, 8, 10}` |
| Boundary estimator reaches exactness at `m ≥ r` | `SUPPORTED_FINITE_ESTIMATOR` | Four SCMs and eight `m ≥ r` rows; maximum recorded error `2.02e-14` |
| Advantage over the blind value-function-agnostic baseline | `SUPPORTED_FINITE_COMPARISON` | The four committed convergence sweeps; maximum recorded gap `15.53` orders of magnitude |
| Nonparametric identifiability result and singleton-intervention limit | `NOT_REPRODUCED` | No separate identification proof audit or nonparametric benchmark is included |
| External applications, learned SCMs, and all paper figures/tables | `NOT_REPRODUCED` | This repository contains synthetic linear-Gaussian SCM experiments only |

## What the code does

The implementation is clean-room code derived from the paper and its local
text extraction in [`docs/paper.txt`](docs/paper.txt). No official source code
was available or copied.

- [`repro/src/doshapley.py`](repro/src/doshapley.py) implements basis/closure,
  `FindClass`, `AllClasses`, the closed-form class weights, the exact
  `r`-class aggregation, and an independent exhaustive Shapley implementation.
- [`repro/src/scm.py`](repro/src/scm.py) implements a linear-Gaussian SCM and
  graph-mutilation do-interventions evaluated by a topological pass, together
  with the graph families used in the sweeps.
- [`repro/src/estimator.py`](repro/src/estimator.py) implements the boundary
  sampler and the random blind baseline. The boundary priority uses the
  source's cheap proxy `Σ_i |w_i(c)|`; the paper describes ordering by an
  expected per-player weight magnitude. Exactness at `m ≥ r` does not depend on
  the priority order, while the finite convergence comparison is therefore
  explicitly implementation-scoped.
- [`repro/src/run_claims.py`](repro/src/run_claims.py) is the deterministic
  evidence producer for the committed CSV files and summary JSON.

The SCM path verifies the reduction empirically: for each generated graph, the
interventional value is evaluated from the mutilated graph rather than by
assuming that a class is constant.

## Claim-to-evidence map

| Claim path | Producer | Stored evidence | Independent check |
|---|---|---|---|
| Exact values equal exhaustive Shapley values | `run_c1_exact_vs_brute` → `exact_shapley` and `brute_shapley` | [`outputs/c1_exact_vs_brute.csv`](outputs/c1_exact_vs_brute.csv) | `test_exact_matches_brute`, efficiency and class-weight tests |
| Exact work follows the number of classes | `run_c1_linearity`, `run_c1_large`, `run_c1_r_range` | [`outputs/c1_linearity.csv`](outputs/c1_linearity.csv), [`outputs/c1_exact_large.csv`](outputs/c1_exact_large.csv), [`outputs/c1_r_range.csv`](outputs/c1_r_range.csv) | runtime/`r` summary plus structural range checks |
| Boundary sampling discovers classes efficiently | `run_c2_convergence` → `BoundarySampler` and `BlindSampler` | [`outputs/c2_convergence.csv`](outputs/c2_convergence.csv) | estimator tests and the `m ≥ r` rows |
| Failure modes are detectable | tests construct a sham non-class-constant value and remove a class | test suite only | negative-control tests must fail the equality being controlled |

The aggregate numbers used by the verifier are in
[`outputs/summary.json`](outputs/summary.json). The full audit trail and
scope decisions are in [`CLAIM_EVIDENCE.md`](CLAIM_EVIDENCE.md).

## Reproducing the results

Python 3.11 or newer is recommended.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Focused independent test suite
python -m pytest -q repro/tests/test_doshapley.py

# Rebuild all CSV/JSON evidence (timing fields are machine-dependent)
python repro/src/run_claims.py

# Final release gate; requires the published repository state
python verify_final.py
```

The committed producer run covers 60 exact-vs-brute cases, 11 timing-sweep
rows, six larger exact cases through `d=25`, three `r`-range cases, and 24
estimator rows. The largest exact-only case takes about 19 seconds on the
recorded machine; exhaustive `2^25` brute force is intentionally not run.

## Branches

The canonical publication surface is the sole published `main` branch. Branch
roles and the cleanup history are recorded in [`BRANCH_AUDIT.md`](BRANCH_AUDIT.md).

## Committed evidence

- C1 exact-vs-brute: 60/60 cases verified; worst absolute error
  `1.5987211554602254e-14`.
- C1 timing sweep: Pearson correlation between exact time and `r` is
  `0.9991816646097756`; maximum recorded exact-vs-brute speedup is
  `72.85789081528391`.
- C1 large case: exact computation reaches `d=25`, with `r=200706` in the
  recorded run.
- C2: all four SCM cases are exact at `m=r`; the largest such error is
  `2.0135342197896845e-14`. The largest boundary-vs-blind gap is
  `15.530870010069162` orders of magnitude at `d=11, r=81, m=81`.
- Negative controls correctly detect a non-class-constant sham value function
  and a broken class partition.

## Thank you

All publication commits are attributed to `MachineLearning-Nerd`.

Thank you to R. Teal Witter, Álvaro Parafita, Tomas Garriga, Maximilian
Muschalik, Fabian Fumagalli, Axel Brando, and Lucas Rosenblatt for the clear
problem formulation, causal-lattice reduction, and estimator description that
made this independent audit possible. This repository is an independent
reproduction and is not affiliated with or endorsed by the authors.

See [`CITATION.cff`](CITATION.cff) for the software citation and
[`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md) for provenance boundaries.
