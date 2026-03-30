import pandas as pd
import glob
import os
import matplotlib.pyplot as plt
from .utils import get_file_path

def count_entries():
    data_location = get_file_path('odd_directory')
    files = glob.glob(f"{data_location}/*_Computation_times.csv")
    total_entries = 0
    for file in files:
        df = pd.read_csv(file)
        # Standardize column names just in case
        total_entries += df.count()
    return total_entries


def plot_list(nb_vertices):
    data_location = get_file_path('odd_directory')
    files = glob.glob(f"{data_location}/*_Computation_times.csv")
    point_list = []

    for file in files:
        df = pd.read_csv(file)

        # 1. Filter rows where 'Vertices' matches your input
        # 2. Select only the columns 'Parameter' and 'Probability'
        filtered_df = df[df['Vertices'] == nb_vertices][['Parameter', 'Probability']]

        # Only add to list if the result isn't empty
        if not filtered_df.empty:
            point_list.append(filtered_df)

    return point_list