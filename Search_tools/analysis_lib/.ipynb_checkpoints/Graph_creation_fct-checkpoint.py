import networkx as nx
# from tqdm import tqdm
import collections as c
from itertools import combinations
import numpy as np
import time
import pandas as pd

start = time.time()

"""
General functions
"""

# def min_degree(some_graph):
#     deltaG = min(nbhood[1] for nbhood in some_graph.degree())
#     return deltaG

def is_clique(graph,list_of_nodes):
    for pair in combinations(list_of_nodes,2):
        if not graph.has_edge(pair[0], pair[1]):
            return False
    return True

"""
To remove the triangles in a graph
"""


def get_triangles(some_graph):
    H = some_graph.copy()
    list_of_triangles = [clique for clique in nx.enumerate_all_cliques(H) if len(clique) == 3]
    return list_of_triangles

def remove_triangles(some_graph):
    """
    Finds all triangles in an undirected graph and removes one edge
    from each triangle to break the cycle.

    The random part is to ensure that the removed edge is not necessarily the one between the lower index vertices
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

"""
For the creation of the graph H0 in [1], Section 3.
"""

def uniform_random_fct(n,m):
    return np.random.randint(0,m,size=n)


def pullback(some_graph, mapping):
    """
    From a graph G on m vertices, and a mapping f:[n] -> [m] (usually m<n), create a new graph
    G^ with n vertices and connect two vertices u,v iff f(u) and f(v) are adjacent in G.

    :param some_graph:
    :param mapping:
    :return:
    """
    G = nx.Graph()
    # 1. Define the vertices for the new graph
    # new_nodes = list(range(nb_vertices))
    new_nodes = list(range(len(mapping)))
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
    """
    Picks a random map 'red' pi_R and a random map 'blue' pi_B.
    Then, pullback (logic is handled by the pullback function) the triangleless red graph using the random map 'red' and
    similarly for the blue graph, pullback preserves clique number, so these graphs are triangleless.
    Afterward, it combines the graphs to create a graph H0 on n vertices, and keeps track of which edge are red and blue
    (might be both at the same time).
    :param H_Red_prime:
    :param H_Blue_prime:
    :param nb_vertices:
    :param parameter_m:
    :return:
    """
    pi_Red = uniform_random_fct(nb_vertices, parameter_m)
    pi_Blue = uniform_random_fct(nb_vertices, parameter_m)

    red_graph = pullback(H_Red_prime, pi_Red)
    blue_graph = pullback(H_Blue_prime, pi_Blue)

    # CRITICAL: Convert to sets of frozen sets to avoid ordering issues
    # and to make them static (not a live view of the graph)
    # later used to check which edges are red and which are blue, otherwise every edge is tagged as red
    # (networkx does not make copy using =, only a pointer to an element)
    red_edges_set = {frozenset(e) for e in red_graph.edges()}
    blue_edges_set = {frozenset(e) for e in blue_graph.edges()}

    # Create H_0 as a fresh graph
    H_0 = nx.Graph()
    H_0.add_nodes_from(range(nb_vertices))
    H_0.add_edges_from(red_graph.edges())
    H_0.add_edges_from(blue_graph.edges())

    return H_0, red_edges_set, blue_edges_set

def clear_H0(nb_vertices,parameter_m,proba):
    """
    Reproduces the process described in [1], Section 3.
    Creates two binomial random graphs on m vertices, with probability p, one is red H_R, the other is blue H_B.
    It then removes all triangles in both graphs (function remove_triangles) to get H_R' and H_B'.
    Next, (this part is handled inside the function Graph_h0), pick a random map 'red' pi_R and a random map 'blue' pi_B.
    Then, pullback (logic is handled by the pullback function) the triangleless red graph using the random map 'red' and
    similarly for the blue graph, pullback preserves clique number, so these graphs are triangleless.
    Afterward, it combines the graphs to create a graph H0 on n vertices, and keeps track of which edge are red and blue
    (might be both at the same time).
    This graph (very likely) has triangles which have at most two edges of each color. The triangles are removed as follows;
    - If a single edge is red, it is removed,
    - If a single edge is blue, it is removed,
    - If both colors are present twice, then either the exclusively red or the exclusively blue edge is removed,
        decided by a coin flip.
    The only step missing, is taking the complement, which is done outside of this function.

    Parameters -----------
    :param nb_vertices: Desired size of the final random graph, denoted by n in [1]
    :param parameter_m: Size of the two random graphs, denoted by m in [1]
    :param proba: Probability used to create the random graphs. denoted by p in [1]
    :return: The graph H0 from [1]

    References ---------
    [1]: Marcus Kühn, Lisa Sauermann, Raphael Steiner, and Yuval Wigderson. Disproof
    of the Odd Hadwiger Conjecture, December 2025. URL: https://arxiv.org/abs/2512.20392v1
    """
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
        print("Forgot a triangle :skull_emoji:",triangle) #sanity check, to be sure no triangle are left
    return h0

"""
For the odd extension
"""

def odd_extension_graph(some_graph):
    """
    Odd extension of a graph
    From an existing graph G, extend the vertex set as follows;
    For each edge xy add two nodes (x,y) and (y,x). They are distinguished as nodes.
    Regarding the edges we proceed as follows;
    - Keep all the original edges from G
    - If v is an original vertex and (a,b) a new vertex, connect them
        if and only if v is disjoint from (a,b) and ax is an edge in G.
        (it is not enough that bx is an edge in G)
    - If (a,b) and (c,d) are two new vertices, connect them if and only if they are disjoint and
    ac is an edge in G or bd is an edge in G

    A clique in the odd extension of a graph described a shallow odd clique minor

    :param some_graph: A simple non-oriented loopless graph
    :return: Odd extension of the input graph
    """
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
