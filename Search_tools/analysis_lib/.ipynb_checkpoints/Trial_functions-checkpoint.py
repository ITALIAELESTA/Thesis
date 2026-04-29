from .Candidate_analysis import *
from .Graph_creation_fct import *
from .Clique_search_fcts import *
import time
from .ExpEntry import *
from .utils import get_file_path
from .Solver import get_c4_induced_solver
from datetime import datetime
import gc
import psutil
"""
Add a function that takes a given graph, not just a random one (I already have it lol)
"""

def format_seconds(seconds):
    """
    Converts a float (seconds) into a string in HH:MM:SS format.
    """
    # Use divmod to get hours and the remaining seconds
    hours, remainder = divmod(int(seconds), 3600)

    # Use divmod again to get minutes and the final seconds
    minutes, seconds = divmod(remainder, 60)

    # Format as a string with leading zeros
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def find_counterexamples(nb_vertices, parameter_interval, proba_int,  time_limit, nb_trials=5, reverse=False):
    # ExperimentEntry.initialize_id()  #allows for the ID of the trials to start from the highest value of current trials
    try:
        computation_time_limit = time_limit(
            nb_vertices)  # allows to change the timit limit function outside the function
    except TypeError:
        computation_time_limit = time_limit

    
    print(f"Time limit : {format_seconds(computation_time_limit)}")

    if reverse:
        proba_interval = reversed(proba_int)
    else:
        proba_interval = proba_int
    
    for param in parameter_interval:
        for proba in proba_interval:
            print(f"Switched to {nb_vertices} vertices, parameter {param} and with probability {proba}")
            for trial in range(0, nb_trials):

                run_trial(nb_vertices, param, round(proba,3), computation_time_limit, trial)


def run_trial(nb_vertices, param, proba, computation_time_limit, trial_number=None):
    if trial_number is not None: print(f"Trial:{trial_number + 1}")

    time1 = time.time()
    random_graph = nx.complement(clear_H0(nb_vertices, param, proba))
    creation_time = round(time.time()-time1,3)
    print("Random graph : ok !")
    if nb_vertices%2==0:
        threshold_step = nb_vertices/4
    else:
        threshold_step = (nb_vertices+3)/4


    start = time.time()
    is_ctexample, exit_via_time_limit = has_large_clique(random_graph,
                                                        threshold=threshold_step, time_limit=computation_time_limit)
    # C4_solver = get_c4_induced_solver(random_graph,show_memory_used=False)
    # if computation_time_limit is not None:
    #     C4_solver.set("timeout", computation_time_limit*1000) #timeout considers second argument as milliseconds
    # result = C4_solver.check()
    ana_time = round(time.time() - start, 3)
    # del C4_solver
    # gc.collect()
    # if result == unsat:
    #     useless = True
    # else:
    #     useless = False
     # IF A GRAPH HAS A C4, IT DOES NOT TELL ANYTHING ABOUT THE GRAPH, ONLY IF IT IS C4 FREE, THEN THE GRAPH IS USELESS
    
    new_entry = ExperimentEntry(vertices=nb_vertices, need_odd=not is_ctexample,
                                    creation_time=creation_time,
                                    analysis_time=ana_time, parameter=param,
                                    probability=proba, time_expired=exit_via_time_limit, time_limit=computation_time_limit)
    new_entry.log()
    if not is_ctexample:
        # print(f"Odd extension required, creating odd extension, {datetime.now().strftime('%H:%M:%S')}")
        # time_start = time.time()
        # odd_extended_random_graph = odd_extension_graph(random_graph)
        # print(f"Odd extension : ok ! {datetime.now().strftime('%H:%M:%S')}")
        # graph_created_time = time.time()
        # graph_creation_duration = graph_created_time - time_start
        # # print(f"Time needed to create the odd extended graph:{round(graph_creation_duration, 4)}")
        # contains_large_clique, time_expired = (
        #     has_large_clique(odd_extended_random_graph, threshold=nb_vertices / 2, time_limit=computation_time_limit))

        # time_required_for_analysis = time.time() - graph_created_time

        # # print(f"Time needed to analyze:{round(time_required_for_analysis, 4)},{datetime.now().strftime('%H:%M:%S')}")
        
        # del odd_extended_random_graph
        # gc.collect()

        save_graph(random_graph, int(new_entry.id), save_into_candidate_folder=True)

    del random_graph
    del new_entry
    gc.collect()
    process = psutil.Process(os.getpid())
    print(f"Memory after trial: {process.memory_info().rss / 1024 / 1024:.2f} MB")

def save_graph(Graph, ID, save_into_candidate_folder=True):
    if not save_into_candidate_folder:
        folder_path = Path(get_file_path('Counterexamples'))
        print("FOUND A COUNTEREXAMPLE !!!!!!!!!!")
    else:
        folder_path = Path(get_file_path('Candidates'))
        # print("time expired, possible candidate")

    # 2. Create the folder if it doesn't exist
    folder_path.mkdir(parents=True, exist_ok=True)

    # 4. Construct the full file path
    file_name = f"{ID}.csv"
    full_path = folder_path / file_name

    # 5. Save the matrix
    matrix = nx.to_pandas_adjacency(Graph)
    matrix.to_csv(full_path, index=True)
    print(f"Saved: {full_path}")
    del Graph
    del matrix
    gc.collect()
