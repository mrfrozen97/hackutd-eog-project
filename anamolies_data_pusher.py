import time
import json
import os
from elasticsearch import Elasticsearch
from datetime import datetime

# === CONFIGURATION (UPDATED for Elastic Cloud) ===
# 1. Cloud Endpoint URL (No change needed here, just the variable name)
ELASTIC_CLOUD_URL = "https://my-elasticsearch-project-e32a9b.es.us-central1.gcp.elastic.cloud/"
ELASTIC_API_KEY = "RjRmblpwb0I0aUN3aFd6cjEyZ1E6d2hRRVBHX0V5MnI3NW1sZXZ0eEpqUQ=="
# 3. Index name
ELASTIC_INDEX_ANOMALIES = "anomalies_data_index"

JSON_FILE = "anomalies.json"
PUSH_INTERVAL_SECONDS = 30

# === ELASTICSEARCH SETUP (FIXED to use hosts) ===
try:
    # --- FIX APPLIED HERE: Using hosts=[URL] instead of cloud_id=URL ---
    es = Elasticsearch(
        hosts=[ELASTIC_CLOUD_URL], # Pass the URL in the standard hosts list
        api_key=ELASTIC_API_KEY,   # Use the API key for authentication
        request_timeout=30
    )

    if not es.ping():
        # Raise a specific error if connection fails
        raise ConnectionError(f"Failed to connect to Elastic Cloud at {ELASTIC_CLOUD_URL}. Check API Key/Network.")

    print(f"Successfully connected to Elastic Cloud at {ELASTIC_CLOUD_URL}.")
except ConnectionError as ce:
    print(f"CRITICAL ELASTIC ERROR: Connection failed: {ce}")
    # The error message should now be more accurate if ping fails
    exit()
except Exception as e:
    # If you still get errors here, they are genuine connection/authentication issues,
    # not Cloud ID format errors.
    print(f"CRITICAL ELASTIC ERROR: An unexpected error occurred during connection: {e}")
    exit()

# ... (The rest of your code remains the same and should now work)

# Create index if it doesn't exist
# Create index if it doesn't exist
def create_index(index_name):
    """Creates the target index with a timestamp mapping for the time field."""
    mapping = {
        "properties": {
            # CORRECTED: Changed HH:MM:ss to HH:mm:ss
            "time": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
            "drain_end_time": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
            "date": {"type": "date", "format": "yyyy-MM-dd"}
        }
    }
    # ... (rest of the creation logic)
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, mappings=mapping)
        print(f"Created index: {index_name}")
    else:
        print(f"Index already exists: {index_name}")


def flatten_anomalies_and_matches(data):
    """
    Flattens the nested JSON data (anomalies and matches) into a single list
    of documents ready for Elasticsearch indexing.
    """
    all_documents = []

    # --- 1. Flatten ANOMALIES ---
    for date_str, cauldrons in data.get("anomalies", {}).items():
        for cid, events in cauldrons.items():
            for event in events:
                # Add metadata for searchability
                event['cauldron_id'] = cid
                event['date'] = date_str
                event['data_source'] = "ANOMALY"
                all_documents.append(event)

    # --- 2. Flatten MATCHES ---
    for date_str, cauldrons in data.get("matches", {}).items():
        for cid, matches in cauldrons.items():
            for match in matches:
                # Add metadata for searchability
                match['cauldron_id'] = cid
                match['date'] = date_str
                match['data_source'] = "MATCH"
                all_documents.append(match)

    return all_documents


# Main loop: load, flatten, and push
def push_anomalies_data():
    while True:
        try:
            # Check if the file exists
            if not os.path.exists(JSON_FILE):
                print(f"WARNING: JSON file not found at {JSON_FILE}. Skipping push.")
                time.sleep(PUSH_INTERVAL_SECONDS)
                continue

            print(f"\n--- Starting push at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

            # 1. Load data from the anomalies.json file
            with open(JSON_FILE, 'r') as f:
                json_data = json.load(f)

            # 2. Flatten the nested structure
            documents_to_push = flatten_anomalies_and_matches(json_data)

            if not documents_to_push:
                print("JSON file is empty or contains no data. Nothing to push.")
                time.sleep(PUSH_INTERVAL_SECONDS)
                continue

            # 3. Push data to Elasticsearch
            pushed_count = 0
            for doc in documents_to_push:
                # Index document (ES generates the ID)
                es.index(index=ELASTIC_INDEX_ANOMALIES, document=doc)
                pushed_count += 1

            print(f"Successfully pushed {pushed_count} documents to {ELASTIC_INDEX_ANOMALIES}.")

        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {JSON_FILE}. Check file integrity.")
        except Exception as e:
            print(f"An unexpected error occurred during the push: {e}")

        # 4. Wait for the defined interval
        time.sleep(PUSH_INTERVAL_SECONDS)

if __name__ == "__main__":
    push_anomalies_data()
