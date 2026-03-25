import networkx as nx
from Generals_functions import*

def graph_with_alphatwo(nb_vert, proba):
    graph = nx.erdos_renyi_graph(nb_vert, proba)
    print(time.time()-start)
    graph_without_triangles = remove_triangles(graph)
    print(time.time()-start)
    cleared_graph = nx.complement(graph_without_triangles)
    print(time.time()-start)
    return cleared_graph

def odd_extension_graph_with_progress(some_graph):
    temp_graph = some_graph.copy()
    original_vertices = set(some_graph.nodes())
    list_edges = list(some_graph.edges())
    adj = {n: set(some_graph[n]) for n in some_graph.nodes()}
    edge_nodes = []

    # Progress Bar 1: Adding edge-nodes
    print("Stage 1: Adding edge-nodes and connecting to original vertices...")
    for u, v in tqdm(list_edges):
        f1, f2 = (u, v), (v, u)
        temp_graph.add_nodes_from([f1, f2])
        edge_nodes.extend([f1, f2])

        for vtx in original_vertices:
            if vtx != u and vtx != v:
                if u in adj[vtx]: temp_graph.add_edge(vtx, f1)
                if v in adj[vtx]: temp_graph.add_edge(vtx, f2)

    # Progress Bar 2: Connecting edge-nodes (The heavy loop)
    print("\nStage 2: Connecting edge-nodes to each other...")
    # We calculate the total number of combinations for a more accurate bar
    num_combinations = len(edge_nodes) * (len(edge_nodes) - 1) // 2

    for edge1, edge2 in tqdm(combinations(edge_nodes, 2), total=num_combinations):
        x, y = edge1
        xp, yp = edge2

        if x != xp and x != yp and y != xp and y != yp:
            if xp in adj[x] or yp in adj[y]:
                temp_graph.add_edge(edge1, edge2)

    return temp_graph

def find_counterexamples(range1,range2, nb_trials=5):
    file_name_for_time_data = datetime.datetime.now().strftime('%d_%m_%Y_%Hh%M%S')
    approximation_mode = 1
    s_core_check_mode = 2
    clique_of_size_n_over_2_mode = 3
    print(f"To use clique n/log^2(n) approximation, type {approximation_mode}"
          f"\n To use s_core check, type {s_core_check_mode}"
          f"\n To use the mode where it checks if the graph has a clique of size n/2, type{clique_of_size_n_over_2_mode}")
    desired_mode = int(input("Desired mode: "))

    cliques_apx = np.array([])
    times_values = np.array([])
    for nb_vertices in range(range1,range2+1):
        param = 6
        proba = 0.1
        total_creation_time = 0
        total_analysis_time = 0
        average_minor = 0
        for trials in range(0,nb_trials):
            time_start = time.time()
            random_graph = nx.complement(clear_H0(nb_vertices,param,proba))
            print("Random graph : ok !")
            odd_extended_random_graph = odd_extension_graph(random_graph)
            print("Odd extension : ok !")
            graph_created_time = time.time()
            graph_creation_duration = time.time() - time_start
            total_creation_time += graph_creation_duration
            match desired_mode:
                case 1:#uses the clique_approximation function from networkx
                    max_odd_minor = len(nx.approximation.max_clique(odd_extended_random_graph))
                    if max_odd_minor < nb_vertices/2:
                        # 1. Create the directory path object
                        folder_path = Path(f"Counterexamples_approx/vertices_{nb_vertices}")

                        # 2. Create the folder if it doesn't exist
                        folder_path.mkdir(parents=True, exist_ok=True)

                        # 3. Generate timestamp with microseconds (%f)
                        # Result: "13_03_2026_16h22M05_123456"
                        timestamp = datetime.datetime.now().strftime('%d_%m_%Y_%Hh%M%S')

                        # 4. Construct the full file path
                        file_name = f"{nb_vertices},{timestamp}.csv"
                        full_path = folder_path / file_name

                        # 5. Save the matrix
                        matrix = nx.to_pandas_adjacency(random_graph)
                        matrix.to_csv(full_path, index=True)
                        print(f"Saved: {full_path}")
                    average_minor += max_odd_minor
                case 2:#checks if the graph has an n/2 core, useless for graph with \alpha(G)=2
                    if not has_s_core(odd_extended_random_graph, nb_vertices / 2):
                        # 1. Create the directory path object
                        folder_path = Path(f"Counterexamples_s_core/vertices_{nb_vertices}")

                        # 2. Create the folder if it doesn't exist
                        folder_path.mkdir(parents=True, exist_ok=True)

                        # 3. Generate timestamp with microseconds (%f)
                        # Result: "13_03_2026_16h22M05_123456"
                        timestamp = datetime.datetime.now().strftime('%d_%m_%Y_%Hh%M%S')

                        # 4. Construct the full file path
                        file_name = f"{nb_vertices},{timestamp}.csv"
                        full_path = folder_path / file_name

                        # 5. Save the matrix
                        matrix = nx.to_pandas_adjacency(random_graph)
                        matrix.to_csv(full_path, index=True)
                        print(f"Saved: {full_path}")
                case 3:#iterate through the cliques, and if it finds one that is larger than n/2, then skips
                    # implement a check, if it takes too long, save the graph as candidate
                    contains_large_clique, time_expired = (
                        has_clique_of_size(odd_extended_random_graph,nb_vertices/2,nb_vertices))
                    if not contains_large_clique:
                        # 1. Create the directory path object
                        if not time_expired:
                            folder_path = Path(f"Actual_Counterexamples/vertices_{nb_vertices}")
                            print("FOUND A COUNTEREXAMPLE !!!!!!!!!!")
                        else:
                            folder_path = Path(f"Candidates/vertices_{nb_vertices}")
                            print("time expired, possible candidate")

                        # 2. Create the folder if it doesn't exist
                        folder_path.mkdir(parents=True, exist_ok=True)

                        # 3. Generate timestamp with microseconds (%f)
                        # Result: "13_03_2026_16h22M05_123456"
                        timestamp = datetime.datetime.now().strftime('%d_%m_%Y_%Hh%M%S')

                        # 4. Construct the full file path
                        file_name = f"{nb_vertices},{timestamp}.csv"
                        full_path = folder_path / file_name

                        # 5. Save the matrix
                        matrix = nx.to_pandas_adjacency(random_graph)
                        matrix.to_csv(full_path, index=True)
                        print(f"Saved: {full_path}")
                case _:
                    print("wrong input")
                    return None

            time_required_for_analysis = time.time() - graph_created_time
            total_analysis_time += time_required_for_analysis

        cliques_apx = np.append(cliques_apx, average_minor/nb_trials) #for the plots
        times_values = np.append(times_values, total_analysis_time/nb_trials)

        # Log the timing
        Title_string =f"{file_name_for_time_data},"
        compl_string =""
        match desired_mode:
            case 1:
                Title_string += "timeittakes_to_find_apx_of_clique.txt"
                compl_string = "the apx of the clique"
            case 2:
                Title_string += "timeittakes_for_s_core.txt"
                compl_string = "if it has an s-core"
            case 3:
                Title_string += "timeittakes_for_classic_argument.txt"
                compl_string = "if it has a clique less than n/2"
        folder_path_time_logs = Path(f"Logs/{Title_string}")
        with open(folder_path_time_logs, "a") as f:
            # Using a standard f-string (no 'r') to ensure \n works
            f.write(f"\nNumber of vertices:{nb_vertices},"
                    f"Average time to create the odd graph:{round(total_creation_time/nb_trials,3)},"
                    f"Average time to find {compl_string}: {round(total_analysis_time/nb_trials,3)}")

    x_axis_range = np.arange(range1,range2+1)
    plt.scatter(x_axis_range,times_values)
    plt.axis('equal')
    plt.show()

