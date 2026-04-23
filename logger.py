import csv
import time
import os
from datetime import datetime

# File where data will be saved
FILE_NAME = "session_data.csv"

def init_db():
    """Creates the CSV file with headers if it doesn't exist."""
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Headers: Time, Status, Eye_Openness, Posture_Score
            writer.writerow(["Timestamp", "Status", "EAR", "Posture_Offset"])
            print(f"Created new log file: {FILE_NAME}")

def log_data(status, ear, posture_offset):
    """Writes a single row of data to the file."""
    # We only log meaningful data, rounded to 2 decimal places to save space
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    with open(FILE_NAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, status, f"{ear:.2f}", f"{posture_offset:.2f}"])