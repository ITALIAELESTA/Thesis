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
