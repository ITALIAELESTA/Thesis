from z3 import *
import networkx as nx
import numpy as np
from itertools import combinations

set_param('parallel.enable', True)
set_param('sat.threads', 8)
set_param('sat.variable_decay', 0.9)


def add_symmetry_breaker(s, vert_vars, k, N):
    # first_v[b] will store the index of the first vertex in branch set b
    first_v = [Int(f"first_v_{b}") for b in range(1, k + 1)]

    for b in range(1, k + 1):
        # Constraints for first_v[b-1] (the index)
        # 1. A vertex at this index MUST be in the set
        s.add(Or([And(first_v[b - 1] == v, vert_vars[v] == b) for v in range(N)]))

        # 2. No vertex with a smaller index can be in the set
        for v in range(N):
            s.add(Implies(vert_vars[v] == b, first_v[b - 1] <= v))

    # 3. NOW apply the symmetry breaker: The indices must be increasing
    for b in range(k - 1):
        s.add(first_v[b] < first_v[b + 1])

def odd_minor_solver(graph: nx.Graph, k: int) -> Solver:
    s = Solver()
    nodes = list(graph.nodes())
    n = len(nodes)
    vert_vars = [Int(f"x_{i}") for i in range(n)]
    color_vars = [Bool(f"c_{i}") for i in range(n)]

    # 1. Domain and Size Constraints
    for x in vert_vars:
        s.add(x >= 0, x <= k)

    for b_id in range(1, k + 1):
        # This is much faster for the solver to process than Sum(If...)
        nodes_in_this_set = [vert_vars[v] == b_id for v in range(n)]
        s.add(AtLeast(*nodes_in_this_set, 1))
        s.add(AtMost(*nodes_in_this_set, 2))

    add_symmetry_breaker(s,vert_vars, k, n)

    # 2. Bipartite Branch Sets (Optimized via non-edges)
    # If size is 2, the two nodes MUST be adjacent.
    for i, j in combinations(range(n), 2):
        if not graph.has_edge(nodes[i], nodes[j]):
            # Non-edges cannot be in the same branch set
            for b_id in range(1, k + 1):
                s.add(Not(And(vert_vars[i] == b_id, vert_vars[j] == b_id)))
        else:
            # If they ARE an edge and in the same set, they must have different colors
            for b_id in range(1, k + 1):
                s.add(Implies(And(vert_vars[i] == b_id, vert_vars[j] == b_id),
                              color_vars[i] != color_vars[j]))

    # 3. Odd Clique Connections (The "Existence" Clause)
    # For every pair of branch sets, there must be an edge with same-colored endpoints
    for b1, b2 in combinations(range(1, k + 1), 2):
        possible_odd_edges = []

        for i, j in combinations(range(n), 2):
            # Only consider actual edges in the graph
            if graph.has_edge(nodes[i], nodes[j]):
                # Edge (i,j) is an "odd connection" between b1 and b2 if:
                # (i in b1 AND j in b2 AND same color) OR (i in b2 AND j in b1 AND same color)
                is_odd = And(color_vars[i] == color_vars[j],
                             Or(And(vert_vars[i] == b1, vert_vars[j] == b2),
                                And(vert_vars[i] == b2, vert_vars[j] == b1)))
                possible_odd_edges.append(is_odd)

        s.add(Or(*possible_odd_edges))

    # for b1,b2 in combinations(range(1, k + 1), 2):
    #     non_odd_edges = []
    #     for i, j in combinations(range(n), 2):
    #         if not graph.has_edge(nodes[i], nodes[j]):
    #             non_edge = And(
    #                 color_vars[i] == color_vars[j],
    #                     Or(
    #                         And (vert_vars[i] == b1, vert_vars[j] == b2),
    #                         And (vert_vars[i] == b2, vert_vars[j] == b1)
    #                            ))
    #             non_odd_edges.append(non_edge)
    #     s.add(Not(And(*non_odd_edges)))

    return s


def print_model_from_solver(s: Solver):
    """
    Parses and prints the branch sets directly from the Solver object.
    Ensures Color A is printed first for branch sets of size 2.
    """
    check_result = s.check()
    if check_result != sat:
        print(f"Result: {check_result}")
        return

    model = s.model()
    branch_assignments = {}  # { node_id: branch_id }
    color_assignments = {}  # { node_id: bool }

    # 1. Scrape all variables
    for d in model.decls():
        name = d.name()
        value = model.get_interp(d)

        if name.startswith("x_"):
            node_id = name.split("_")[1]
            b_id = value.as_long()
            if b_id > 0:
                branch_assignments[node_id] = b_id

        elif name.startswith("c_"):
            node_id = name.split("_")[1]
            color_assignments[node_id] = is_true(value)

    # 2. Organize nodes into sets
    sets = {}
    for node_id, b_id in branch_assignments.items():
        if b_id not in sets:
            sets[b_id] = []

        # We store the raw boolean so we can sort by it later
        is_color_a = color_assignments.get(node_id, False)
        sets[b_id].append({
            "label": f"Node {node_id} ({'Color A' if is_color_a else 'Color B'})",
            "is_a": is_color_a
        })

    # 3. Print the results
    print("=" * 40)
    print(f"{'SHALLOW ODD MINOR CONFIGURATION':^40}")
    print("=" * 40)

    for b_id in sorted(sets.keys()):
        # Sort members: True (Color A) comes before False (Color B)
        # reverse=True ensures 1 (True) comes before 0 (False)
        sorted_members = sorted(sets[b_id], key=lambda x: x["is_a"], reverse=True)

        member_strings = [m["label"] for m in sorted_members]
        print(f"Branch Set {b_id:02}: [ {' -- '.join(member_strings)} ]")

    print("=" * 40)

