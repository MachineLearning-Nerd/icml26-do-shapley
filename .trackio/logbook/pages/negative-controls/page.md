# Negative controls


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_566385752216", "created_at": "2026-07-17T04:33:06+00:00", "title": "Negative controls (must fail to match)"}
-->
Falsification is as valuable as verification — both controls are required to *break* exact==brute.

**Control A — sham value function.** If ν is *not* constant on classes (per-subset noise added, violating the do-calculus reduction the method depends on), the r-class collapse is wrong: exact ≠ brute by >1e-3. ✅ detected.

**Control B — drop the empty-set class.** Removing one class (the level-0 / ∅ class) breaks the partition of the 2^d coalitions → exact ≠ brute by >1e-3. ✅ detected. (This was a real bug during development: Algorithm 2's loop ℓ=d..1 generates size-0 children but the paper returns C₀∪…∪C_d, so ∅ must be included as a class.)

Both controls correctly fail to reproduce exact==brute, confirming the result is not an artifact of the implementation agreeing with itself.
