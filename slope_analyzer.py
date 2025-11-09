import requests
import pandas as pd
import numpy as np
from rdp import rdp
from datetime import date  # <-- 1. ADD THIS IMPORT

class SlopeAnalyzer:
    # ... (all the class code remains unchanged) ...
    # ... (SlopeAnalyzer.__init__)
    # ... (SlopeAnalyzer._simplify)
    # ... (SlopeAnalyzer._compute_slopes)
    # ... (SlopeAnalyzer.inflection_points)
    # ... (SlopeAnalyzer.average_positive_slope)
    # ... (SlopeAnalyzer.average_negative_slope)
    def __init__(self, timestamps, levels, epsilon=20):
        self.timestamps = np.array(timestamps)
        self.levels = np.array(levels, dtype=float)
        self.epsilon = epsilon
        self.simplified = None
        self.slopes = None
        self._simplify()
        self._compute_slopes()

    def _simplify(self):
        time_idx = np.arange(len(self.timestamps))
        points = np.column_stack((time_idx, self.levels))
        self.simplified = rdp(points, epsilon=self.epsilon)

    def _compute_slopes(self):
        slopes = []
        xs = self.simplified[:, 0].astype(int)
        ys = self.simplified[:, 1]
        for i in range(1, len(xs)):
            dt = xs[i] - xs[i-1]
            if dt <= 0: continue
            dy = ys[i] - ys[i-1]
            slope = dy / dt
            slopes.append(slope)
        self.slopes = slopes

    def inflection_points(self):
        xs = self.simplified[:, 0].astype(int)
        ys = self.simplified[:, 1]
        points = []
        for i in range(len(xs)):
            ts = self.timestamps[xs[i]]
            lvl = ys[i]
            points.append((ts, lvl))
        return points

    def average_positive_slope(self):
        pos = [s for s in self.slopes if s > 0]
        return sum(pos)/len(pos) if pos else 0

    def average_negative_slope(self):
        neg = [s for s in self.slopes if s < 0]
        return sum(neg)/len(neg) if neg else 0


def get_negative_intervals_ending_on(inflection_points, target_date, avg_growth_rate):
    """
    Finds negative slope intervals that end on a specific calendar date.
    """
    found_intervals = []
    
    if len(inflection_points) < 2:
        return found_intervals

    for i in range(len(inflection_points) - 1):
        start_time, start_value = inflection_points[i]
        end_time, end_value = inflection_points[i+1]
        
        is_negative_slope = end_value < start_value
        matches_target_date = end_time.date() == target_date
        
        if is_negative_slope and matches_target_date:
            time_taken = end_time - start_time
            drain_volume = (start_value - end_value) + time_taken.total_seconds() / 60 * avg_growth_rate
            
            found_intervals.append({
                "interval": (start_time, end_time),
                "end_point": (end_time, end_value),
                "duration": time_taken,
                "drain_volume": drain_volume
            })
            
    return found_intervals


# <-- 2. ADD THIS WRAPPER -->
if __name__ == "__main__":
    
    # This code will ONLY run when you execute this file directly
    # It will NOT run when you import it from another file
    
    BASE_URL = "https://hackutd2025.eog.systems"

    # Fetch full data
    data = requests.get(f"{BASE_URL}/api/Data?start_date=0&end_date=1762645088").json()

    # Load into DataFrame
    rows = []
    for entry in data:
        timestamp = entry["timestamp"]
        for cid, level in entry["cauldron_levels"].items():
            rows.append([timestamp, cid, level])

    df = pd.DataFrame(rows, columns=["timestamp", "cauldron_id", "level"])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by="timestamp")

    # Only Cauldron 001
    df_1 = df[df["cauldron_id"] == "cauldron_001"].sort_values(by="timestamp")

    an = SlopeAnalyzer(df_1["timestamp"], df_1["level"], epsilon=20)

    print(f"Average positive slope: {an.average_positive_slope():.3f} L/min")
    print(f"Average negative slope: {an.average_negative_slope():.3f} L/min")

    # --- You need to define the target_date here for this part to work ---
    #     (Using an example date from your ticket data)
    target_date = date(2025, 10, 30) 
    
    print(f"\n===== Drain Info with Volumes for {target_date} =====")
    drain_infos = get_negative_intervals_ending_on(an.inflection_points(), target_date, an.average_positive_slope())
    
    if not drain_infos:
        print("No drain events found for this date.")
    else:
        for info in drain_infos:
            volume = info["drain_volume"]
            print(f"  - Drain Volume: {volume:.2f} L, Duration: {info['duration']}")