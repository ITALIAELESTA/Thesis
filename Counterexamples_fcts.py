import datetime

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from pathlib import Path
import csv
# from Scraped_functions import*
from Graph_creation_fct import*
from Clique_search_fcts import *
import time
from ExpEntry import*


"""
Add a function that takes a given graph, not just a random one (I already have it lol)
"""

def find_counterexamples(proba_interval,param_interval, nb_vertices, time_limit_fct, nb_trials=5):
    ExperimentEntry.initialize_id() #allows for the ID of the trials to start from the highest value of current trials
    proba_interval = np.linspace(proba_interval[0],proba_interval[1],10)
    parameter_interval = range(param_interval[0],param_interval[1]+1)
    # print(proba_interval)
    computation_time_limit = time_limit_fct(nb_vertices)  # allows to change the timit limit function outside the function
    for proba in proba_interval: #add a for loop for parameter_m
        for param in parameter_interval:
            print(f"Switched to {nb_vertices} vertices, parameter {param} and with probability {proba}")
            for trials in range(0,nb_trials):
                run_trial(nb_vertices, param, proba,computation_time_limit,trials)


        """
        Add a new way to identify which entry in the csv corresponds to which graph,
        and save the odd extended graph, then put into the website
        """

def run_trial(nb_vertices, param, proba,computation_time_limit,trial_number=None):
    if not trial_number: print(f"Trial:{trial_number + 1}")
    # print(computation_time_limit)
    random_graph = nx.complement(clear_H0(nb_vertices, param, proba))
    # print("Random graph : ok !")

    normal_graph_has_large_clique, _ = has_large_clique(random_graph,
                                                        threshold=nb_vertices / 2, time_limit=computation_time_limit)

    if not normal_graph_has_large_clique:
        print(f"Odd extension required, creating odd extension, {datetime.now().strftime('%H:%M:%S')}")
        time_start = time.time()
        odd_extended_random_graph = odd_extension_graph(random_graph)
        print(f"Odd extension : ok !,{datetime.now().strftime('%H:%M:%S')}")
        graph_created_time = time.time()
        graph_creation_duration = graph_created_time - time_start
        print(f"Time needed to create the odd extended graph:{round(graph_creation_duration,4)}")
        contains_large_clique, time_expired = (
            has_large_clique(odd_extended_random_graph, threshold=nb_vertices / 2, time_limit=computation_time_limit))

        time_required_for_analysis = time.time() - graph_created_time

        print(f"Time needed to analyze:{round(time_required_for_analysis,4)},{datetime.now().strftime('%H:%M:%S')}")

        new_entry = ExperimentEntry(vertices=nb_vertices,for_odd=True, id_needs_increasing=True and time_expired, creation_time=round(graph_creation_duration,4),
                                    analysis_time=round(time_required_for_analysis,4), parameter=param,
                                    probability=proba, time_expired=time_expired,time_limit=computation_time_limit)
        new_entry.log()
        if not contains_large_clique:
            save_graph(random_graph, int(new_entry.id), save_into_candidate_folder=time_expired)
    else:
        print(f"Graph has large clique already")
        new_entry = ExperimentEntry(vertices=nb_vertices,for_odd=False, id_needs_increasing=False, parameter=param,
                                    probability=proba)
        new_entry.log()

def save_graph(Graph,ID,save_into_candidate_folder=True):
    if not save_into_candidate_folder:
        folder_path = Path(f"Counterexamples")
        print("FOUND A COUNTEREXAMPLE !!!!!!!!!!")
    else:
        folder_path = Path(f"Candidates_w_ID")
        print("time expired, possible candidate")

    # 2. Create the folder if it doesn't exist
    folder_path.mkdir(parents=True, exist_ok=True)


    # 4. Construct the full file path
    file_name = f"{ID}.csv"
    full_path = folder_path / file_name

    # 5. Save the matrix
    matrix = nx.to_pandas_adjacency(Graph)
    matrix.to_csv(full_path, index=True)
    print(f"Saved: {full_path}")