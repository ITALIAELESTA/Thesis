import numpy as np
from Counterexamples_fcts import*
from Graph_creation_fct import*
import networkx as nx

def time_limit_fct(n):
    return 10*n+600

n = 60

find_counterexamples([0.2,0.3],[30,30] , 60,time_limit_fct,nb_trials=1)

