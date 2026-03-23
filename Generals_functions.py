import networkx as nx
# from tqdm import tqdm
from itertools import combinations
import numpy as np
import time

start = time.time()

def min_degree(some_graph):
    deltaG = min(nbhood[1] for nbhood in some_graph.degree())
    return deltaG

def is_clique(graph,list_of_nodes):
    for pair in combinations(list_of_nodes,2):
        if not graph.has_edge(pair[0], pair[1]):
            return False
    return True

"""
For the creation of the graph H_0
"""


def get_triangles(some_graph):
    H = some_graph.copy()
    list_of_triangles = [clique for clique in nx.enumerate_all_cliques(H) if len(clique) == 3]
    return list_of_triangles

def remove_triangles(some_graph):
    """
    Finds all triangles in an undirected graph and removes one edge
    from each triangle to break the cycle.

    Tune so the removed edge is random, and not the one with lower index
    """
    # Create a copy so we don't modify the original graph object unexpectedly
    H = some_graph.copy()

    # We loop because removing one edge might affect multiple triangles
    # Find all 3-cliques (triangles)
    triangles = get_triangles(H)
    # this method of creating a list, loops through all the cliques given by the function, and keeps the one of size 3
    for triangle in triangles: #loops through all the triangles
        u,v,w = triangle
        if is_clique(H,triangle):# if not a triangle anymore, no need to remove an edge
            #necessary because if edge is not present, there is an error when trying to remove it
            # Remove the edge between the first two nodes of the triangle
            random_edge = np.random.randint(0,3)
            # print(random_edge)
            match random_edge:
                case 0:
                    H.remove_edge(u, v)
                case 1:
                    H.remove_edge(u,w)
                case 2:
                    H.remove_edge(v,w)
    return H

def uniform_random_fct(n,m):
    return np.random.randint(0,m,size=n)


def pullback(nb_vertices, some_graph, mapping):
    G = nx.Graph()
    # 1. Define the vertices for the new graph
    new_nodes = list(range(nb_vertices))
    G.add_nodes_from(new_nodes)

    # 2. Iterate over pairs of vertices in the NEW graph
    for u, v in combinations(new_nodes, 2):
        # 3. Check if their images under the map are connected in some_graph
        # map[u] and map[v] are the 'target' vertices
        if some_graph.has_edge(mapping[u], mapping[v]):
            G.add_edge(u, v)
            # print(mapping[u],mapping[v])

    return G

def Graph_h0(H_Red_prime, H_Blue_prime, nb_vertices, parameter_m):
    pi_Red = uniform_random_fct(nb_vertices, parameter_m)
    pi_Blue = uniform_random_fct(nb_vertices, parameter_m)

    red_graph = pullback(nb_vertices, H_Red_prime, pi_Red)
    blue_graph = pullback(nb_vertices, H_Blue_prime, pi_Blue)

    # CRITICAL: Convert to sets of frozensets to avoid ordering issues
    # and to make them static (not a live view of the graph)
    red_edges_set = {frozenset(e) for e in red_graph.edges()}
    blue_edges_set = {frozenset(e) for e in blue_graph.edges()}

    # Create H_0 as a fresh graph
    H_0 = nx.Graph()
    H_0.add_nodes_from(range(nb_vertices))
    H_0.add_edges_from(red_graph.edges())
    H_0.add_edges_from(blue_graph.edges())

    return H_0, red_edges_set, blue_edges_set

def clear_H0(nb_vertices,parameter_m,proba):
    H_R = nx.erdos_renyi_graph(parameter_m,proba)
    H_B = nx.erdos_renyi_graph(parameter_m,proba)
    H_R_prime = remove_triangles(H_R)
    H_B_prime = remove_triangles(H_B)
    h0,red_edges,blue_edges = Graph_h0(H_R_prime,H_B_prime,nb_vertices,parameter_m)
    #red_edges, blue_edges are frozen, it is necessary, before, it tagged every blue edge as red&blue
    for triangle in get_triangles(h0):
        if is_clique(h0, triangle):
            # Convert combinations to frozensets for the lookup
            tri_edges = [frozenset(e) for e in combinations(triangle, 2)]

            # Now these lookups are order-independent and accurate
            red_edges_triangle = [e for e in tri_edges if e in red_edges]
            blue_edges_triangle = [e for e in tri_edges if e in blue_edges]

            if len(red_edges_triangle) == 1:
                # To remove from h0, unpack the frozenset
                u, v = list(red_edges_triangle[0])
                h0.remove_edge(u, v)

            elif len(blue_edges_triangle) == 1:
                u, v = list(blue_edges_triangle[0])
                h0.remove_edge(u, v)

            else:
                # Randomly choose based on color groups
                if np.random.randint(0, 2):
                    # Remove red edges that are NOT also blue
                    to_remove = [e for e in red_edges_triangle if e not in blue_edges]
                    for e in to_remove:
                        u, v = list(e)
                        if h0.has_edge(u, v): h0.remove_edge(u, v)
                else:
                    # Remove blue edges that are NOT also red
                    to_remove = [e for e in blue_edges_triangle if e not in red_edges]
                    for e in to_remove:
                        u, v = list(e)
                        if h0.has_edge(u, v): h0.remove_edge(u, v)
    for triangle in get_triangles(h0):
        print("noob",triangle)
    return h0

"""
For the odd extension
"""

def odd_extension_graph(some_graph):
    temp_graph = some_graph.copy()
    original_vertices = set(some_graph.nodes())
    list_edges = list(some_graph.edges())
    adj = {n: set(some_graph[n]) for n in some_graph.nodes()}
    edge_nodes = []

    # Progress Bar 1: Adding edge-nodes
    # print("\nStage 1: Adding edge-nodes and connecting to original vertices...")
    for u, v in list_edges:
        f1, f2 = (u, v), (v, u)
        temp_graph.add_nodes_from([f1, f2])
        edge_nodes.extend([f1, f2])

        for vtx in original_vertices:
            if vtx != u and vtx != v:
                if u in adj[vtx]: temp_graph.add_edge(vtx, f1)
                if v in adj[vtx]: temp_graph.add_edge(vtx, f2)

    # Progress Bar 2: Connecting edge-nodes (The heavy loop)
    # print("\nStage 2: Connecting edge-nodes to each other...")
    # We calculate the total number of combinations for a more accurate bar
    # num_combinations = len(edge_nodes) * (len(edge_nodes) - 1) // 2

    for edge1, edge2 in combinations(edge_nodes, 2):  #, total=num_combinations):
        x, y = edge1
        xp, yp = edge2

        if x != xp and x != yp and y != xp and y != yp:
            if xp in adj[x] or yp in adj[y]:
                temp_graph.add_edge(edge1, edge2)
    return temp_graph


"""
Required for the check if it is a counterexample
"""
def has_clique_of_size(some_graph, threshold,time_limit,using_core_method=True):
    """
    Returns True as soon as a clique of size >= s is found.
    Otherwise, returns False after checking all maximal cliques.
    """
    # find_cliques yields maximal cliques one by one
    # print(time.time() - start)
    if using_core_method:
        core_graph = nx.k_core(some_graph, k=threshold - 1)
        graph_used = core_graph
    else:
        graph_used = some_graph
    # print(f"Start of clique computation:{time.time() - start}")
    start_time = time.time()
    exit_via_time_limit = False
    for clique in nx.find_cliques(graph_used): #can be optimized here, because find_cliques
        # only returns a maximal clique, so the computation might continue while having found a clique large enough
        if len(clique) >= threshold:
            print(f"Size of found clique:{len(clique)}, size of graph:{len(graph_used)}")
            return True,exit_via_time_limit

        if time.time() - start_time > time_limit:
            exit_via_time_limit = True
            print(f"\nTIME LIMIT EXCEEDED")
            break  # Exit the loop if too much time has passed
    return False,exit_via_time_limit
    #implement a "fail-safe" if the computation takes too long

