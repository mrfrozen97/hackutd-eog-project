"""
FastAPI backend for witch routing simulation
Exposes simulation results as JSON API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import math
import random
import json
import os
import sys
from datetime import datetime
import numpy as np
import networkx as nx
from collections import deque

# Add parent directory to path to import slopes.json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Witch Routes API")

# CORS configuration for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------
# Load slopes.json
# --------------------------------------------------------------
SLOPE_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "AI Model", "slopes.json")
try:
    with open(SLOPE_DATA_PATH) as f:
        SLOPE_DATA = json.load(f)
except FileNotFoundError:
    print(f"Warning: slopes.json not found at {SLOPE_DATA_PATH}")
    SLOPE_DATA = {}

# --------------------------------------------------------------
# ID mapping
# --------------------------------------------------------------
ID_MAP = {f"c{i}": f"cauldron_{i:03d}" for i in range(1, 13)}
ID_MAP["market"] = "market"

# --------------------------------------------------------------
# Cauldrons + market with realistic spread
# --------------------------------------------------------------
base_cauldrons = [
    {"id": "c1",  "lat": 33.2148, "lon": -97.1331, "max_volume": 1000},
    {"id": "c2",  "lat": 33.2155, "lon": -97.1325, "max_volume":  800},
    {"id": "c3",  "lat": 33.2142, "lon": -97.1338, "max_volume": 1200},
    {"id": "c4",  "lat": 33.2160, "lon": -97.1318, "max_volume":  750},
    {"id": "c5",  "lat": 33.2135, "lon": -97.1345, "max_volume":  900},
    {"id": "c6",  "lat": 33.2165, "lon": -97.1310, "max_volume":  650},
    {"id": "c7",  "lat": 33.2128, "lon": -97.1352, "max_volume": 1100},
    {"id": "c8",  "lat": 33.2170, "lon": -97.1305, "max_volume":  700},
    {"id": "c9",  "lat": 33.2120, "lon": -97.1360, "max_volume":  950},
    {"id": "c10", "lat": 33.2175, "lon": -97.1300, "max_volume":  850},
    {"id": "c11", "lat": 33.2115, "lon": -97.1368, "max_volume": 1050},
    {"id": "c12", "lat": 33.2180, "lon": -97.1295, "max_volume":  600},
]
market = {"id": "market", "lat": 33.215, "lon": -97.133}

SPREAD_X = 0.0012
SPREAD_Y = 0.0009

cauldrons = []
for i, c in enumerate(base_cauldrons):
    jitter_x = (i % 4 - 1.5) * SPREAD_X / 3
    jitter_y = (i // 4 - 1.5) * SPREAD_Y / 3
    cauldrons.append({
        "id": c["id"],
        "lat": c["lat"] + jitter_y,
        "lon": c["lon"] + jitter_x,
        "max_volume": c["max_volume"]
    })

# --------------------------------------------------------------
# Graph
# --------------------------------------------------------------
def build_graph():
    G = nx.Graph()
    nodes = [c["id"] for c in cauldrons] + ["market"]
    for n in nodes:
        G.add_node(n)
    
    def get_coords(n):
        if n == "market":
            return market["lat"], market["lon"]
        return next(x for x in cauldrons if x["id"] == n)["lat"], next(x for x in cauldrons if x["id"] == n)["lon"]
    
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            lat_a, lon_a = get_coords(a)
            lat_b, lon_b = get_coords(b)
            d = math.hypot(lat_b - lat_a, lon_b - lon_a)
            G.add_edge(a, b, weight=max(5, int(d * 5000)))
    return G

G = build_graph()

# --------------------------------------------------------------
# Q-agent
# --------------------------------------------------------------
class QAgent:
    def __init__(self, sz):
        self.q = np.random.uniform(-1, 1, (10, 10, 10, sz))
        self.mem = deque(maxlen=2000)
        self.eps = 1.0
    
    def _d(self, s):
        return tuple(min(int(x * 9), 9) for x in s)
    
    def act(self, s):
        if random.random() < self.eps:
            return random.randrange(self.q.shape[3])
        return int(np.argmax(self.q[self._d(s)]))
    
    def remember(self, s, a, r, s2, d):
        self.mem.append((s, a, r, s2, d))
    
    def replay(self):
        if len(self.mem) < 32:
            return
        for s, a, r, s2, d in random.sample(self.mem, 32):
            si, s2i = self._d(s), self._d(s2)
            target = r if d else r + 0.95 * np.max(self.q[s2i])
            self.q[si][a] += 0.001 * (target - self.q[si][a])
        self.eps = max(0.01, self.eps * 0.995)

# --------------------------------------------------------------
# Environment
# --------------------------------------------------------------
class WitchEnv:
    def __init__(self, assigned):
        self.assigned = assigned
        self.nodes = assigned + ["market"]
        self.idx = {n: i for i, n in enumerate(self.nodes)}
        self.max_t, self.max_l, self.unload_t = 480, 2000, 15
        self.reset()
    
    def reset(self):
        self.t = self.load = 0.0
        self.pos = "market"
        self.vol = {c["id"]: 0.0 for c in cauldrons}
        self.delivered = 0.0
        self.route = ["market"]
        return self._obs()
    
    def _obs(self):
        return np.array([
            self.idx[self.pos] / len(self.nodes),
            min(self.t / self.max_t, 1),
            min(self.load / self.max_l, 1)
        ], dtype=np.float32)
    
    def _travel(self, to):
        return G[self.pos][to]["weight"] if self.pos != to else 0
    
    def _fill(self, cid):
        return SLOPE_DATA.get(ID_MAP[cid], {}).get("fill_rate", 1.0)
    
    def _pour(self, cid):
        return SLOPE_DATA.get(ID_MAP[cid], {}).get("pour_rate", 1.0)
    
    def step(self, a):
        nxt = self.nodes[a]
        travel = self._travel(nxt)
        
        # All cauldrons fill up during travel time
        for cid in self.assigned:
            mv = next(c for c in cauldrons if c["id"] == cid)["max_volume"]
            self.vol[cid] = min(self.vol[cid] + self._fill(cid) * travel, mv)
        
        self.t += travel
        r = -travel * 0.1
        
        if nxt == "market":
            # ONLY at market: unload/dump collected potion
            self.t += self.unload_t
            r += self.load * 0.5 - self.unload_t * 0.1
            self.delivered += self.load
            self.load = 0.0  # Empty the witch's tank
        else:
            # At cauldrons: ONLY collect/pickup potion (cannot dump here)
            avail = self.vol[nxt]
            pour = self._pour(nxt)
            want = min(avail, self.max_l - self.load)
            coll_t = want / pour if pour > 0 else 0
            take = min(avail, pour * coll_t)
            self.vol[nxt] -= take  # Remove from cauldron
            self.load += take      # Add to witch's tank
            self.t += coll_t
            r += take * 0.2 - coll_t * 0.1
        
        self.pos = nxt
        self.route.append(nxt)
        return self._obs(), r, self.t >= self.max_t, {}

# --------------------------------------------------------------
# Train / simulate
# --------------------------------------------------------------
def train_cluster(cl):
    env = WitchEnv(cl)
    ag = QAgent(len(env.nodes))
    for _ in range(400):
        s = env.reset()
        while True:
            a = ag.act(s)
            s2, r, d, _ = env.step(a)
            ag.remember(s, a, r, s2, d)
            s = s2
            if d:
                break
        ag.replay()
    return ag

def simulate_n_witches(n):
    ids = [c["id"] for c in cauldrons]
    random.shuffle(ids)
    clusters = [ids[i::n] for i in range(n)]
    agents = [train_cluster(cl) for cl in clusters]
    envs = [WitchEnv(cl) for cl in clusters]
    states = [e.reset() for e in envs]
    routes = [["market"] for _ in envs]
    
    # Track detailed schedule for each witch
    schedules = [[] for _ in envs]
    
    for _ in range(8000):
        done = True
        for i, (env, ag) in enumerate(zip(envs, agents)):
            if env.t >= env.max_t:
                continue
            done = False
            
            # Record current state before action
            prev_pos = env.pos
            prev_time = env.t
            prev_load = env.load
            
            a = ag.act(states[i])
            ns, _, d, _ = env.step(a)
            states[i] = ns
            routes[i].append(env.pos)
            
            # Record schedule entry
            schedules[i].append({
                "from": prev_pos,
                "to": env.pos,
                "start_time": prev_time,
                "end_time": env.t,
                "duration": env.t - prev_time,
                "load_before": prev_load,
                "load_after": env.load,
                "action": "unload" if env.pos == "market" else "collect"
            })
            
            if d:
                env.t = env.max_t + 1
        if done:
            break
    
    total_vol = {cid: 0.0 for cid in ids}
    total_delivered = 0.0
    for env in envs:
        for cid, v in env.vol.items():
            total_vol[cid] += v
        total_delivered += env.delivered
    
    overflow = any(
        total_vol[cid] > next(c for c in cauldrons if c["id"] == cid)["max_volume"]
        for cid in total_vol
    )
    visited = set()
    for r in routes:
        visited.update(r)
    
    return (
        not overflow and len(visited & set(ids)) == len(ids),
        routes,
        total_vol,
        total_delivered,
        schedules
    )

def find_min():
    """Find minimum number of witches needed (minimum 3)"""
    for n in range(3, 100):  # Start from 3 witches minimum
        ok, routes, vols, delivered, schedules = simulate_n_witches(n)
        if ok:
            return n, routes, vols, delivered, schedules
    return None, None, None, None, None

# --------------------------------------------------------------
# API Endpoints
# --------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Witch Routes API", "endpoint": "/api/witch-routes"}

@app.get("/api/witch-routes")
def get_witch_routes():
    """
    Calculate optimal witch routes and return simulation data
    Returns:
        {
            "n_witches": int,
            "routes": list of lists (witch paths),
            "volumes": dict (final cauldron volumes),
            "delivered": float (total delivered to market),
            "cauldrons": list (cauldron positions and metadata),
            "market": dict (market position),
            "schedules": list of daily schedules for each witch
        }
    """
    try:
        n, routes, vols, delivered, schedules = find_min()
        
        if n is None:
            raise HTTPException(status_code=500, detail="Failed to find optimal route")
        
        # Convert routes to coordinate paths for frontend
        route_coords = []
        for route in routes:
            path = []
            for node in route:
                if node == "market":
                    path.append({
                        "id": "market",
                        "lat": market["lat"],
                        "lon": market["lon"]
                    })
                else:
                    c = next(x for x in cauldrons if x["id"] == node)
                    path.append({
                        "id": c["id"],
                        "lat": c["lat"],
                        "lon": c["lon"]
                    })
            route_coords.append(path)
        
        # Format schedules with just the path for each witch
        formatted_schedules = []
        for witch_idx, schedule in enumerate(schedules):
            # Extract just the path (sequence of locations)
            path = []
            if schedule:
                path.append(schedule[0]["from"])  # Starting location
                for activity in schedule:
                    path.append(activity["to"])  # Add each destination
            
            # Remove consecutive duplicates
            deduplicated_path = []
            for location in path:
                if not deduplicated_path or deduplicated_path[-1] != location:
                    deduplicated_path.append(location)
            
            witch_schedule = {
                "witch_id": witch_idx + 1,
                "path": deduplicated_path
            }
            
            formatted_schedules.append(witch_schedule)
        
        # Save schedules to JSON file
        schedule_output = {
            "timestamp": datetime.now().isoformat(),
            "n_witches": n,
            "total_delivered": delivered,
            "schedules": formatted_schedules
        }
        
        schedule_file_path = os.path.join(os.path.dirname(__file__), "witch_schedules.json")
        try:
            with open(schedule_file_path, 'w') as f:
                json.dump(schedule_output, f, indent=2)
            print(f"Schedule saved to {schedule_file_path}")
        except Exception as e:
            print(f"Warning: Could not save schedule file: {e}")
        
        # Add volume ratio to cauldrons
        cauldrons_with_status = []
        for c in cauldrons:
            vol = vols.get(c["id"], 0)
            ratio = vol / c["max_volume"]
            cauldrons_with_status.append({
                **c,
                "current_volume": vol,
                "ratio": ratio,
                "status": "critical" if ratio > 0.9 else "warning" if ratio > 0.7 else "ok"
            })
        
        return {
            "n_witches": n,
            "routes": route_coords,
            "volumes": vols,
            "delivered": delivered,
            "cauldrons": cauldrons_with_status,
            "market": market,
            "schedules": formatted_schedules
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
