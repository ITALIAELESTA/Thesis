import networkx as nx
import collections as c
import time

"""
Clique search, only the second one is being used
"""
def has_clique_of_size(some_graph, threshold,time_limit=None,using_core_method=True):
    """
    Returns True as soon as a maximal clique of size >= s is found.
    Otherwise, returns False after checking all maximal cliques.

    If no time limit is given, will run until it finds a large clique or ran through all the cliques.
    By then, the universe would have collapsed :skull_emoji:
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

        if time.time() - start_time > time_limit and time_limit:
            exit_via_time_limit = True
            print(f"\nTIME LIMIT EXCEEDED")
            break  # Exit the loop if too much time has passed
    return False,exit_via_time_limit
    #implement a "fail-safe" if the computation takes too long

def has_large_clique(graph, threshold,time_limit=None,nodes=None):
    """
    Function is adapted from the find_cliques function of the networkx library.

    Returns True if a clique of size >= threshold exists.
    Returns False if no such clique exists OR if time_limit is reached.

    If no time limit is given, will run until it finds a large clique or ran through all the cliques.
    By then, the universe would have collapsed :skull_emoji:
    """
    start_time = time.time()
    G = nx.k_core(graph, k=threshold - 1) # does not seem to do anything in practice,
    # at least for odd extended graph which have a large core number
    if threshold <= 0: return True, False #those two lines are useless in the event threshold is nb_vertices/2
    if len(G) < threshold: return False, False

    adj = {u: {v for v in G[u] if v != u} for u in G}
    Q = nodes[:] if nodes is not None else []

    cand = set(G)
    for node in Q:
        if node not in cand:
            raise ValueError(f"The given `nodes` {nodes} do not form a clique")
        cand &= adj[node]

    if len(Q) >= threshold: return True, False

    if not cand:
        return len(Q) >= threshold

    subg = cand.copy()
    stack = []
    Q.append(None)

    u = max(subg, key=lambda u: len(cand & adj[u]))
    ext_u = cand - adj[u]

    try:
        while True:
            if time_limit and (time.time() - start_time) > time_limit:
                print(f"Timeout reached ({time_limit}s). Terminating search.")
                return False, True
            if ext_u:
                q = ext_u.pop()
                cand.remove(q)
                Q[-1] = q

                current_size = len([n for n in Q if n is not None])
                # print(current_size)
                if current_size >= threshold:
                    # print(f"Algorithm works well, there is a clique of size: {current_size}, which should equal {threshold}")
                    return True, False



                adj_q = adj[q]
                cand_q = cand & adj_q

                # Pruning: Only dive deeper if threshold is physically reachable
                if current_size + len(cand_q) >= threshold:
                    subg_q = subg & adj_q
                    if subg_q:
                        stack.append((subg, cand, ext_u))
                        Q.append(None)
                        subg = subg_q
                        cand = cand_q
                        u = max(subg, key=lambda u: len(cand & adj[u]))
                        ext_u = cand - adj[u]
            else:
                Q.pop()
                subg, cand, ext_u = stack.pop()
    except IndexError:
        return False, False

def has_s_core(G, S): #quick algorithm, but is likely (how likely?) to skip a counterexample
    """
    Prunes the graph G to find if an (S-1)-core exists using an O(n+m) approach.
    Uses collections.deque for efficient O(1) pop operations.
    """
    if G.number_of_nodes() < S:
        return False

    threshold = S - 1
    # 1. Initialize degrees and the double-ended queue
    degrees = dict(G.degree())
    queue = c.deque([node for node, deg in degrees.items() if deg < threshold])

    # Track removed nodes in a set for O(1) lookups
    removed = set(queue)
    remaining_count = G.number_of_nodes() - len(removed)

    # 2. Iterative pruning
    while queue:
        # popleft() is O(1), whereas list.pop(0) is O(n)
        v = queue.popleft()

        for neighbor in G.neighbors(v):
            if neighbor not in removed:
                degrees[neighbor] -= 1

                # If neighbor's degree drops below threshold, prune it
                if degrees[neighbor] < threshold:
                    removed.add(neighbor)
                    queue.append(neighbor)
                    remaining_count -= 1

                    # Early exit: if we have fewer than S nodes left,
                    # an S-clique is mathematically impossible.
                    if remaining_count < S:
                        return False

    return remaining_count >= S

