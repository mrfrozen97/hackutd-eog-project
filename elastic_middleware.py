import time
import requests
from elasticsearch import Elasticsearch

# === CONFIGURATION ===
API_URL = "https://hackutd2025.eog.systems/api/Data"  # Replace with your API endpoint
ELASTIC_HOST = "localhost"
ELASTIC_PORT = 9200
ELASTIC_INDEX = "api_data_index"  # New index name

# If authentication is needed, add http_auth=("user", "pass")
es = Elasticsearch(["http://localhost:9200"], http_auth=('elastic', 'W8ErCZGg'),)

# Create index with proper mapping based on swagger schema
def create_index(index_name):
    if not es.indices.exists(index=index_name):
        # Mapping based on HistoricalDataDto from swagger.json
        mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {
                        "type": "date",
                        "format": "strict_date_time"
                    },
                    "cauldron_levels": {
                        "properties": {
                            "cauldron_001": {"type": "double"},
                            "cauldron_002": {"type": "double"},
                            "cauldron_003": {"type": "double"},
                            "cauldron_004": {"type": "double"},
                            "cauldron_005": {"type": "double"},
                            "cauldron_006": {"type": "double"},
                            "cauldron_007": {"type": "double"},
                            "cauldron_008": {"type": "double"},
                            "cauldron_009": {"type": "double"},
                            "cauldron_010": {"type": "double"},
                            "cauldron_011": {"type": "double"},
                            "cauldron_012": {"type": "double"}
                        }
                    }
                }
            }
        }
        es.indices.create(index=index_name, body=mapping)
        print(f"Created index: {index_name} with proper mapping")
    else:
        print(f"Index already exists: {index_name}")

create_index(ELASTIC_INDEX)

# Main loop: fetch and push every 1 minute
def fetch_and_push():
    while True:
        try:
            response = requests.get(API_URL)
            response.raise_for_status()
            data = response.json()
            # If data is a list, index each item using 'timestamp' as the document ID
            if isinstance(data, list):
                pushed = 0
                for item in data:
                    if isinstance(item, dict) and "timestamp" in item:
                        es.index(index=ELASTIC_INDEX, id=item["timestamp"], document=item)
                        pushed += 1
                    elif isinstance(item, dict):
                        es.index(index=ELASTIC_INDEX, document=item)
                        pushed += 1
                    else:
                        es.index(index=ELASTIC_INDEX, document={"value": item})
                        pushed += 1
                print(f"Pushed {pushed} items at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            elif isinstance(data, dict):
                if "fields" in data and "timestamp" in data["fields"]:
                    es.index(index=ELASTIC_INDEX, id=data["fields"]["timestamp"], document=data)
                else:
                    es.index(index=ELASTIC_INDEX, document=data)
                print(f"Pushed 1 item at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                es.index(index=ELASTIC_INDEX, document={"value": data})
                print(f"Pushed 1 primitive item at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)  # Wait 1 minute

if __name__ == "__main__":
    fetch_and_push()
