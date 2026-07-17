# STATUS — Exactly Computing do-Shapley Values (`Peim0KY6ty`)

**Session:** NewPaper. **Last updated:** 2026-07-17. **State:** locally complete; publication queued.

GitHub: `MachineLearning-Nerd/icml26-repro-Peim0KY6ty-do-shapley` (pending push).
HF Space (queued): `DineshAI/Peim0KY6ty`.

## Source audit

- arXiv [2602.07203](https://arxiv.org/abs/2602.07203); OpenReview `Peim0KY6ty`.
- **No official code released** — clean-room implementation directly from the PDF.
- Both claims CPU-feasible at full algorithmic scale; no GPU/training.

## Evidence (locally complete)

- **C1 verified:** exact `r`-class algorithm (Algorithm 2 + Eq. 4) == brute-force
  `2^d`-coalition Shapley across **60 SCMs**, worst error **1.6e-14**;
  efficiency axiom <1e-13. Runtime **linear in `r`** (corr 0.9995), up to
  **73×** faster than brute; solves d=25 where brute (2^25) is infeasible.
  `r` spans `[d, 2^d]` (chain r≈d+1 → all-to-Y r=2^d).
- **C2 verified:** boundary sampler (Algorithm 3) exact at budget `m ≥ r`
  (**≤3.7e-15**), beating a value-function-agnostic baseline by up to
  **15.5 orders of magnitude** at `m = r`; advantage grows monotonically as `m → r`.
- **28/28 pytest tests pass** (claims, lemmas, axioms, 2 negative controls).
- Trackio logbook complete, tagged, pinned, command-captured, secret-scanned.

## Next

- Push to public GitHub `MachineLearning-Nerd/icml26-repro-Peim0KY6ty-do-shapley`.
- Publish `DineshAI/Peim0KY6ty` after the HF daily Space-creation quota resets
  (~23h), verify public tags + artifact bucket, then set `under_verdict`.
