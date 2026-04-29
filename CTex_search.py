import argparse
import numpy as np
import Search_tools.analysis_lib as al
from z3 import set_param

def main():
    set_param('parallel.enable', True)
    set_param('sat.threads', 3)
    set_param('sat.variable_decay', 1)
    parser = argparse.ArgumentParser(description="Run counterexample search.")
    
    # Define the arguments you want to change per instance
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--p_start", type=int, required=True, help="Start of parameters range")
    parser.add_argument("--p_end", type=int, required=True, help="End of parameters range")
    parser.add_argument("--prob_min", type=float, default=0.1)
    parser.add_argument("--prob_max", type=float, default=0.9)

    args = parser.parse_args()

    # Convert arguments to your variables
    n = args.n
    parameters = range(args.p_start, args.p_end)
    proba = np.linspace(args.prob_min, args.prob_max, 81)
    
    def time_limit(n):
        return 600
        
    nb_trials = 1

    # Run the library function
    al.find_counterexamples(n, parameters, proba, time_limit, nb_trials=nb_trials, reverse=True)

if __name__ == "__main__":
    main()