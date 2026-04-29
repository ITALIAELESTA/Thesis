import argparse
import numpy as np
import Search_tools.analysis_lib as al
from z3 import set_param

def main():
    set_param('parallel.enable', True)
    set_param('sat.threads', 1)
    set_param('sat.variable_decay', 1)
    parser = argparse.ArgumentParser(description="Run counterexample search.")
    
    # Define the arguments you want to change per instance
    parser.add_argument("--n_start", type=int, default=100)
    parser.add_argument("--n_end", type=int, default=200)
    parser.add_argument("--p_start", type=int, required=True, help="Start of parameters range")
    parser.add_argument("--p_end", type=int, required=True, help="End of parameters range")
    parser.add_argument("--prob_min", type=float, default=0.8)
    parser.add_argument("--prob_max", type=float, default=0.9)

    args = parser.parse_args()

    # Convert arguments to your variables
    n_start = args.n_start
    n_end = args.n_end
    parameters = range(args.p_start, args.p_end)
    proba = np.linspace(args.prob_min, args.prob_max, 11)
    
    def time_limit(n):
        return 1800
        
    nb_trials = 1

    # Run the library function
    for n in range(n_start, n_end):
        al.find_counterexamples(n, parameters, proba, time_limit, nb_trials=nb_trials, reverse=True)

if __name__ == "__main__":
    main()