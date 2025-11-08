import requests
import pandas as pd

BASE_URL = "https://hackutd2025.eog.systems"

# 1. Get cauldron information (max capacities)
info = requests.get(f"{BASE_URL}/api/Information/cauldrons").json()
max_volumes = {c['id']: c['max_volume'] for c in info}

# 2. Pull historical level data (large range)
# You can change start/end timestamps if needed
data = requests.get(f"{BASE_URL}/api/Data?start_date=0&end_date=2000000000").json()

# Convert to DataFrame for easy analysis
records = []
for row in data:
    t = row["timestamp"]
    for cid, level in row["cauldron_levels"].items():
        records.append([t, cid, level])

df = pd.DataFrame(records, columns=["timestamp", "cauldron_id", "level"])

# Ensure timestamps ordered
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(by=["cauldron_id", "timestamp"])

# Compute per-minute fill rate: Δvolume / Δtime
fill_rates = {}

for cid in df['cauldron_id'].unique():
    temp = df[df['cauldron_id'] == cid].copy()
    temp['delta'] = temp['level'].diff()

    # average change per minute
    avg_rate = temp['delta'].mean()
    fill_rates[cid] = avg_rate

# Print results nicely
print("=== Fill Rates (liters per minute) ===")
for cid, rate in fill_rates.items():
    print(f"{cid} : {rate:.3f} L/min   (Max capacity = {max_volumes[cid]})")
