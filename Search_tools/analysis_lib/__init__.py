from .Candidate_analysis import *
from .Clique_search_fcts import *
from .ExpEntry import *
from .Graph_creation_fct import *
from .Trial_functions import *
from .utils import get_file_path
from .Plotter import *


import sys

# This injects the libraries into the 'main' workspace (your Notebook)
if 'ipykernel' in sys.modules:
    import numpy as np
    import pandas as pd
    import networkx as nx

    # Get a reference to the notebook's global namespace
    import __main__

    __main__.np = np
    __main__.pd = pd
    __main__.nx = nx