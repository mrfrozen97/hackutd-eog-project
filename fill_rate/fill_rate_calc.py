import requests
import pandas as pd
import matplotlib.pyplot as plt

BASE_URL = "https://hackutd2025.eog.systems"

# Pull historical data
data = requests.get(f"{BASE_URL}/api/Data?start_date=0&end_date=2000000000").json()

# Convert JSON to DataFrame (flattened)
rows = []
for entry in data:
    timestamp = entry["timestamp"]
    for cid, level in entry["cauldron_levels"].items():
        rows.append([timestamp, cid, level])

df = pd.DataFrame(rows, columns=["timestamp", "cauldron_id", "level"])

# Convert timestamp and sort
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(by=["timestamp"])

# Filter only cauldron_001
df_1 = df[df['cauldron_id'] == "cauldron_001"]

# === Plot ===
plt.figure(figsize=(10,5))
plt.plot(df_1['timestamp'], df_1['level'], label="Cauldron 001", linewidth=2)

plt.title("Potion Level Over Time – Cauldron 001")
plt.xlabel("Time")
plt.ylabel("Level (Liters)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# for i in data:
#     print(i)

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
