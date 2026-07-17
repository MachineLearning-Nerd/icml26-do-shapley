"""Core do-Shapley machinery for the reproduction of Parafita et al.,
"Exactly Computing do-Shapley Values" (arXiv 2602.07203, ICML 2026).

Implements the paper's definitions and algorithms directly from the PDF:

  * Definition 2.1 (Basis) and Definition 2.2 (Closure).
  * Algorithm 1  FindClass  -- compute basis S and closure S_bar of a set.
  * Algorithm 2  AllClasses -- enumerate the r equivalence classes (closed sets)
    by descending the lattice of closed sets via Lemma 3.1, in O(r(d+e)).
  * Equation 4  -- the r-class Shapley decomposition  phi_i = sum_j nu(c_j) w_i(c_j).
  * Brute-force Shapley over all 2^d coalitions (independent ground truth).

The graph is a DAG over nodes 0..d-1 (the d ancestor variables) plus a target
node Y = d.  Edges live in `parents`.  The value function nu(S) is supplied by
the caller (see scm.py); everything here is nu-agnostic.
"""
from __future__ import annotations
from math import comb
from itertools import combinations
from typing import Callable, Dict, FrozenSet, List, Sequence, Set, Tuple

ValueFn = Callable[[frozenset], float]


# --------------------------------------------------------------------------- #
#  Graph reachability helpers
# --------------------------------------------------------------------------- #
def _ancestors_of_target(parents: Dict[int, Set[int]], d: int) -> Set[int]:
    """Nodes in [d] with a directed path to the target node Y (= d)."""
    # children adjacency
    children: Dict[int, Set[int]] = {i: set() for i in range(d + 1)}
    for node, ps in parents.items():
        for p in ps:
            children[p].add(node)
    # reverse BFS from Y
    anc: Set[int] = set()
    stack = [d]
    seen = {d}
    while stack:
        n = stack.pop()
        for p in parents.get(n, ()):  # walk up the parents
            if p not in seen:
                seen.add(p)
                if p != d:
                    anc.add(p)
                stack.append(p)
    return anc


def reachable_to_target_after_do(parents: Dict[int, Set[int]], d: int,
                                 intervene: Set[int]) -> Set[int]:
    """Nodes in [d] that still have a directed path to Y in the graph G'
    obtained by deleting all incoming edges to `intervene` (Algorithm 1: G').
    Equivalently: ancestors of Y in the mutilated graph.

    Reverse BFS from Y: an edge p->n survives iff n is NOT intervened (its
    incoming edges are intact).  So we may extend upward through a node n only
    when n is not in `intervene`; an intervened node can be the *start* of a
    path (and is recorded as reachable) but never an intermediate hop, because
    its incoming edges are severed."""
    anc: Set[int] = set()
    stack = [d]
    seen = {d}
    while stack:
        n = stack.pop()
        if n in intervene:
            continue  # incoming edges to n are cut -> cannot extend upward via n
        for p in parents.get(n, ()):
            if p not in seen:
                seen.add(p)
                if p != d:
                    anc.add(p)
                stack.append(p)
    return anc


# --------------------------------------------------------------------------- #
#  Algorithm 1: FindClass
# --------------------------------------------------------------------------- #
def find_class(S: Set[int], parents: Dict[int, Set[int]], d: int
               ) -> Tuple[Set[int], Set[int]]:
    """Algorithm 1 (FindClass).

    Returns (basis, closure):
      * basis   = nodes of S that are still ancestors of Y after do(S);
      * closure = S plus every node of [d] that is NOT an ancestor of Y
                  after do(S) (i.e. blocked from Y by S).
    """
    nanc = reachable_to_target_after_do(parents, d, S)
    basis = S & nanc
    closure = S | (set(range(d)) - nanc)
    return basis, closure


def is_irreducible(S: Set[int], parents: Dict[int, Set[int]], d: int) -> bool:
    basis, _ = find_class(S, parents, d)
    return basis == S


def is_closed(S: Set[int], parents: Dict[int, Set[int]], d: int) -> bool:
    _, closure = find_class(S, parents, d)
    return closure == S


# --------------------------------------------------------------------------- #
#  Shapley class weights (closed form of Equation 5)
# --------------------------------------------------------------------------- #
def shapley_weight(d: int, ell: int) -> float:
    """Standard Shapley coalition weight  p_ell = 1 / (d * C(d-1, ell))."""
    return 1.0 / (d * comb(d - 1, ell))


def class_weight_i(i: int, basis: Set[int], closure: Set[int], d: int) -> float:
    """Closed-form weight w_i(c) for a class with given `basis` (S) and
    `closure` (S_bar).  Derived from Equation 5:

        if i in S    :  + sum_{ell=|S|}^{|S_bar|} C(|S_bar|-|S|, ell-|S|) p_{ell-1}
        if i notin S_bar : - sum_{ell=|S|}^{|S_bar|} C(|S_bar|-|S|, ell-|S|) p_ell
        else (i in S_bar \ S): 0   (verified independently to be exactly 0).
    """
    s = len(basis)
    L = len(closure)
    k = L - s  # number of "free" blocked nodes in the class
    if i in basis:
        return sum(comb(k, ell - s) * shapley_weight(d, ell - 1)
                   for ell in range(s, L + 1))
    if i not in closure:
        return -sum(comb(k, ell - s) * shapley_weight(d, ell)
                    for ell in range(s, L + 1))
    return 0.0  # i in closure \ basis  -> exactly zero (proven in the paper)


# --------------------------------------------------------------------------- #
#  Algorithm 2: AllClasses  (enumerate the r equivalence classes)
# --------------------------------------------------------------------------- #
def all_classes(parents: Dict[int, Set[int]], d: int
                ) -> List[Tuple[Set[int], Set[int]]]:
    """Algorithm 2 (AllClasses).  Returns the list of (basis, closure) for all
    r equivalence classes, discovered by descending the lattice of closed sets
    from [d] using Lemma 3.1 (closure \\ {j} is closed for j in basis).

    A closed set of size ell-1 can be generated from several closed sets of size
    ell, so we de-duplicate closures at each level (a set of frozensets).  The
    number of DISTINCT closures equals r; exactly one FindClass call per class
    => O(r(d+e))."""
    # closed[l] = de-duplicated set of closures known to be closed, of size l
    closed: Dict[int, Set[frozenset]] = {l: set() for l in range(d + 1)}
    full = frozenset(range(d))
    closed[d].add(full)
    classes: List[Tuple[Set[int], Set[int]]] = []
    # Descend d..0; the paper returns C0 U ... U Cd, so the empty-set class
    # (level 0) is included.  Level 0 generates no children.
    for ell in range(d, -1, -1):
        for closure in closed[ell]:
            basis, _ = find_class(set(closure), parents, d)  # one call per class
            classes.append((set(basis), set(closure)))
            # Lemma 3.1: closure \ {j} is closed for each j in basis
            for j in basis:
                child = frozenset(set(closure) - {j})
                if ell - 1 >= 0:
                    closed[ell - 1].add(child)
    return classes


def count_findclass_calls_in_allclasses(parents, d) -> int:
    """Diagnostic: the number of FindClass invocations performed by
    Algorithm 2 -- equals r (exactly one FindClass call per class)."""
    # Tracked inside all_classes by counting the returned classes.
    return len(all_classes(parents, d))


# --------------------------------------------------------------------------- #
#  Exact Shapley via the r-class decomposition (Equation 4)
# --------------------------------------------------------------------------- #
def exact_shapley(nu: ValueFn, parents: Dict[int, Set[int]], d: int
                  ) -> Tuple[List[float], Dict]:
    """phi_i = sum_{j=1..r} nu(c_j) * w_i(c_j).  Returns (phi, info)."""
    classes = all_classes(parents, d)
    phi = [0.0] * d
    nu_vals: List[float] = []
    for basis, closure in classes:
        # nu(c) = nu(any member) = nu(basis) = nu(closure)
        v = nu(frozenset(basis))
        nu_vals.append(v)
        for i in range(d):
            phi[i] += v * class_weight_i(i, basis, closure, d)
    info = {"r": len(classes), "nu_vals": nu_vals, "classes": classes}
    return phi, info


# --------------------------------------------------------------------------- #
#  Brute-force Shapley over all 2^d coalitions (independent ground truth)
# --------------------------------------------------------------------------- #
def brute_shapley(nu: ValueFn, d: int) -> List[float]:
    """phi_i = sum_{S subset [d]\\{i}} p_|S| [nu(S u {i}) - nu(S)]."""
    # precompute nu for every subset
    nu_of: Dict[frozenset, float] = {}
    for mask in range(1 << d):
        S = frozenset(j for j in range(d) if mask & (1 << j))
        nu_of[S] = nu(S)
    phi = [0.0] * d
    for i in range(d):
        for mask in range(1 << d):
            if mask & (1 << i):
                continue
            S = frozenset(j for j in range(d) if mask & (1 << j))
            ell = len(S)
            phi[i] += shapley_weight(d, ell) * (nu_of[S | {i}] - nu_of[S])
    return phi
