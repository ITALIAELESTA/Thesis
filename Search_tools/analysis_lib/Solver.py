from z3 import *
import networkx as nx
import numpy as np
from itertools import combinations

import psutil

set_param('parallel.enable', True)
set_param('sat.threads', 8)
set_param('sat.variable_decay', 1)

def light_symmetry_breaker(s,vert_vars,k,n):
    for b in range(2, k + 1):
        for v in range(1, n):
            s.add(Implies(vert_vars[v] == b,
                          Or([vert_vars[u] == b - 1 for u in range(v)])))

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

    is_pair = [Bool(f"is_pair_{b}") for b in range(1, k + 1)]
    #candidates do not have a clique of size k, so if there is an odd minor it must have at least two pairs
    # (if only one there is a normal clique)
    for b in range(1, k + 1):
        indicators = [vert_vars[v] == b for v in range(n)]
        # is_pair[b-1] is true if the set size is exactly 2
        s.add(is_pair[b - 1] == (PbEq([(indicators[v], 1) for v in range(n)], 2)))
        #this line is to ensure that if is_pair_j, the branch set B_j has exactly two vertices

    # 3. Add your brute-force knowledge: "At least 2 sets are pairs"
    # This doesn't care if it's B1 and B2 or B10 and B25.
    s.add(AtLeast(*is_pair, 2))

    add_symmetry_breaker(s,vert_vars, k, n)

    # 2. Bipartite Branch Sets (Optimized via non-edges)
    # If size is 2, the two nodes MUST be adjacent.
    for i, j in combinations(range(n), 2):
        if not graph.has_edge(nodes[i], nodes[j]):
            # Non-edges cannot be in the same set
            s.add(Implies(vert_vars[i] > 0, vert_vars[i] != vert_vars[j]))
        else:
            # If they ARE an edge and in the same set, they must have different colors
            s.add(Implies(And(vert_vars[i] == vert_vars[j], vert_vars[i] > 0),
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

def print_used_memory():
    process = psutil.Process(os.getpid())
    print(f"Memory in use: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    
def get_c4_induced_solver(G,show_memory_used=False):
    """
    Returns a Z3 solver that checks if the graph G contains
    an induced subgraph isomorphic to C4.
    """

    solver = Solver()
    nodes = list(G.nodes())

    # Define 4 variables representing the indices of the vertices in G
    # mapping to the vertices of the C4 cycle (p1, p2, p3, p4)
    p = [Int(f'p{i}') for i in range(4)]

    # Constraint 1: Every p[i] must correspond to a valid node index in G
    for i in range(4):
        solver.add(p[i] >= 0, p[i] < len(nodes))

    # Constraint 2: All four vertices must be distinct
    solver.add(Distinct(p))

    # Define the adjacency matrix for the target C4
    # Edges: (0,1), (1,2), (2,3), (3,0)
    c4_edges = {(0, 1), (1, 2), (2, 3), (3, 0)}

    # Constraint 3: The "Induced" Mapping
    # For every pair (i, j) in our 4 chosen vertices:
    # If (i, j) is an edge in C4, there MUST be an edge in G.
    # If (i, j) is NOT an edge in C4, there MUST NOT be an edge in G.
    
    for i in range(4):
        for j in range(i + 1, 4):
            if show_memory_used: print_used_memory()
            # Check if this pair is part of the C4 cycle
            is_c4_edge = (i, j) in c4_edges or (j, i) in c4_edges

            # Build the condition based on G's actual adjacency
            edge_conditions = []
            for u_idx in range(len(nodes)):
                for v_idx in range(len(nodes)):
                    if u_idx == v_idx:
                        continue

                    # Does an edge exist between node at u_idx and node at v_idx?
                    has_edge = G.has_edge(nodes[u_idx], nodes[v_idx])

                    if is_c4_edge:
                        # If it should be an edge, G must have it
                        if not has_edge:
                            solver.add(Not(And(p[i] == u_idx, p[j] == v_idx)))
                            solver.add(Not(And(p[i] == v_idx, p[j] == u_idx)))
                    else:
                        # If it's an induced subgraph, non-C4-edges must NOT exist in G
                        if has_edge:
                            solver.add(Not(And(p[i] == u_idx, p[j] == v_idx)))
                            solver.add(Not(And(p[i] == v_idx, p[j] == u_idx)))

    return solver

