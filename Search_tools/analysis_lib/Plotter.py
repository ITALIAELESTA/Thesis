import pandas as pd
import glob
import matplotlib.pyplot as plt
from .utils import get_file_path
import seaborn as sns


def plot_scatter_data(nb_vertices):
    good_list, bad_list = plot_list(nb_vertices)

    if not good_list and not bad_list:
        print("No data found.")
        return

    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")

    # Plot Good Data (Blue)
    if good_list:
        combined_good = pd.concat(good_list, ignore_index=True)
        sns.scatterplot(
            data=combined_good,
            x='Parameter',
            y='Probability',
            color='blue',
            label='Success',
            alpha=0.6
        )

    # Plot Bad Data (Red)
    if bad_list:
        combined_bad = pd.concat(bad_list, ignore_index=True)
        sns.scatterplot(
            data=combined_bad,
            x='Parameter',
            y='Probability',
            color='red',
            label='Timeout',
            alpha=0.6
        )

        # 4. Force X-axis to show every integer
        # First, get all data to find the range
        all_data = pd.concat(good_list + bad_list, ignore_index=True)
        x_min = int(all_data['Parameter'].min())
        x_max = int(all_data['Parameter'].max())

        # Set ticks from min to max (inclusive)
        plt.xticks(range(x_min, x_max + 1))

        # 5. Add labels and title
        plt.title(f'Probability vs Parameter (Vertices: {nb_vertices})')
        plt.xlabel('Parameter')
        plt.ylabel('Probability')
        plt.legend()
        plt.show()


def plot_list(nb_vertices):
    data_location = get_file_path('odd_directory')
    files = glob.glob(f"{data_location}/*_Computation_times.csv")
    good_list = []
    bad_list = []

    for file in files:
        df = pd.read_csv(file)

        # Use ~ for "NOT" and & for "AND"
        # Assuming 'Exit via Timeout' is True for "bad" results
        mask_base = (df['Vertices'] == nb_vertices)

        positive_df = df[mask_base & (df['Exit via Timeout'])][['Parameter', 'Probability']]
        negative_df = df[mask_base & (~df['Exit via Timeout'])][['Parameter', 'Probability']]

        if not negative_df.empty:
            bad_list.append(negative_df)
        if not positive_df.empty:
            good_list.append(positive_df)# Assuming timeout is "good"

    return good_list, bad_list


def count_entries():
    data_location = get_file_path('odd_directory')
    files = glob.glob(f"{data_location}/*_Computation_times.csv")
    total_entries = 0
    for file in files:
        df = pd.read_csv(file)
        # Standardize column names just in case
        total_entries += df.count()
    return total_entries