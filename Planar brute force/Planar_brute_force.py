#!/usr/bin/env python3
"""
Verifier for the finite part of the proof that Hadwiger's conjecture holds
for complements of planar graphs on at most 19 vertices.

Input: graph6 lines for planar graphs H.  The program checks only the boundary
families left by the proof:
  n=13, chi(complement(H))=7, 28 <= e(H) <= 33
  n=14, chi(complement(H))=7, e(H)=36
  n=15, chi(complement(H))=8, 36 <= e(H) <= 39
  n=17, chi(complement(H))=9, e(H)=45
For each such H, it verifies that complement(H) has a K_chi minor.

The graph6 input can be produced by plantri, for example with options -p -g
and the corresponding vertex/edge ranges.  The verifier itself is independent
of plantri: it checks planarity, chromatic number, and the clique minor directly.
"""

from __future__ import annotations

import argparse
import sys
from functools import lru_cache
from typing import Iterable, List, Sequence, Tuple

import networkx as nx

# Boundary cases left by the proof: (number of vertices, chromatic number) -> allowed |E(H)|.
WINDOWS = {
    (13, 7): set(range(28, 34)),
    (14, 7): {36},
    (15, 8): set(range(36, 40)),
    (17, 9): {45},
}
RELEVANT_N = {13, 14, 15, 17}


def relabel_0_to_n_minus_1(G: nx.Graph) -> nx.Graph:
    """Return an isomorphic graph whose vertices are 0,1,...,n-1."""
    return nx.convert_node_labels_to_integers(G, ordering="default")


def adjacency_masks(G: nx.Graph) -> List[int]:
    """Bit-mask adjacency representation.  Vertices must be 0..n-1."""
    n = G.number_of_nodes()
    adj = [0] * n
    for u, v in G.edges():
        adj[u] |= 1 << v
        adj[v] |= 1 << u
    return adj


def can_color(G: nx.Graph, q: int) -> bool:
    """Exact q-colourability by DSATUR backtracking."""
    G = relabel_0_to_n_minus_1(G)
    n = G.number_of_nodes()
    if n == 0:
        return True
    adj_sets = [set(G.neighbors(v)) for v in range(n)]
    degrees = [len(adj_sets[v]) for v in range(n)]
    color = [-1] * n
    sat = [set() for _ in range(n)]
    uncolored = set(range(n))

    def dfs(left: int) -> bool:
        if left == 0:
            return True

        # DSATUR choice: largest saturation degree, then largest ordinary degree.
        v = max(uncolored, key=lambda x: (len(sat[x]), degrees[x]))
        forbidden = sat[v]

        # Try colours in a deterministic order.  The test forbidden-by-sat is enough,
        # because sat[v] stores colours used by coloured neighbours.
        for c in range(q):
            if c in forbidden:
                continue
            changed = []
            color[v] = c
            uncolored.remove(v)
            for w in adj_sets[v]:
                if color[w] == -1 and c not in sat[w]:
                    sat[w].add(c)
                    changed.append(w)
            if dfs(left - 1):
                return True
            for w in changed:
                sat[w].remove(c)
            uncolored.add(v)
            color[v] = -1
        return False

    return dfs(n)


def chromatic_number(G: nx.Graph) -> int:
    """Exact chromatic number."""
    G = relabel_0_to_n_minus_1(G)
    n = G.number_of_nodes()
    # A small lower bound from clique number saves time, but correctness does not depend on it.
    lb = 1
    try:
        lb = max((len(C) for C in nx.find_cliques(G)), default=1)
    except Exception:
        lb = 1
    for q in range(lb, n + 1):
        if can_color(G, q):
            return q
    raise RuntimeError("unreachable: every n-vertex graph is n-colourable")


def _connected_subsets(adj: Sequence[int], max_size: int) -> Tuple[List[int], List[int]]:
    """All nonempty connected vertex subsets of size at most max_size.

    Returns (subsets, neighbourhood_masks), sorted by size and then mask.
    """
    n = len(adj)
    full = 1 << n

    @lru_cache(maxsize=None)
    def neigh(mask: int) -> int:
        if mask == 0:
            return 0
        lsb = mask & -mask
        v = lsb.bit_length() - 1
        return neigh(mask ^ lsb) | adj[v]

    def is_connected(mask: int) -> bool:
        start = mask & -mask
        seen = 0
        stack = start
        while stack:
            lsb = stack & -stack
            stack ^= lsb
            if seen & lsb:
                continue
            seen |= lsb
            v = lsb.bit_length() - 1
            stack |= adj[v] & mask & ~seen
        return seen == mask

    subsets = []
    for mask in range(1, full):
        if mask.bit_count() <= max_size and is_connected(mask):
            subsets.append(mask)
    subsets.sort(key=lambda m: (m.bit_count(), m))
    nbh = [neigh(m) for m in subsets]
    return subsets, nbh


def has_complete_minor(G: nx.Graph, t: int) -> bool:
    """Exact test for a K_t minor by searching branch-set models.

    A branch-set model is a collection of t pairwise disjoint, nonempty, connected
    vertex sets that are pairwise adjacent.  Since n <= 19 in this application,
    a direct bit-mask backtracking search is adequate.
    """
    G = relabel_0_to_n_minus_1(G)
    n = G.number_of_nodes()
    if t <= 1:
        return n >= t
    if n < t:
        return False

    # Fast positive test.
    if any(len(C) >= t for C in nx.find_cliques(G)):
        return True

    adj = adjacency_masks(G)
    max_branch_size = n - t + 1
    subsets, nbh = _connected_subsets(adj, max_branch_size)
    N = len(subsets)

    # For each subset index i, a bit mask of vertices in subsets[i] and its neighbour mask.
    chosen: List[int] = []
    chosen_nbh: List[int] = []

    def dfs(start: int, depth: int, used: int) -> bool:
        remaining_sets = t - depth
        if remaining_sets == 0:
            return True
        if n - used.bit_count() < remaining_sets:
            return False

        # Branch sets are unordered; requiring increasing subset-index removes permutations.
        for i in range(start, N):
            S = subsets[i]
            if S & used:
                continue
            # Leave at least one vertex for every future branch set.
            if n - (used | S).bit_count() < remaining_sets - 1:
                continue
            ok = True
            for B, NB in zip(chosen, chosen_nbh):
                # Pairwise adjacent means some edge between S and B.
                if not (nbh[i] & B):
                    ok = False
                    break
                # Symmetric for simple graphs, kept only as a sanity guard for masks.
                if not (NB & S):
                    ok = False
                    break
            if not ok:
                continue
            chosen.append(S)
            chosen_nbh.append(nbh[i])
            if dfs(i + 1, depth + 1, used | S):
                return True
            chosen.pop()
            chosen_nbh.pop()
        return False

    return dfs(0, 0, 0)


def read_graph6_stream(stream: Iterable[bytes]) -> Iterable[nx.Graph]:
    """Yield graphs from graph6 lines, ignoring graph6 headers and blank lines."""
    for raw in stream:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(b">>graph6<<"):
            # graph6 headers, when present, may be concatenated with the first graph.
            line = line[len(b">>graph6<<"):]
            if not line:
                continue
        elif line.startswith(b">>"):
            continue
        yield nx.from_graph6_bytes(line)


def verify_graph(H_raw: nx.Graph, check_planarity: bool = True) -> Tuple[bool, str]:
    """Return (ok, message).  ok=False means a counterexample was found."""
    H = relabel_0_to_n_minus_1(H_raw)
    n = H.number_of_nodes()
    if n not in RELEVANT_N:
        return True, "skipped: irrelevant order"
    if check_planarity and not nx.check_planarity(H, counterexample=False)[0]:
        raise ValueError("input graph is not planar")

    mH = H.number_of_edges()
    G = nx.complement(H)
    k = chromatic_number(G)
    if (n, k) not in WINDOWS or mH not in WINDOWS[(n, k)]:
        return True, "skipped: not in a boundary window"

    if has_complete_minor(G, k):
        return True, f"checked: n={n}, eH={mH}, chi={k}"

    bad = nx.to_graph6_bytes(H, header=False).decode("ascii").strip()
    return False, f"COUNTEREXAMPLE H in graph6: {bad}  (n={n}, eH={mH}, chi={k})"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="graph6 files; stdin is used if none are given")
    parser.add_argument("--trust-planar", action="store_true", help="skip NetworkX planarity check")
    args = parser.parse_args(argv)

    total = 0
    boundary = 0
    by_case = {}

    def process_stream(fh) -> int:
        nonlocal total, boundary, by_case
        for H in read_graph6_stream(fh):
            total += 1
            H = relabel_0_to_n_minus_1(H)
            n = H.number_of_nodes()
            mH = H.number_of_edges()
            if n in RELEVANT_N:
                G = nx.complement(H)
                # Avoid doing chromatic/minor work unless the edge count could matter.
                possible_edge = any(n == nn and mH in es for (nn, _), es in WINDOWS.items())
                if possible_edge:
                    ok, msg = verify_graph(H, check_planarity=not args.trust_planar)
                    if not ok:
                        print(msg, file=sys.stderr)
                        return 1
                    if msg.startswith("checked:"):
                        boundary += 1
                        key = (n, chromatic_number(G), mH)
                        by_case[key] = by_case.get(key, 0) + 1
        return 0

    if args.files:
        for path in args.files:
            with open(path, "rb") as fh:
                rc = process_stream(fh)
                if rc:
                    return rc
    else:
        rc = process_stream(sys.stdin.buffer)
        if rc:
            return rc

    print(f"OK: no counterexample found.  input graphs={total}; boundary graphs checked={boundary}.")
    for key in sorted(by_case):
        n, k, mH = key
        print(f"  n={n:2d}, chi={k:2d}, e(H)={mH:2d}: {by_case[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


