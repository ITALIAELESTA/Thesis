#!/bin/bash
#SBATCH --job-name=Cand_Search      # A name to identify your job
# #SBATCH --output=Logs/prints/%A_%a_OUTPUT.out
# #SBATCH --error=Logs/errors/%A_%a_ERROR.err
#SBATCH --time=96:00:00             # Strictly limit to 96 hours
#SBATCH --ntasks=1                # Number of instances to run
#SBATCH --cpus-per-task=3         # Adjust if your script uses multi-threading
#SBATCH --mem-per-cpu=2G                   # Amount of RAM needed (e.g., 4 Gigabytes)

# Load your python environment if you use conda or modules
#module load python/3.10 

#SBATCH --array=0-100%2  # Runs 9 instances of this script
export PYTHONUNBUFFERED=1
# This ensures Python looks in your personal '--user' folder
export PYTHONUSERBASE=$HOME/.local
export PATH=$HOME/.local/bin:$PATH
# Calculate a different start parameter for each task
# Instance 0 gets 100, Instance 1 gets 110, etc.
START_P=$(( 80 + (SLURM_ARRAY_TASK_ID * 2) ))
END_P=$(( START_P + 2 ))

srun python3 CTex_search.py --p_start $START_P --p_end $END_P 
# --task_id $SLURM_ARRAY_TASK_ID