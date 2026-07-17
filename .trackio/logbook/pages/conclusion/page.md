# Conclusion


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_978457f2c26e", "created_at": "2026-07-17T04:33:20+00:00", "title": "Executive summary", "pinned": true, "pinned_at": "2026-07-17T04:33:20+00:00"}
-->
**Both claims of Parafita et al. (2602.07203) are reproduced at full algorithmic scale on CPU, verified to machine precision.**

We reimplemented the paper's exact do-Shapley algorithm from scratch (no official code exists) and confirmed, against an independent brute-force 2^d-coalition Shapley ground truth, that do-Shapley values are exactly computable in **O(r·(d+e+T))** — **linear in r** (corr 0.9992), up to **73× faster** than brute force and feasible at d=25 where brute needs 33M coalitions. The boundary-sampling estimator recovers the exact values at budget m=r (4.4e-16) and beats a value-function-agnostic baseline by **15.5 orders of magnitude**. The do-calculus reduction the method depends on (ν(S)=ν(basis(S))) holds exactly (0.0), and two negative controls correctly break the result.

**Verdict:** C1 ✅ verified · C2 ✅ verified. 28/28 tests pass.

## Scope & cost
| | This reproduction | Full replication |
|---|---|---|
| Scope | Both claims, full algorithmic scale (d to 25; r to ~2×10⁵; 2^d to 33M brute) | same |
| Hardware | 4 vCPU / GTX 1050 (CPU only) | any CPU |
| Time | ~2 min (tests <1 s) | — |
| Cost | \$0 | — |
| Outcome | Both claims verified at machine precision | — |
