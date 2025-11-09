from elasticsearch import Elasticsearch
import requests
import time

# === CONFIGURATION ===
ELASTIC_HOST = "localhost"
ELASTIC_PORT = 9200
ELASTIC_INDEX = "geo_points_index"  # Node index
MARKET_INDEX = "geo_point_market_index"  # Market index
EDGE_INDEX = "geo_edges_index"      # Edge index
API_BASE = "https://hackutd2025.eog.systems"

es = Elasticsearch([f"http://{ELASTIC_HOST}:{ELASTIC_PORT}"], http_auth=('elastic', 'W8ErCZGg'))

# Create index with geo_point mapping for nodes
def create_geo_index(index_name):
    if not es.indices.exists(index=index_name):
        mapping = {
            "mappings": {
                "properties": {
                    "geo": {"type": "geo_point"},
                    "name": {"type": "keyword"},
                    "type": {"type": "keyword"},
                    "id": {"type": "keyword"}
                }
            }
        }
        es.indices.create(index=index_name, body=mapping)
        print(f"Created geo index: {index_name}")
    else:
        print(f"Geo index already exists: {index_name}")

# Create index with geo_shape mapping for edges
def create_edge_index(index_name):
    if not es.indices.exists(index=index_name):
        mapping = {
            "mappings": {
                "properties": {
                    "line": {"type": "geo_shape"},
                    "from": {"type": "keyword"},
                    "to": {"type": "keyword"},
                    "travel_time_minutes": {"type": "integer"}
                }
            }
        }
        es.indices.create(index=index_name, body=mapping)
        print(f"Created edge index: {index_name}")
    else:
        print(f"Edge index already exists: {index_name}")

create_geo_index(ELASTIC_INDEX)
create_geo_index(MARKET_INDEX)
create_edge_index(EDGE_INDEX)

# Fetch and index geo points from cauldrons, market, couriers
def fetch_and_push_geo_points():
    while True:
        try:
            # Cauldrons
            cauldron_resp = requests.get(f"{API_BASE}/api/Information/cauldrons")
            cauldrons = cauldron_resp.json()
            for c in cauldrons:
                if "latitude" in c and "longitude" in c:
                    doc = {
                        "geo": {"lat": c["latitude"], "lon": c["longitude"]},
                        "name": c.get("name", c.get("id", "cauldron")),
                        "type": "cauldron",
                        "id": c.get("id")
                    }
                    es.index(index=ELASTIC_INDEX, id=f"cauldron_{doc['id']}", document=doc)
            # Market
            market_resp = requests.get(f"{API_BASE}/api/Information/market")
            market = market_resp.json()
            if "latitude" in market and "longitude" in market:
                doc = {
                    "geo": {"lat": market["latitude"], "lon": market["longitude"]},
                    "name": market.get("name", "market"),
                    "type": "market",
                    "id": market.get("id")
                }
                es.index(index=MARKET_INDEX, id=f"market_{doc['id']}", document=doc)
            # Couriers (no geo, but can add if available)
            courier_resp = requests.get(f"{API_BASE}/api/Information/couriers")
            couriers = courier_resp.json()
            for courier in couriers:
                if "latitude" in courier and "longitude" in courier:
                    doc = {
                        "geo": {"lat": courier["latitude"], "lon": courier["longitude"]},
                        "name": courier.get("name", courier.get("courier_id", "courier")),
                        "type": "courier",
                        "id": courier.get("courier_id")
                    }
                    es.index(index=ELASTIC_INDEX, id=f"courier_{doc['id']}", document=doc)
            print(f"Geo points indexed at {time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Build node lookup for geo coordinates
            node_lookup = {}
            res = es.search(index=ELASTIC_INDEX, body={"query": {"match_all": {}}}, size=1000)
            for doc in res["hits"]["hits"]:
                node_lookup[doc["_source"]["id"]] = doc["_source"]["geo"]
            
            # Also include market node
            market_res = es.search(index=MARKET_INDEX, body={"query": {"match_all": {}}}, size=1000)
            for doc in market_res["hits"]["hits"]:
                node_lookup[doc["_source"]["id"]] = doc["_source"]["geo"]

            # Fetch and index edges
            network_resp = requests.get(f"{API_BASE}/api/Information/network")
            network = network_resp.json()
            edges = network.get("edges", [])
            for edge in edges:
                from_id = edge.get("from")
                to_id = edge.get("to")
                from_geo = node_lookup.get(from_id)
                to_geo = node_lookup.get(to_id)
                if from_geo and to_geo:
                    edge_doc = {
                        "from": from_id,
                        "to": to_id,
                        "travel_time_minutes": edge.get("travel_time_minutes"),
                        "line": {
                            "type": "linestring",
                            "coordinates": [
                                [from_geo["lon"], from_geo["lat"]],
                                [to_geo["lon"], to_geo["lat"]]
                            ]
                        }
                    }
                    es.index(index=EDGE_INDEX, document=edge_doc)
            print(f"Edges indexed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    fetch_and_push_geo_points()
import time
import requests
from elasticsearch import Elasticsearch

# === CONFIGURATION ===
ELASTIC_HOST = "localhost"
ELASTIC_PORT = 9200
ELASTIC_INDEX = "geo_points_index"  # New index for geo points
API_BASE = "https://hackutd2025.eog.systems"

es = Elasticsearch([f"http://{ELASTIC_HOST}:{ELASTIC_PORT}"], http_auth=('elastic', 'W8ErCZGg'))

# Create index with geo_point mapping

def create_geo_index(index_name):
    if not es.indices.exists(index=index_name):
        mapping = {
            "mappings": {
                "properties": {
                    "geo": {"type": "geo_point"},
                    "name": {"type": "keyword"},
                    "type": {"type": "keyword"}
                }
            }
        }
        es.indices.create(index=index_name, body=mapping)
        print(f"Created geo index: {index_name}")
    else:
        print(f"Geo index already exists: {index_name}")

create_geo_index(ELASTIC_INDEX)

# Fetch and index geo points from cauldrons, market, couriers

def fetch_and_push_geo_points():
    try:
        # Cauldrons
        cauldron_resp = requests.get(f"{API_BASE}/api/Information/cauldrons")
        cauldrons = cauldron_resp.json()
        for c in cauldrons:
            if "latitude" in c and "longitude" in c:
                doc = {
                    "geo": {"lat": c["latitude"], "lon": c["longitude"]},
                    "name": c.get("name", c.get("id", "cauldron")),
                    "type": "cauldron",
                    "id": c.get("id")
                }
                es.index(index=ELASTIC_INDEX, id=f"cauldron_{doc['id']}", document=doc)
        # Market
        market_resp = requests.get(f"{API_BASE}/api/Information/market")
        market = market_resp.json()
        if "latitude" in market and "longitude" in market:
            doc = {
                "geo": {"lat": market["latitude"], "lon": market["longitude"]},
                "name": market.get("name", "market"),
                "type": "market",
                "id": market.get("id")
            }
            es.index(index=ELASTIC_INDEX, id=f"market_{doc['id']}", document=doc)
        # Couriers (no geo, but can add if available)
        courier_resp = requests.get(f"{API_BASE}/api/Information/couriers")
        couriers = courier_resp.json()
        for courier in couriers:
            # If courier has geo info, add it
            if "latitude" in courier and "longitude" in courier:
                doc = {
                    "geo": {"lat": courier["latitude"], "lon": courier["longitude"]},
                    "name": courier.get("name", courier.get("courier_id", "courier")),
                    "type": "courier",
                    "id": courier.get("courier_id")
                }
                es.index(index=ELASTIC_INDEX, id=f"courier_{doc['id']}", document=doc)
        print(f"Geo points indexed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_push_geo_points()
