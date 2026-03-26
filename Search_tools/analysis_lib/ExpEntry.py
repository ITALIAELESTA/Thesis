from pathlib import Path
import csv
import os
import pandas as pd
from datetime import datetime, timedelta
from .utils import get_file_path


class ExperimentEntry:
    _id_counter = 1
    id_string = 'id'
    odd_log_dir = Path(get_file_path('odd_directory'))
    non_odd_log_dir = Path(get_file_path('non_odd_directory'))
    def __init__(self, for_odd=True, vertices=None, creation_time=None, analysis_time=None,
                 parameter=None, probability=None, time_expired=None,time_limit=None):
        if for_odd:
            self.id = ExperimentEntry._id_counter
            ExperimentEntry._id_counter += 1
        else:
            self.id = None
        self.relevant = for_odd
        self.vertices = vertices
        self.creation_time = creation_time
        self.analysis_time = analysis_time
        self.parameter = parameter
        self.probability = probability
        self.time_expired = time_expired
        self.daystamp = datetime.now().strftime("%d_%m_%Y")
        self.timestamp = datetime.now().strftime('%H:%M:%S')
        self.time_limit = time_limit

    @classmethod
    def initialize_id(cls):
        # 1. Define date strings
        today_str = datetime.now().strftime("%d_%m_%Y")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%d_%m_%Y")


        today_file = f"{cls.odd_log_dir}/{today_str}_Computation_times.csv"
        yesterday_file = f"{cls.odd_log_dir}/{yesterday_str}_Computation_times.csv"

        # 2. Check Today first, then Yesterday
        target_file = None
        if os.path.exists(today_file):
            target_file = today_file

        elif os.path.exists(yesterday_file):
            target_file = yesterday_file
            print("From yesterday")
        # 3. If a file was found, grab the last ID
        if target_file:
            try:
                df = pd.read_csv(target_file)
                if not df.empty:
                    # Logic: Max ID + 1
                    cls._id_counter = df[cls.id_string].max() + 1
                    print(f"Initialized id to {cls._id_counter} from {target_file}")
                    print(f"{today_file}")
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

