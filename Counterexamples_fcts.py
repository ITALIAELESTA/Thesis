import datetime
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from Generals_functions import*
import time
from pathlib import Path
import collections as c
import csv
# from Scraped_functions import*

def find_counterexamples(range1,range2, nb_trials=5):
    time_tag_for_log = datetime.datetime.now().strftime('%d_%m_%Y_%Hh%M_%S')

    # cliques_apx = np.array([])
    # times_values = np.array([])
    for nb_vertices in range(range1,range2+1):
        print(f"Switched to {nb_vertices} vertices")
        param = 6
        proba = 0.1
        total_creation_time = 0
        total_analysis_time_using_core = 0
        for trials in range(0,nb_trials):
            print(f"Trial:{trials}")
            time_start = time.time()
            random_graph = nx.complement(clear_H0(nb_vertices,param,proba))
            print("Random graph : ok !")
            odd_extended_random_graph = odd_extension_graph(random_graph)
            print("Odd extension : ok !")
            graph_created_time = time.time()
            graph_creation_duration = graph_created_time - time_start
            print(f"Time needed to create the graph:{graph_creation_duration}")
            total_creation_time += graph_creation_duration
            #iterate through the cliques, and if it finds one that is larger than n/2, then skips
            # implement a check, if it takes too long, save the graph as candidate

            #likely won't exit via time limit, so no need to check if it did
            normal_graph_has_large_clique,_ = has_clique_of_size(random_graph,nb_vertices/2,nb_vertices)
            #usually happens that the original graph itself has a clique of size at least n/2
            if not normal_graph_has_large_clique:
                contains_large_clique, time_expired = (
                    has_clique_of_size(odd_extended_random_graph,nb_vertices/2,10*nb_vertices+600))

                if not contains_large_clique:
                # 1. Create the directory path object
                    if not time_expired: #is likely to save the same graph twice,
                        # but no fix needed since I will keep only one method in the end
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

            time_required_for_analysis = time.time() - graph_created_time
            print(f"Time needed to analyze:{time_required_for_analysis},"
                  f"nb_vertices:{nb_vertices}")
            total_analysis_time_using_core += time_required_for_analysis


        # cliques_apx = np.append(cliques_apx, average_minor/nb_trials) #for the plots
        # times_values = np.append(times_values, total_analysis_time/nb_trials)

        # Log the timing

        Title_string = "Computation_times.csv"  # Changed extension to .csv
        folder_path_time_logs = Path(f"Logs/{Title_string}")

        # Create the directory if it doesn't exist
        folder_path_time_logs.parent.mkdir(parents=True, exist_ok=True)

        # Define the data row
        data_row_with_core = [
            nb_vertices,
            round(total_creation_time / nb_trials, 3),
            round(total_analysis_time_using_core / nb_trials, 3),
            time_tag_for_log
        ]
        #will not be needed it the future
        # data_row_without_core = [
        #     nb_vertices,
        #     round(total_creation_time / nb_trials, 3),
        #     round(total_analysis_time_without_core / nb_trials, 3),
        #     False,
        #     time_tag_for_log
        # ]
        # Check if we need to write a header (if file is empty/new)
        file_exists = folder_path_time_logs.exists()

        with open(folder_path_time_logs, "a", newline="") as f:
            writer = csv.writer(f)

            # Write header only once
            if not file_exists:
                writer.writerow(["Vertices", "Avg Creation Time", "Avg Analysis Time", "Time of computation"])

            # Append the data
            writer.writerow(data_row_with_core)
            # writer.writerow(data_row_without_core)




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
