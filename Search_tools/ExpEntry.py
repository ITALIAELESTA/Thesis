from pathlib import Path
import csv
import os
import glob
import pandas as pd
from datetime import datetime
from .utils import get_file_path


class ExperimentEntry:
    _id_counter = 1
    id_string = 'id'
    odd_log_dir = Path(get_file_path('odd_directory'))
    non_odd_log_dir = Path(get_file_path('non_odd_directory'))
    def __init__(self, need_odd=False, vertices=None, creation_time=None, analysis_time=None,
                 parameter=None, probability=None, time_expired=None,time_limit=None):
        if need_odd:
            self.id = self._get_next_cluster_id()
        else:
            self.id = None
        self.relevant = need_odd
        self.vertices = vertices
        self.creation_time = creation_time
        self.analysis_time = analysis_time
        self.parameter = parameter
        self.probability = probability
        self.time_expired = time_expired
        self.daystamp = datetime.now().strftime("%d_%m_%Y")
        self.timestamp = datetime.now().strftime('%H:%M:%S')
        self.time_limit = time_limit

    @staticmethod
    def _get_next_cluster_id():
        # Create a hidden directory to store "ticket" files
        ticket_dir = Path(get_file_path('Tickets'))
        ticket_dir.mkdir(parents=True, exist_ok=True)

        # 1. Look at existing tickets to find the current high-water mark
        existing_tickets = [int(f) for f in os.listdir(ticket_dir) if f.isdigit()]
        next_id = max(existing_tickets) + 1 if existing_tickets else 1

        # 2. Try to "claim" this ID by creating an empty file
        while True:
            try:
                # 'x' mode means "exclusive creation" - it fails if file exists
                ticket_path = ticket_dir / str(next_id)
                with open(ticket_path, "x") as f:
                    pass
                    # If we get here, we successfully claimed the ID
                return next_id
            except FileExistsError:
                # Someone else grabbed this ID in the last millisecond!
                # Increment and try the next one.
                next_id += 1

    @classmethod
    def initialize_id(cls):

        pattern = os.path.join(cls.odd_log_dir, "*_Computation_times.csv")
        files = glob.glob(pattern)

        target_file = None

        if files:
            # 2. Sort files by modification time (most recent first)
            # This is safer than parsing dates from filenames
            files.sort(key=os.path.getmtime, reverse=True)
            target_file = files[0]
        if target_file:
            try:
                df = pd.read_csv(target_file)
                if not df.empty:
                    # Logic: Max ID + 1
                    cls._id_counter = df[cls.id_string].max() + 1
                    print(f"Initialized id to {cls._id_counter} from {target_file}")
                    # print(f"{today_file}")
            except Exception as e:
                print(f"Found file {target_file} but couldn't read it: {e}")
        else:
            print("No recent files found. Starting ID at 1.")

    def log(self):
        headers = [
            type(self).id_string, "Vertices", "Parameter", "Probability", "Creation Time",
            "Analysis Time", "Timestamp", "Exit via Timeout", "Time Limit"
        ]

        data_row = [self.id, self.vertices, self.parameter, self.probability,
                    self.creation_time, self.analysis_time,
                    self.timestamp, self.time_expired,
                    f"{self.time_limit}s"
        ]


        if self.relevant:
            log_dir = type(self).odd_log_dir
            file_path = log_dir / f"{self.daystamp}_Computation_times.csv"

        else:
            log_dir = type(self).non_odd_log_dir
            file_path = log_dir / f"{self.daystamp}_OddExt_not_req_Computation_times.csv"
        # if self.relevant:
        #     log_dir = Path(f"Logs/Required_odd_ext")
        #     file_path = log_dir / f"{self.daystamp}_Computation_times.csv"
        # else:
        #     log_dir = Path(f"Logs/Fast_computation")
        #     file_path = log_dir / f"{self.daystamp}_OddExt_not_req_Computation_times.csv"

        log_dir.mkdir(parents=True, exist_ok=True)
        file_is_there = file_path.exists()
        with open(file_path, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_is_there:
                writer.writerow(headers)
            writer.writerow(data_row)
        print(f"New data entry created in :{file_path} with id :{self.id}")

