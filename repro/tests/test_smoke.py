"""Smoke test: validate the core do-Shapley machinery before building evidence."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
from doshapley import (find_class, all_classes, exact_shapley, brute_shapley,
                       is_irreducible, is_closed)
from scm import make_random_scm, make_chain_scm, make_complete_bipartite_to_y


def maxdiff(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


def test_reduction_nu_eq_basis():
    """nu(S) == nu(basis(S)) for all S (do-calculus rule 3 reduction)."""
    d = 7
    for seed in range(5):
        scm = make_random_scm(d, edge_prob=0.4, seed=seed)
        worst = 0.0
        for mask in range(1 << d):
            S = frozenset(j for j in range(d) if mask & (1 << j))
            basis, closure = find_class(set(S), {k: set(v) for k, v in scm.parents.items()}, d)
            worst = max(worst, abs(scm.value(S) - scm.value(frozenset(basis))))
        assert worst < 1e-12, (seed, worst)
        print(f"  seed {seed}: max|nu(S)-nu(basis(S))| = {worst:.2e}")


def test_exact_eq_brute():
    """Exact r-class algorithm == brute-force 2^d Shapley, machine precision."""
    d = 8
    parents_as = lambda scm: {k: set(v) for k, v in scm.parents.items()}
    for seed in range(6):
        scm = make_random_scm(d, edge_prob=0.45, seed=seed)
        phi_ex, info = exact_shapley(scm.value, parents_as(scm), d)
        phi_br = brute_shapley(scm.value, d)
        md = maxdiff(phi_ex, phi_br)
        assert md < 1e-10, (seed, md, info["r"])
        # Shapley efficiency axiom: sum phi_i = nu([d]) - nu(empty)
        eff = abs(sum(phi_ex) - (scm.value(frozenset(range(d))) - scm.value(frozenset())))
        assert eff < 1e-10, (seed, eff)
        print(f"  seed {seed}: r={info['r']:>3}, |exact-brute|={md:.2e}, efficiency err={eff:.2e}")


def test_r_bounds():
    """r in [d, 2^d]: chain within range; all-to-Y => 2^d (every subset irreducible)."""
    d = 6
    chain = make_chain_scm(d, seed=1)
    rc = len(all_classes({k: set(v) for k, v in chain.parents.items()}, d))
    assert d <= rc <= (1 << d), (rc, d)
    comp = make_complete_bipartite_to_y(d, seed=1)
    rk = len(all_classes({k: set(v) for k, v in comp.parents.items()}, d))
    assert rk == (1 << d), (rk, 1 << d)
    print(f"  chain r={rc} in [d={d}, 2^d={1<<d}];  all-to-Y r={rk} == 2^d={1<<d}")


if __name__ == "__main__":
    print("test_reduction_nu_eq_basis:"); test_reduction_nu_eq_basis()
    print("test_exact_eq_brute:"); test_exact_eq_brute()
    print("test_r_bounds:"); test_r_bounds()
    print("ALL SMOKE TESTS PASSED")
