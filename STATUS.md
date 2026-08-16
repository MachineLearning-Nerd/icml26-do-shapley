# Status — icml26-do-shapley

**Paper:** *Exactly Computing do-Shapley Values*
**Authors:** R. Teal Witter, Álvaro Parafita, Tomas Garriga, Maximilian
Muschalik, Fabian Fumagalli, Axel Brando, and Lucas Rosenblatt
**Sources:** [arXiv:2602.07203](https://arxiv.org/abs/2602.07203) ·
[OpenReview Peim0KY6ty](https://openreview.net/forum?id=Peim0KY6ty)
**Repository:** <https://github.com/MachineLearning-Nerd/icml26-do-shapley>

## Release status

The scoped clean-room reproduction, documentation, and evidence bundle are
complete. The final release gate is mechanical: `verify_final.py` checks the
canonical `main` branch, commit attribution, repository name, committed
metrics, and the focused test suite from a fresh clone.

## Verified in scope

- Exact `r`-class aggregation agrees with exhaustive `2^d` Shapley values on
  60 generated linear-Gaussian SCMs.
- The maximum C1 absolute error is `1.5987211554602254e-14`; all 60 rows are
  marked verified in the committed output.
- The exact implementation reaches `d=25` and the recorded timing sweep has
  exact-time/`r` correlation `0.9991816646097756`.
- The boundary sampler is exact at `m ≥ r` for four SCM cases, with maximum
  recorded error `2.0135342197896845e-14` on those rows.
- The largest committed boundary-vs-blind gap is `15.530870010069162` orders
  of magnitude at `d=11, r=81, m=81`.
- The test suite contains 28 focused tests, including efficiency, symmetry,
  class-weight, exact-vs-brute, estimator, and negative-control checks.

## Not reproduced

- The paper's universal complexity and estimator guarantees are not claimed
  as experimentally proved; the repository supplies implementation evidence
  and finite checks only.
- The nonparametric identifiability theorem and singleton-intervention limit
  are not independently audited here.
- External datasets, learned/nonlinear SCMs, applications, and complete paper
  figures/tables are outside this repository's scope.

## Provenance

No official implementation was available for this clean-room reproduction.
The code is derived from the paper and the local paper-text artifact listed in
[`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md). The exact claim boundaries and
producer-to-output paths are recorded in [`CLAIM_EVIDENCE.md`](CLAIM_EVIDENCE.md).
