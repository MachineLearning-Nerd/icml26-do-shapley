"""Estimators for do-Shapley values (Section 4 of Parafita et al. 2602.07203).

  * BoundarySampler  -- Algorithm 3 / doEstimator: a targeted lattice
    exploration that, with a budget of m value-function queries, is guaranteed
    to discover min(m, r) DISTINCT equivalence classes (Theorem in Sec. 4).
    It prioritises classes by expected weight magnitude and expands each
    visited class's lattice neighbours.  When m >= r it has visited every class
    and recovers the exact Shapley values to machine precision.

  * BlindSampler      -- the value-function-agnostic baseline: sample coalitions
    uniformly at random and cache nu by basis.  Because it samples blindly, a
    budget of m queries typically yields far fewer than m distinct classes
    (sample redundancy), so it converges far more slowly and does NOT reach
    machine precision at m = r.

Both estimators share the same final aggregation (Equation 4 restricted to the
discovered classes, with undiscovered classes contributing 0), so any accuracy
difference is attributable purely to *which/how many* classes each discovers.
"""
from __future__ import annotations
import heapq
from typing import Callable, Dict, List, Set, Tuple
from doshapley import find_class, class_weight_i, all_classes

ValueFn = Callable[[frozenset], float]


def estimate_from_known(known: Dict[frozenset, Tuple[Set[int], float]],
                        parents: Dict[int, Set[int]], d: int) -> List[float]:
    """phi_i = sum over known classes of nu(c) * w_i(c)."""
    phi = [0.0] * d
    for closure, (basis, nuval) in known.items():
        for i in range(d):
            phi[i] += nuval * class_weight_i(i, basis, set(closure), d)
    return phi


def _weight_magnitude(basis: Set[int], closure: Set[int], d: int) -> float:
    """Priority proxy: total absolute Shapley weight of a class,
    sum_i |w_i(c)|.  The paper orders by E_i |w_i(c)|; the total is a
    monotone proxy that is cheap to compute once the class is known."""
    return sum(abs(class_weight_i(i, basis, closure, d)) for i in range(d))


class BoundarySampler:
    """Algorithm 3: priority-queue lattice exploration.  Guarantees that every
    one of the m queries yields a NEW distinct class, up to r."""

    def __init__(self, nu: ValueFn, parents: Dict[int, Set[int]], d: int):
        self.nu = nu
        self.parents = parents
        self.d = d
        self.seen: Set[frozenset] = set()
        self.known: Dict[frozenset, Tuple[Set[int], float]] = {}
        # priority queue: (-priority, counter, closure_frozenset)
        self._queue: List[Tuple[float, int, frozenset]] = []
        self._ctr = 0
        self._enqueue(frozenset(range(d)))

    def _enqueue(self, closure: frozenset):
        if closure in self.seen:
            return
        basis, clo = find_class(set(closure), self.parents, self.d)
        pri = _weight_magnitude(basis, clo, self.d)
        self.seen.add(frozenset(clo))  # mark canonical closure as seen
        heapq.heappush(self._queue, (-pri, self._ctr, frozenset(clo)))
        self._ctr += 1

    def _neighbors(self, basis: Set[int], closure: Set[int]):
        d = self.d
        # lower neighbours: closure \ {j} for j in basis
        for j in basis:
            yield frozenset(set(closure) - {j})
        # upper neighbours: closure u {j} for j not in closure
        for j in range(d):
            if j not in closure:
                yield frozenset(set(closure) | {j})

    def run(self, budget: int) -> int:
        """Spend up to `budget` value-function queries.  Returns queries used."""
        queries = 0
        while queries < budget and self._queue:
            _, _, closure = heapq.heappop(self._queue)
            if closure not in self.seen:
                # could have been seen under a different key; skip
                self.seen.add(closure)
            basis, clo = find_class(set(closure), self.parents, self.d)
            canonical = frozenset(clo)
            if canonical in self.known:
                continue  # already queried this class
            nuval = self.nu(canonical)          # <-- the value-function query
            queries += 1
            self.known[canonical] = (set(basis), nuval)
            for nb in self._neighbors(set(basis), set(clo)):
                self._enqueue(nb)
        return queries

    def estimate(self) -> List[float]:
        return estimate_from_known(self.known, self.parents, self.d)


class BlindSampler:
    """Value-function-agnostic baseline: sample coalitions uniformly at random,
    cache nu by basis (so repeated classes cost no extra model eval but still
    count against the budget as a query).  Reports the distinct classes found."""

    def __init__(self, nu: ValueFn, parents: Dict[int, Set[int]], d: int,
                 rng):
        self.nu = nu; self.parents = parents; self.d = d; self.rng = rng
        self.known: Dict[frozenset, Tuple[Set[int], float]] = {}

    def run(self, budget: int) -> int:
        d = self.d
        queries = 0
        while queries < budget:
            # random coalition (non-empty subset), uniform over the 2^d-1
            mask = self.rng.integers(1, 1 << d)
            S = frozenset(j for j in range(d) if mask & (1 << j))
            basis, clo = find_class(set(S), self.parents, d)
            canonical = frozenset(clo)
            queries += 1  # the blind estimator pays a query even on a redundant class
            if canonical not in self.known:
                self.known[canonical] = (set(basis), self.nu(canonical))
        return queries

    def estimate(self) -> List[float]:
        return estimate_from_known(self.known, self.parents, self.d)


def num_classes(d: int, parents) -> int:
    return len(all_classes(parents, d))
