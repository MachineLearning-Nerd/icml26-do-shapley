# Claim-to-evidence audit

This file separates what the repository directly checks from what remains
outside its finite, clean-room scope.

## C1 — exact computation through causal classes

### Paper claim

For an SCM whose coalitions reduce to `r` irreducible classes, the do-Shapley
sum can be evaluated from one value per class with the class weights in Eq. 5,
using the `r`-class construction in Algorithms 1–2 and Eq. 4. The paper gives
the implementation-level complexity `O(r(d+e+T))`.

### Repository path

1. `repro/src/scm.py:LinearSCM.value` performs a graph-mutilation
   intervention and topological propagation.
2. `repro/src/doshapley.py:find_class` computes the basis and closure.
3. `repro/src/doshapley.py:all_classes` descends the closed-set lattice and
   de-duplicates closures.
4. `repro/src/doshapley.py:class_weight_i` evaluates the Eq. 5 weights.
5. `repro/src/doshapley.py:exact_shapley` aggregates one value per class.
6. `repro/src/doshapley.py:brute_shapley` independently enumerates all
   `2^d` coalitions for the finite ground truth.
7. `repro/src/run_claims.py:run_c1_exact_vs_brute` records the 60 comparisons;
   the timing functions record the scaling and large-case sweeps.

### Stored evidence

- `outputs/c1_exact_vs_brute.csv`: 60 data rows, all `verified=True`.
- `outputs/c1_linearity.csv`: 11 data rows comparing exact and brute timing.
- `outputs/c1_exact_large.csv`: six exact-only rows for `d=20..25`.
- `outputs/c1_r_range.csv`: three chain/all-to-`Y` structural checks.
- `outputs/summary.json`: aggregate metrics consumed by `verify_final.py`.
- `repro/tests/test_doshapley.py`: exact-vs-brute, efficiency, symmetry,
  partition, closed-form-weight, and `FindClass` tests.

### Result and boundary

The 60 finite comparisons have worst absolute error
`1.5987211554602254e-14`. The recorded timing correlation between exact time
and `r` is `0.9991816646097756`, and the largest exact-vs-brute speedup is
`72.85789081528391`. These support the implementation and finite suite; they
do not replace a formal proof of the paper's asymptotic bound.

## C2 — boundary-sampling estimator

### Paper claim

Algorithm 3 explores the boundary of the causal lattice and can recover the
class-weighted Shapley estimate under a query budget, becoming exact once all
`r` classes have been queried. The paper contrasts this with value-function-
agnostic sampling.

### Repository path

- `repro/src/estimator.py:BoundarySampler` canonicalizes each query to a
  closure, queues lattice neighbours, and aggregates known classes.
- `repro/src/estimator.py:BlindSampler` provides the random-coalition baseline
  with basis caching.
- `repro/src/run_claims.py:run_c2_convergence` runs four SCM cases across
  budgets from below `r` through `2r`.

The implementation's queue priority is `Σ_i |w_i(c)|`, a cheap monotone proxy
for the paper's expected per-player weight priority. Therefore the finite
convergence and comparison numbers are reported as implementation-scoped
evidence. At `m ≥ r`, priority affects order but not eventual class coverage.

### Stored evidence

`outputs/c2_convergence.csv` contains 24 rows for:

| `d` | `r` | rows |
|---:|---:|---:|
| 12 | 107 | 6 |
| 14 | 668 | 6 |
| 13 | 1913 | 6 |
| 11 | 81 | 6 |

The eight rows with `m ≥ r` have `boundary_distinct == r`; their maximum
boundary error is `2.0135342197896845e-14`. The largest boundary-vs-blind gap
is `15.530870010069162` orders of magnitude at `d=11, r=81, m=81`.

## Controls

- A sham value function deliberately violates class constancy; the exact
  class-reduced result must disagree with the independent brute result.
- Removing the empty-set class breaks the partition; the exact result must
  disagree with brute force.
- Direct enumeration of class members independently verifies the closed-form
  class weights.

These controls test the reproduction's assumptions and failure detection; they
are not additional paper claims.

## Outside scope

The following are intentionally `NOT_REPRODUCED`:

- the paper's nonparametric identifiability theorem and singleton-intervention
  limitation;
- universal asymptotic theorem proofs beyond the source implementation;
- learned or nonlinear SCMs, external datasets, application studies, and all
  paper figures/tables not represented by the committed synthetic sweeps.
