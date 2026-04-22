import pandas as pd
import networkx as nx
from networkx.algorithms import threshold
import numpy as np
from .Clique_search_fcts import *
from .Graph_creation_fct import *
from .utils import get_file_path,move_file
from .Solver import *
import datetime
from pathlib import Path
import glob
import gc
import csv
from pprint import pprint
import os

metadata_folder = Path(get_file_path('odd_directory'))
garbage_folder = Path(get_file_path('Garbage'))
candidate_folder = Path(get_file_path('Candidates'))

def get_timeout_graph_ids(metadata_path=metadata_folder, id_col='id', vertex_col='Vertices', timeout_col='Exit via Timeout'):
    search_pattern = os.path.join(metadata_path, "*.csv")
    files = glob.glob(search_pattern)
    if not files:
        return []

    df_list = []
    for f in files:
        try:
            # We load everything as object/string first to prevent weird type conversions
            df_list.append(pd.read_csv(f, usecols=[id_col, vertex_col, timeout_col]))
        except ValueError:
            continue

    if not df_list:
        return []

    master_df = pd.concat(df_list, ignore_index=True)

    # --- THE FIX: ROBUST BOOLEAN CONVERSION ---
    # This converts "True", "true", 1, and True all into the same actual Boolean True
    def force_boolean(value):
        if isinstance(value, bool):
            return value
        str_val = str(value).strip().lower()
        return str_val in ['True', '1', 't', 'y', 'yes']

    master_df[timeout_col] = master_df[timeout_col].apply(force_boolean)
    # ------------------------------------------

    # Filter for True (the timeouts), then sort
    sorted_df = (
        master_df[master_df[timeout_col] == True]
        .drop_duplicates(subset=[id_col])
        .dropna(subset=[vertex_col])
        .sort_values(by=vertex_col)
    )
    # print(f"Total rows: {len(master_df)} | Rows after timeout filter: {len(sorted_df)}")
    return sorted_df[id_col].tolist()

def print_graph_info(target_id):
    # Get all csv files in the Logs folder
    target_directory = Path(get_file_path('odd_directory'))
    files = glob.glob(f"{target_directory}/*_Computation_times.csv")
    found = False
    try:
        int_target = int(target_id)
        for file in files:

            df = pd.read_csv(file)
            # Standardize column names just in case
            df.columns = df.columns.str.strip().str.lower()

            match = df[df['id'] == int_target]

            if not match.empty:
                print(f"Found ID {target_id} in file: {file}")
                pprint(match.iloc[0].to_dict(), sort_dicts=False)
                found = True
    except ValueError:
        pass

    if not found:
        print(f"No entry saved under ID {target_id}")

    return None

def csv_to_graph(csv_string):
    try:
        # 1. Load the CSV
        df = pd.read_csv(csv_string, index_col=0)

        # 2. Convert column names to integers to match the index
        df.columns = df.columns.astype(int)

        # 3. Create the graph
        G = nx.from_pandas_adjacency(df)
        return G
    except FileNotFoundError:
        print(f"No graph saved under {csv_string}")
        return None

def csv_to_graph_using_id(graph_id):
    target_directory = Path(get_file_path('Candidates'))
    graph_csv_filepath = Path(f"{target_directory}/{graph_id}.csv")
    graph = csv_to_graph(graph_csv_filepath)
    return graph

def run_further_analysis(graph_id, time_limit=None):#scrap it, it is WAAAAAAAAY slower than SAT solver
    target_directory = Path(get_file_path('Candidates'))
    graph_csv_filepath = Path(f"{target_directory}/{graph_id}.csv")
    G = csv_to_graph_using_id(graph_id)
    if G is not None:
        threshold = G.number_of_nodes()/2
        print(f"{datetime.datetime.now().strftime('%H:%M:%S')} Creating the graph ...")
        G_odd = odd_extension_graph(G)
        print(f"{datetime.datetime.now().strftime('%H:%M:%S')} Graph created successfully, starting analysis...")
        not_a_counterexample,exit_through_limit = has_large_clique(G_odd,threshold,time_limit=time_limit)
        if not_a_counterexample:
            print("BEURH")
            destination_folder = Path(get_file_path('Garbage'))
        if not exit_through_limit:
            print("YES")
            destination_folder = Path(get_file_path('Counterexamples'))

        try:
            move_file(graph_csv_filepath, destination_folder)
        except NameError:
            pass

def further_analysis_with_SAT(graph):
    threshold = int(np.ceil(graph.number_of_nodes()/2))
    s = odd_minor_solver(graph,threshold)
    print("Solver ready")
    result = s.check()

    if result ==sat:
        print("SAT found")
    elif result == unsat:
        print("UNSAT")

    # Delete the reference to the solver
    del s
    # Force Python to actually clear the deleted objects from RAM
    gc.collect()

    return result

def analyze_candidates_better():
    #get the list of IDs
    sorted_ids = get_timeout_graph_ids()
    print(sorted_ids)
    #set up the logging
    sat_folder = Path(get_file_path('Sat_computation'))
    sat_folder.mkdir(parents=True, exist_ok=True)
    file_path = sat_folder / f"Sat_duration.csv"
    file_is_there = file_path.exists()

    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
    if not file_is_there:
        headers = ['id','Sat analysis time']
        writer.writerow(headers)
    for graph_id in sorted_ids:
        graph = csv_to_graph_using_id(graph_id)
        # print(graph)
        if graph is not None:
            print(f"Currently analyzing graph: {graph_id}")
            print_graph_info(graph_id)
            start_time = time.time()
            print("Starting with SAT")
            result = further_analysis_with_SAT(graph)
            diff_time = round(time.time() - start_time, 4)
            data_row = [graph_id, diff_time]
            writer.writerow(data_row)
            if result == sat:
                destination_folder = Path(get_file_path('Garbage'))
            elif result == unsat:
                destination_folder = Path(get_file_path('Counterexamples'))
            try:
                file = f"{candidate_folder}/{graph_id}.csv"
                move_file(file, destination_folder)
            except NameError:
                pass

def increments(graph,start_step=0):
    threshold = int(np.ceil(graph.number_of_nodes() / 2))

    for i in range(start_step,threshold + 1):
        print(f"--- Testing k = {i} ---")

        # 1. Create solver inside the loop
        s = odd_minor_solver(graph, i)
        print("Solver ready")
        # 2. Use set_param for global parallel settings if .set() fails


        start = time.time()
        result = s.check()

        duration = round(time.time() - start, 4)

        if result == sat:
            print(f"k={i}: SAT found in {duration}s")
            # print_model_from_solver(s) # Call your printer here
        elif result == unsat:
            print(f"k={i}: UNSAT in {duration}s")
        else:
            print(f"k={i}: UNKNOWN in {duration}s")

        with open("sah.txt", 'a') as f:
            f.write(f"{i}: {duration} seconds\n")

        # 3. Explicitly delete solver and collect garbage to free RAM
        del s

        gc.collect()

def quick_analysis(graph,time_limit=None):
    n = len(graph.nodes())
    if n%2 == 0:
        threshold_step = n/4
    else:
        threshold_step = (n+3)/4

    cliqueN_over4,_ = has_large_clique(graph,threshold_step,time_limit=time_limit)
    #returns true if the graph has a clique of size more than n/4
    return cliqueN_over4

def quick_analysis_all_candidates(time_limit=None):
    target = Path(get_file_path('Candidates'))
    files = glob.glob(f"{target}/*.csv")
    for file in files:
        graph = csv_to_graph(file)
        if graph is not None:
            no_use = quick_analysis(graph,time_limit)
            if no_use:
                move_file(file, garbage_folder)

def has_C4(graph,time_limit=None):
    solver = get_c4_induced_solver(graph)
    if time_limit is not None:
        solver.set("timeout", time_limit*1000) #timeout considers second argument as milliseconds
    result = solver.check()
    # Delete the reference to the solver

    if result == sat:
        answer = True
    elif result == unsat:
        answer = False
    else:
        answer = None
    del solver
    # Force Python to actually clear the deleted objects from RAM
    gc.collect()
    return answer


def C4_analysis_all_candidates(time_limit=None):
    target = Path(get_file_path('Candidates'))
    files = glob.glob(f"{target}/*.csv")
    for file in files:
        graph = csv_to_graph(file)
        print(graph)
        if graph is not None:
            no_use = has_C4(graph,time_limit)
            if no_use:
                move_file(file, garbage_folder)