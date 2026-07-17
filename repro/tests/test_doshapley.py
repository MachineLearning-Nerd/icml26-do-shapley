"""Formal pytest suite for the do-Shapley reproduction (Parafita et al. 2602.07203).

Each test maps to a paper claim or lemma and is independent of the evidence
scripts (re-run-safe, deterministic).  Run:  pytest -q repro/tests
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import pytest
from doshapley import (find_class, all_classes, exact_shapley, brute_shapley,
                       class_weight_i, shapley_weight, is_irreducible, is_closed)
from scm import (make_random_scm, make_chain_scm, make_sparse_scm,
                 make_complete_bipartite_to_y)
from estimator import BoundarySampler, BlindSampler

P = lambda scm: {k: set(v) for k, v in scm.parents.items()}
maxdiff = lambda a, b: float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


# -- Lemma: nu(S) == nu(basis(S)) == nu(closure(S))  (do-calculus rule 3) -----
@pytest.mark.parametrize("seed", range(6))
def test_nu_reduction(seed):
    d, scm = 7, make_sparse_scm(7, extra_edge_prob=0.3, seed=seed)
    parents = P(scm)
    wb = wc = 0.0
    for mask in range(1 << d):
        S = frozenset(j for j in range(d) if mask & (1 << j))
        b, cl = find_class(set(S), parents, d)
        wb = max(wb, abs(scm.value(S) - scm.value(frozenset(b))))
        wc = max(wc, abs(scm.value(S) - scm.value(frozenset(cl))))
    assert wb == 0.0 and wc == 0.0


# -- Claim 1: exact r-class algorithm == brute-force 2^d, machine precision ----
@pytest.mark.parametrize("seed", range(8))
def test_exact_eq_brute(seed):
    d = 8
    scm = make_sparse_scm(d, extra_edge_prob=0.25, seed=seed)
    phi_ex, info = exact_shapley(scm.value, P(scm), d)
    phi_br = brute_shapley(scm.value, d)
    assert maxdiff(phi_ex, phi_br) < 1e-9


# -- Shapley efficiency axiom: sum_i phi_i == nu([d]) - nu(empty) -------------
@pytest.mark.parametrize("seed", range(6))
def test_efficiency(seed):
    d = 8
    scm = make_sparse_scm(d, extra_edge_prob=0.2, seed=seed)
    phi, _ = exact_shapley(scm.value, P(scm), d)
    eff = sum(phi) - (scm.value(frozenset(range(d))) - scm.value(frozenset()))
    assert abs(eff) < 1e-9


# -- Shapley symmetry: structurally identical variables get identical values ---
def test_symmetry():
    # X0 and X1 are symmetric (both direct, identical weights) -> equal phi
    from scm import LinearSCM
    d = 3
    parents = {0: set(), 1: set(), 2: set(), 3: {0, 1, 2}}
    weights = {(0, 3): 1.5, (1, 3): 1.5, (2, 3): 0.7}
    intercepts = np.array([0.0, 0.0, 0.0, 0.0])
    scm = LinearSCM(d, parents, weights, intercepts, np.zeros(d))
    phi, _ = exact_shapley(scm.value, P(scm), d)
    assert abs(phi[0] - phi[1]) < 1e-12


# -- r in [d, 2^d]; chain compressed, all-to-Y maximal -----------------------
def test_r_bounds():
    d = 7
    rc = len(all_classes(P(make_chain_scm(d, seed=1)), d))
    assert d <= rc <= (1 << d)
    rk = len(all_classes(P(make_complete_bipartite_to_y(d, seed=1)), d))
    assert rk == (1 << d)


# -- closed-form class weight == direct enumeration over class members ---------
def test_class_weight_closed_form():
    d = 7
    from itertools import combinations
    scm = make_sparse_scm(d, extra_edge_prob=0.35, seed=4)
    parents = P(scm)
    worst = 0.0
    for basis, closure in all_classes(parents, d):
        extra = [x for x in closure if x not in basis]
        for i in range(d):
            w = 0.0
            for k in range(len(extra) + 1):
                for combo in combinations(extra, k):
                    T = set(basis) | set(combo)
                    if i in T:
                        w += shapley_weight(d, len(T) - 1)
                    else:
                        w -= shapley_weight(d, len(T))
            worst = max(worst, abs(w - class_weight_i(i, basis, closure, d)))
    assert worst < 1e-12   # closed form agrees with direct enumeration (FP tol)


# -- FindClass returns a basis that is irreducible & a closure that is closed --
def test_findclass_canonical():
    d = 7
    scm = make_sparse_scm(d, extra_edge_prob=0.3, seed=2)
    parents = P(scm)
    for mask in range(1 << d):
        S = set(j for j in range(d) if mask & (1 << j))
        b, cl = find_class(S, parents, d)
        assert is_irreducible(b, parents, d)            # basis is irreducible
        assert is_closed(cl, parents, d)                # closure is closed
        assert b <= S <= cl                             # sandwich invariant


# -- Claim 2: boundary sampler == exact when budget m >= r --------------------
def test_boundary_exact_at_full_budget():
    d = 11
    scm = make_sparse_scm(d, extra_edge_prob=0.15, seed=5)
    parents = P(scm)
    phi_ex, info = exact_shapley(scm.value, parents, d)
    r = info["r"]
    bs = BoundarySampler(scm.value, parents, d)
    bs.run(budget=2 * r)
    assert len(bs.known) == r                      # discovered every class
    assert maxdiff(bs.estimate(), phi_ex) < 1e-12  # exact to machine precision


# -- Claim 2: boundary finds min(m,r) distinct classes; blind finds fewer ----
def test_boundary_dominates_blind():
    d = 12
    scm = make_sparse_scm(d, extra_edge_prob=0.2, seed=6)
    parents = P(scm)
    _, info = exact_shapley(scm.value, parents, d)
    r = info["r"]
    m = r // 2
    b = BoundarySampler(scm.value, parents, d); b.run(budget=m)
    bl = BlindSampler(scm.value, parents, d, np.random.default_rng(0)); bl.run(budget=m)
    assert len(b.known) == m        # boundary: every query a new class
    assert len(bl.known) < m        # blind: redundancy -> fewer distinct


# -- Negative control A: a SHAM value function (nu not reduced on classes) ---
# If nu differs across members of a class (violating the do-calculus reduction
# that the whole method relies on), the r-class formula MUST disagree with the
# brute-force definition.  Control "fails to match" => pass.
def test_negative_sham_value():
    d = 7
    scm = make_sparse_scm(d, extra_edge_prob=0.3, seed=8)
    parents = P(scm)
    rng = np.random.default_rng(0)
    sham = {mask: float(rng.normal()) for mask in range(1 << d)}  # per-subset noise
    nu_sham = lambda S: scm.value(S) + sham[sum(1 << j for j in S)]
    phi_ex, _ = exact_shapley(nu_sham, parents, d)   # collapses to basis (wrong)
    phi_br = brute_shapley(nu_sham, d)               # uses true per-subset nu
    assert maxdiff(phi_ex, phi_br) > 1e-3


# -- Negative control B: omitting the empty-set class breaks the partition -----
# This is the exact failure mode discovered during development: dropping the
# level-0 class leaves one coalition un-accounted, so exact != brute.
def test_negative_no_empty_class():
    d = 6
    scm = make_sparse_scm(d, extra_edge_prob=0.4, seed=9)
    parents = P(scm)
    phi_br = brute_shapley(scm.value, d)
    classes = [c for c in all_classes(parents, d) if len(c[1]) > 0]  # drop empty
    phi = [0.0] * d
    for basis, closure in classes:
        v = scm.value(frozenset(basis))
        for i in range(d):
            phi[i] += v * class_weight_i(i, basis, closure, d)
    assert maxdiff(phi, phi_br) > 1e-3
