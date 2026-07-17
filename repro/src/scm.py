"""Linear-Gaussian Structural Causal Model and the interventional value
function nu(S) = E[Y | do(S = x_S)] for the do-Shapley reproduction.

The do-intervention is implemented faithfully: do(S = x_S) *deletes all incoming
edges to the nodes in S* and fixes those nodes to x_S, exactly as in Pearl's
do-calculus.  Because the SCM is linear, the interventional mean is obtained in
closed form by a single topological pass over the mutilated graph.

This gives a genuine causal value function, for which the paper's reduction
nu(S) = nu(basis(S)) is a *theorem* (do-calculus rule 3) that we verify
empirically rather than assume.
"""
from __future__ import annotations
from typing import Dict, Set, Tuple
import numpy as np


class LinearSCM:
    def __init__(self, d: int, parents: Dict[int, Set[int]],
                 weights: Dict[Tuple[int, int], float], intercepts: np.ndarray,
                 baseline: np.ndarray):
        """
        d          : number of ancestor variables (nodes 0..d-1); Y is node d.
        parents    : parents[node] -> set of parent node indices (within 0..d).
        weights    : weights[(p, node)] -> coefficient.
        intercepts : length d+1, structural intercept b_node.
        baseline   : length d, the fixed value x_S assigned to intervened vars
                     (the do-Shapley reference instance x).
        """
        self.d = d
        self.parents = {n: set(ps) for n, ps in parents.items()}
        self.weights = dict(weights)
        self.intercepts = intercepts.copy()
        self.baseline = baseline.copy()
        self._topo = self._topo_order()

    def _topo_order(self):
        # Kahn's algorithm over nodes 0..d (Y = d). Parents must precede child.
        n = self.d + 1
        indeg = [0] * n
        children: Dict[int, Set[int]] = {i: set() for i in range(n)}
        for node, ps in self.parents.items():
            for p in ps:
                children[p].add(node)
                indeg[node] += 1
        stack = [i for i in range(n) if indeg[i] == 0]
        order = []
        while stack:
            n0 = stack.pop()
            order.append(n0)
            for c in children[n0]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    stack.append(c)
        if len(order) != n:
            raise ValueError("graph has a cycle")
        return order

    def value(self, S: frozenset) -> float:
        """nu(S) = E[Y | do(S = x_S)] via mutilation + topological propagation.

        Nodes in S are clamped to `baseline` and their incoming edges removed."""
        d = self.d
        val = np.zeros(d + 1)
        intervened = set(S)
        for node in self._topo:
            if node in intervened:
                val[node] = self.baseline[node]
            else:
                s = self.intercepts[node]
                for p in self.parents.get(node, ()):
                    s += self.weights.get((p, node), 0.0) * val[p]
                val[node] = s
        return float(val[d])  # value of Y


# --------------------------------------------------------------------------- #
#  Random DAG generators (control graph density, hence r)
# --------------------------------------------------------------------------- #
def make_random_scm(d: int, edge_prob: float, y_parents_frac: float = 1.0,
                    seed: int = 0, baseline_value: float = 0.0) -> LinearSCM:
    """Random DAG: topological order 0<1<...<d-1; forward edge i->j (i<j)
    present with prob `edge_prob`.  Each node is a parent of Y with prob
    `y_parents_frac`.  Higher edge_prob => denser graph => larger r."""
    rng = np.random.default_rng(seed)
    parents: Dict[int, Set[int]] = {i: set() for i in range(d + 1)}
    weights: Dict[Tuple[int, int], float] = {}
    for j in range(1, d):
        for i in range(j):
            if rng.random() < edge_prob:
                parents[j].add(i)
                weights[(i, j)] = float(rng.normal(0.0, 1.0))
    # attach nodes to target Y
    for i in range(d):
        if rng.random() < y_parents_frac:
            parents[d].add(i)
            weights[(i, d)] = float(rng.normal(0.0, 1.0))
    intercepts = rng.normal(0.0, 1.0, d + 1)
    baseline = np.full(d, baseline_value, dtype=float)
    return LinearSCM(d, parents, weights, intercepts, baseline)


def make_chain_scm(d: int, seed: int = 0, baseline_value: float = 0.0) -> LinearSCM:
    """Chain X0->X1->...->X_{d-1}->Y.  Minimally connected: r == d."""
    rng = np.random.default_rng(seed)
    parents: Dict[int, Set[int]] = {i: set() for i in range(d + 1)}
    weights: Dict[Tuple[int, int], float] = {}
    for j in range(1, d):
        parents[j].add(j - 1)
        weights[(j - 1, j)] = float(rng.normal(0.0, 1.0))
    parents[d].add(d - 1)
    weights[(d - 1, d)] = float(rng.normal(0.0, 1.0))
    intercepts = rng.normal(0.0, 1.0, d + 1)
    baseline = np.full(d, baseline_value, dtype=float)
    return LinearSCM(d, parents, weights, intercepts, baseline)


def make_sparse_scm(d: int, extra_edge_prob: float = 0.0, seed: int = 0,
                    baseline_value: float = 0.0) -> LinearSCM:
    """Sparse *connected* DAG: a chain backbone X0->X1->...->X_{d-1}->Y
    guarantees every node is an ancestor of Y, then extra forward edges i->j
    (i<j) are added with prob `extra_edge_prob`.  Because the backbone makes
    many variables' paths to Y pass through other variables, most subsets are
    reducible, so r is well below 2^d (the paper's real-world regime).
    `extra_edge_prob` sweeps r from ~d+1 (chain) up toward 2^d."""
    rng = np.random.default_rng(seed)
    parents: Dict[int, Set[int]] = {i: set() for i in range(d + 1)}
    weights: Dict[Tuple[int, int], float] = {}
    # backbone chain (ensures all nodes reach Y)
    for j in range(1, d):
        parents[j].add(j - 1)
        weights[(j - 1, j)] = float(rng.normal(0.0, 1.0))
    parents[d].add(d - 1)
    weights[(d - 1, d)] = float(rng.normal(0.0, 1.0))
    # extra forward edges (i<j) -- these are the only edges that can shortcut
    # the backbone and increase r toward 2^d
    for j in range(1, d):
        for i in range(j - 1):  # skip the backbone edge (i=j-1 already added)
            if rng.random() < extra_edge_prob:
                parents[j].add(i)
                weights[(i, j)] = float(rng.normal(0.0, 1.0))
    # a few extra direct feeders into Y as extra_edge_prob allows
    for i in range(d - 1):
        if rng.random() < extra_edge_prob * 0.5:
            parents[d].add(i)
            weights[(i, d)] = float(rng.normal(0.0, 1.0))
    intercepts = rng.normal(0.0, 1.0, d + 1)
    baseline = np.full(d, baseline_value, dtype=float)
    return LinearSCM(d, parents, weights, intercepts, baseline)


def make_complete_bipartite_to_y(d: int, seed: int = 0,
                                 baseline_value: float = 0.0) -> LinearSCM:
    """All d nodes point directly to Y, no other edges.  Every subset is
    irreducible (each node has a direct path to Y through no other node),
    so r == 2^d (the worst case)."""
    rng = np.random.default_rng(seed)
    parents: Dict[int, Set[int]] = {i: set() for i in range(d + 1)}
    weights: Dict[Tuple[int, int], float] = {}
    for i in range(d):
        parents[d].add(i)
        weights[(i, d)] = float(rng.normal(0.0, 1.0))
    intercepts = rng.normal(0.0, 1.0, d + 1)
    baseline = np.full(d, baseline_value, dtype=float)
    return LinearSCM(d, parents, weights, intercepts, baseline)
