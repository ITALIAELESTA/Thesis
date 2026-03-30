# import pandas as pd
# import networkx as nx
from .Clique_search_fcts import *
from .Graph_creation_fct import *
from .utils import get_file_path
import datetime
from pathlib import Path
import glob

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



def Run_further_analysis(graph_id):
    target_directory = Path(get_file_path('Candidates'))
    graph_csv_filepath = Path(f"{target_directory}/{graph_id}.csv")
    G = csv_to_graph(graph_csv_filepath)
    if G is not None:
        threshold = G.number_of_nodes()/2
        print(f"{datetime.datetime.now().strftime('%H:%M:%S')} Creating the graph ...")
        G_odd = odd_extension_graph(G)
        print(f"{datetime.datetime.now().strftime('%H:%M:%S')} Graph created successfully, starting analysis...")
        not_a_counterexample,_ = has_large_clique(G_odd,threshold)
        if not_a_counterexample:
            # print("BEURH")
            destination_folder = Path(get_file_path('Garbage'))
            destination_folder.mkdir(parents=True, exist_ok=True)
            # Move the file
            file_destination = f"{destination_folder}/{graph_id}.csv"
        else:
            print("YES")
            destination_folder = Path(get_file_path('Counterexamples'))
            destination_folder.mkdir(parents=True, exist_ok=True)
            # Move the file
            file_destination = f"{destination_folder}/{graph_id}.csv"
        graph_csv_filepath.rename(file_destination)
        print(f"{datetime.datetime.now().strftime('%H:%M:%S')} File moved successfully to {file_destination}")






