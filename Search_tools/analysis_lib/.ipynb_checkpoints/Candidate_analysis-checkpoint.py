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

set_param('sat.threads', 8)
set_param('parallel.enable', True)
set_param('sat.variable_decay', 0.9)
def print_graph_info(target_id):
    # Get all csv files in the Logs folder
    target_directory = Path(get_file_path('odd_directory'))
    files = glob.glob(f"{target_directory}/*_Computation_times.csv")
    found = False
    for file in files:
        df = pd.read_csv(file)
        # Standardize column names just in case
        df.columns = df.columns.str.strip().str.lower()

        match = df[df['id'] == target_id]

        if not match.empty:
            print(f"Found ID {target_id} in file: {file}")
            print(match.iloc[0].to_dict())
            found = True

    if not found:
        print(f"No entry saved under ID {target_id}")

    return None

# print_graph_info(120)

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

def csv_to_graph_using_id(graph_id):
    target_directory = Path(get_file_path('Candidates'))
    graph_csv_filepath = Path(f"{target_directory}/{graph_id}.csv")
    return csv_to_graph(graph_csv_filepath)

# def run_further_analysis(graph_id):#scrap it, it is WAAAAAAAAY slower than SAT solver
#     target_directory = Path(get_file_path('Candidates'))
#     graph_csv_filepath = Path(f"{target_directory}/{graph_id}.csv")
#     G = csv_to_graph_using_id(graph_id)
#     if G is not None:
#         threshold = G.number_of_nodes()/2
#         print(f"{datetime.datetime.now().strftime('%H:%M:%S')} Creating the graph ...")
#         G_odd = odd_extension_graph(G)
#         print(f"{datetime.datetime.now().strftime('%H:%M:%S')} Graph created successfully, starting analysis...")
#         not_a_counterexample,_ = has_large_clique(G_odd,threshold)
#         if not_a_counterexample:
#             print("BEURH")
#             destination_folder = Path(get_file_path('Garbage'))
#         else:
#             print("YES")
#             destination_folder = Path(get_file_path('Counterexamples'))
#
#         move_file(graph_csv_filepath, destination_folder)

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


def analyze_candidates():
    target = Path(get_file_path('Candidates'))
    files = glob.glob(f"{target}/*.csv")
    for file in files:
        # Convert the string ID to an integer
        id_int = Path(file).stem
        print(f"Currently analyzing graph: {id_int}")
        print_graph_info(id_int)
        graph = csv_to_graph(file)
        start_time = time.time()
        print("Starting with SAT")
        result = further_analysis_with_SAT(graph)
        diff_time = round(time.time() - start_time, 4)
        sat_folder = Path(get_file_path('Sat_computation'))
        file_path = sat_folder / f"Sat_duration.csv"
        sat_folder.mkdir(parents=True, exist_ok=True)
        file_is_there = file_path.exists()
        data_row = [id_int,diff_time]
        headers = ['id','Sat analysis time']
        with open(file_path, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_is_there:
                writer.writerow(headers)
            writer.writerow(data_row)
        if result == sat:
            destination_folder = Path(get_file_path('Garbage'))
        elif result == unsat:
            destination_folder = Path(get_file_path('Counterexamples'))
        try:
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



