import requests
import pandas as pd
import numpy as np
from rdp import rdp

class SlopeAnalyzer:
    def __init__(self, timestamps, levels, epsilon=20):
        """
        timestamps: list/array of datetime or numeric time values
        levels: list/array of corresponding tank levels
        epsilon: RDP simplification tolerance (higher = smoother polygon)
        """
        self.timestamps = np.array(timestamps)
        self.levels = np.array(levels, dtype=float)
        self.epsilon = epsilon

        self.simplified = None
        self.slopes = None

        self._simplify()
        self._compute_slopes()

    def _simplify(self):
        """Apply RDP simplification to raw time-series"""
        time_idx = np.arange(len(self.timestamps))
        points = np.column_stack((time_idx, self.levels))
        self.simplified = rdp(points, epsilon=self.epsilon)

    def _compute_slopes(self):
        """Compute slopes between simplified polygon segments"""
        slopes = []
        xs = self.simplified[:, 0].astype(int)
        ys = self.simplified[:, 1]

        for i in range(1, len(xs)):
            dt = xs[i] - xs[i-1]  # minutes between samples
            if dt <= 0:
                continue
            dy = ys[i] - ys[i-1]
            slope = dy / dt  # liters per minute
            slopes.append(slope)

        self.slopes = slopes

    # ---------- NEW METHOD ----------
    def inflection_points(self):
        """
        Returns list of key inflection points as:
        [(timestamp, level), (timestamp, level), ...]
        """
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




# -----------------------------------------------------------
# ✅ Your normal code to fetch data and filter one cauldron
# -----------------------------------------------------------

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

# ✅ Only Cauldron 001
df_1 = df[df["cauldron_id"] == "cauldron_001"].sort_values(by="timestamp")



# -----------------------------------------------------------
# ✅ Use our slope analyzer class on cauldron_001
# -----------------------------------------------------------

an = SlopeAnalyzer(df_1["timestamp"], df_1["level"], epsilon=20)

print("===== Cauldron 001 Slope Summary =====")
print(f"Average positive slope: {an.average_positive_slope():.3f} L/min")
print(f"Average negative slope: {an.average_negative_slope():.3f} L/min")

print(an.inflection_points())

def get_negative_intervals_ending_on(inflection_points, target_date):
    """
    Finds negative slope intervals that end on a specific calendar date.
    """
    found_intervals = []
    
    if len(inflection_points) < 2:
        return found_intervals

    for i in range(len(inflection_points) - 1):
        start_time, start_value = inflection_points[i]
        end_time, end_value = inflection_points[i+1]
        
        # --- Check 1: Is the slope negative? ---
        is_negative_slope = end_value < start_value
        
        # --- Check 2: Does the segment end on our target date? ---
        matches_target_date = end_time.date() == target_date
        
        if is_negative_slope and matches_target_date:
            
            time_taken = end_time - start_time
            
            # --- NEW: Calculate the drain volume ---
            # (The starting level minus the ending level)
            drain_volume = start_value - end_value
            
            found_intervals.append({
                "interval": (start_time, end_time),
                "end_point": (end_time, end_value),
                "duration": time_taken,
                "drain_volume": drain_volume  # <-- Added this
            })
            
    return found_intervals

print("===== Drain Info with Volumes =====")
drain_infos = get_negative_intervals_ending_on(an.inflection_points(), target_date)
for info in drain_infos:
    interval = info["interval"]
    end_point = info["end_point"]
    duration = info["duration"]
    volume = info["drain_volume"]
    print(f"Interval: {interval}, End Point: {end_point}, Duration: {duration}, Drain Volume: {volume:.2f} L")
