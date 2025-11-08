import requests
import pandas as pd
import matplotlib.pyplot as plt

BASE_URL = "https://hackutd2025.eog.systems"

# Fetch historical data
data = requests.get(f"{BASE_URL}/api/Data?start_date=0&end_date=2000000000").json()

# Convert JSON to DataFrame
rows = []
for entry in data:
    timestamp = entry["timestamp"]
    for cid, level in entry["cauldron_levels"].items():
        rows.append([timestamp, cid, level])

df = pd.DataFrame(rows, columns=["timestamp", "cauldron_id", "level"])
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(by=["timestamp"])

# === Plot all cauldrons ===
plt.figure(figsize=(12,6))

unique_ids = df['cauldron_id'].unique()
for cid in unique_ids:
    df_temp = df[df['cauldron_id'] == cid]
    plt.plot(df_temp['timestamp'], df_temp['level'], label=cid)

plt.title("Potion Levels Over Time – All Cauldrons")
plt.xlabel("Time")
plt.ylabel("Level (Liters)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()


# === Compute Average Fill Rate for Each Cauldron ===
fill_rates = {}

for cid in unique_ids:
    df_temp = df[df['cauldron_id'] == cid].sort_values(by="timestamp")
    df_temp["diff"] = df_temp["level"].diff()  # change per minute

    # Positive slopes only (when filling)
    positive = df_temp[df_temp["diff"] > 0]["diff"]

    if len(positive) > 0:
        fill_rates[cid] = positive.mean()
    else:
        fill_rates[cid] = 0

print("\n=== Average Fill Rates (Liters per Minute) ===")
for c, r in fill_rates.items():
    print(f"{c}: {r:.3f}")
