import csv
import matplotlib.pyplot as plt
from collections import Counter

FILE_NAME = "session_data.csv"

def generate_report():
    timestamps = []
    statuses = []
    ear_values = []q
    posture_values = []

    # 1. READ THE RAW DATA
    try:
        with open(FILE_NAME, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                timestamps.append(row['Timestamp'])
                statuses.append(row['Status'])
                ear_values.append(float(row['EAR']))
                posture_values.append(float(row['Posture_Offset']))
    except FileNotFoundError:
        print("No data found! Run 'main.py' first to generate data.")
        return

    if not statuses:
        print("Data file is empty.")
        return

    # 2. CALCULATE STATISTICS
    total_samples = len(statuses)
    # Assuming 1 log per second (from our main.py logic)
    total_minutes = total_samples / 60.0 
    
    status_counts = Counter(statuses)
    
    print(f"\n--- SESSION REPORT ({total_minutes:.2f} Minutes) ---")
    for status, count in status_counts.items():
        minutes = count / 60.0
        print(f"{status}: {minutes:.2f} min ({count} samples)")

    # 3. GENERATE DIAGRAMS
    # We will create a figure with 2 charts: A Pie Chart and a Line Graph
    plt.figure(figsize=(12, 6))

    # CHART 1: Pie Chart (Distribution of Time)
    plt.subplot(1, 2, 1) # 1 row, 2 columns, position 1
    labels = status_counts.keys()
    sizes = status_counts.values()
    colors = []
    for label in labels:
        if "FOCUSED" in label: colors.append('green')
        elif "FATIGUE" in label: colors.append('red')
        elif "DISTRACTED" in label: colors.append('orange')
        elif "POSTURE" in label: colors.append('yellow')
        else: colors.append('gray')

    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Session Focus Distribution')

    # CHART 2: Line Graph (Fatigue & Posture over time)
    plt.subplot(1, 2, 2) # 1 row, 2 columns, position 2
    
    # We create a simple X-axis (0, 1, 2... seconds)
    x_axis = range(len(timestamps))
    
    # Plot Eye Openness (EAR)
    plt.plot(x_axis, ear_values, label='Eye Openness (EAR)', color='blue', alpha=0.6)
    # Plot Posture Offset
    plt.plot(x_axis, posture_values, label='Posture Offset', color='purple', alpha=0.6)
    
    # Draw the "Bad" threshold lines so you can see when you failed
    plt.axhline(y=0.22, color='r', linestyle='--', label='Fatigue Threshold')
    plt.axhline(y=0.20, color='y', linestyle='--', label='Posture Threshold')

    plt.xlabel('Time (Seconds)')
    plt.ylabel('Score')
    plt.title('Fatigue & Posture Trends')
    plt.legend()
    plt.grid(True)

    # 4. SHOW AND SAVE
    plt.tight_layout()
    plt.savefig('daily_report.png') # Saves the image automatically
    print("\nReport saved as 'daily_report.png'")
    plt.show() # Pops up the window

if __name__ == "__main__":
    generate_report()