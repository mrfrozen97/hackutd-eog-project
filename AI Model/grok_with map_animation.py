# --------------------------------------------------------------
#  grok_perfect_matplotlib.py
#  → 3 witches + slopes.json + REALISTIC SPREAD + MATPLOTLIB ANIMATION
# --------------------------------------------------------------
import math, random, json, os
import numpy as np
import networkx as nx
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
# --------------------------------------------------------------
# 1. LOAD slopes.json
# --------------------------------------------------------------
with open("slopes.json") as f:
    SLOPE_DATA = json.load(f)

# --------------------------------------------------------------
# 2. ID mapping
# --------------------------------------------------------------
ID_MAP = {f"c{i}": f"cauldron_{i:03d}" for i in range(1, 13)}
ID_MAP["market"] = "market"

# --------------------------------------------------------------
# 3. Cauldrons + market (original tight coords + slight spread)
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

# --- Slight realistic spread (not a full circle) ---
SPREAD_X = 0.0012   # ~250m east-west
SPREAD_Y = 0.0009   # ~200m north-south

cauldrons = []
for i, c in enumerate(base_cauldrons):
    # Add small jitter based on index (looks natural)
    jitter_x = (i % 4 - 1.5) * SPREAD_X / 3
    jitter_y = (i // 4 - 1.5) * SPREAD_Y / 3
    cauldrons.append({
        "id": c["id"],
        "lat": c["lat"] + jitter_y,
        "lon": c["lon"] + jitter_x,
        "max_volume": c["max_volume"]
    })

# --------------------------------------------------------------
# 4. Graph (using slightly spread coords)
# --------------------------------------------------------------
def build_graph():
    G = nx.Graph()
    nodes = [c["id"] for c in cauldrons] + ["market"]
    for n in nodes: G.add_node(n)
    def c(n):
        if n == "market": return market["lat"], market["lon"]
        return next(x for x in cauldrons if x["id"] == n)["lat"], next(x for x in cauldrons if x["id"] == n)["lon"]
    for a, b in [(nodes[i], nodes[j]) for i in range(len(nodes)) for j in range(i+1, len(nodes))]:
        lat_a, lon_a = c(a)
        lat_b, lon_b = c(b)
        d = math.hypot(lat_b-lat_a, lon_b-lon_a)
        G.add_edge(a, b, weight=max(5, int(d*5000)))
    return G
G = build_graph()

# --------------------------------------------------------------
# 5. Q-agent
# --------------------------------------------------------------
class QAgent:
    def __init__(self, sz):
        self.q = np.random.uniform(-1, 1, (10,10,10,sz))
        self.mem = deque(maxlen=2000)
        self.eps = 1.0
    def _d(self, s): return tuple(min(int(x*9),9) for x in s)
    def act(self, s):
        if random.random() < self.eps: return random.randrange(self.q.shape[3])
        return int(np.argmax(self.q[self._d(s)]))
    def remember(self, s,a,r,s2,d): self.mem.append((s,a,r,s2,d))
    def replay(self):
        if len(self.mem) < 32: return
        for s,a,r,s2,d in random.sample(self.mem, 32):
            si, s2i = self._d(s), self._d(s2)
            target = r if d else r + 0.95*np.max(self.q[s2i])
            self.q[si][a] += 0.001 * (target - self.q[si][a])
        self.eps = max(0.01, self.eps*0.995)

# --------------------------------------------------------------
# 6. Environment
# --------------------------------------------------------------
class WitchEnv:
    def __init__(self, assigned):
        self.assigned = assigned
        self.nodes = assigned + ["market"]
        self.idx = {n:i for i,n in enumerate(self.nodes)}
        self.max_t, self.max_l, self.unload_t = 480, 2000, 15
        self.reset()
    def reset(self):
        self.t = self.load = 0.0
        self.pos = "market"
        self.vol = {c["id"]:0.0 for c in cauldrons}
        self.delivered = 0.0
        self.route = ["market"]
        return self._obs()
    def _obs(self):
        return np.array([self.idx[self.pos]/len(self.nodes),
                         min(self.t/self.max_t,1),
                         min(self.load/self.max_l,1)], dtype=np.float32)
    def _travel(self, to): return G[self.pos][to]["weight"] if self.pos != to else 0
    def _fill(self, cid): return SLOPE_DATA[ID_MAP[cid]]["fill_rate"] *1.3
    def _pour(self, cid): return SLOPE_DATA[ID_MAP[cid]]["pour_rate"]
    def step(self, a):
        nxt = self.nodes[a]; travel = self._travel(nxt)
        for cid in self.assigned:
            mv = next(c for c in cauldrons if c["id"]==cid)["max_volume"]
            self.vol[cid] = min(self.vol[cid] + self._fill(cid)*travel, mv)
        self.t += travel; r = -travel*0.1
        if nxt == "market":
            self.t += self.unload_t
            r += self.load*0.5 - self.unload_t*0.1
            self.delivered += self.load; self.load = 0.0
        else:
            avail = self.vol[nxt]; pour = self._pour(nxt)
            want = min(avail, self.max_l-self.load)
            coll_t = want/pour; take = min(avail, pour*coll_t)
            self.vol[nxt] -= take; self.load += take
            self.t += coll_t; r += take*0.2 - coll_t*0.1
        self.pos = nxt; self.route.append(nxt)
        return self._obs(), r, self.t >= self.max_t, {}

# --------------------------------------------------------------
# 7. Train / simulate
# --------------------------------------------------------------
def train_cluster(cl):
    env = WitchEnv(cl); ag = QAgent(len(env.nodes))
    for _ in range(400):
        s = env.reset()
        while True:
            a = ag.act(s); s2,r,d,_ = env.step(a)
            ag.remember(s,a,r,s2,d); s = s2
            if d: break
        ag.replay()
    return ag

def simulate_n_witches(n):
    ids = [c["id"] for c in cauldrons]; random.shuffle(ids)
    clusters = [ids[i::n] for i in range(n)]
    agents = [train_cluster(cl) for cl in clusters]
    envs = [WitchEnv(cl) for cl in clusters]
    states = [e.reset() for e in envs]
    routes = [["market"] for _ in envs]

    for _ in range(8000):
        done = True
        for i,(env,ag) in enumerate(zip(envs,agents)):
            if env.t >= env.max_t: continue
            done = False
            a = ag.act(states[i]); ns,_,d,_ = env.step(a)
            states[i] = ns; routes[i].append(env.pos)
            if d: env.t = env.max_t + 1
        if done: break

    total_vol = {cid:0.0 for cid in ids}
    total_delivered = 0.0
    for env in envs:
        for cid,v in env.vol.items(): total_vol[cid] += v
        total_delivered += env.delivered

    overflow = any(total_vol[cid] > next(c for c in cauldrons if c["id"]==cid)["max_volume"] for cid in total_vol)
    visited = set(); [visited.update(r) for r in routes]
    return not overflow and len(visited & set(ids)) == len(ids), routes, total_vol, total_delivered

def find_min():
    print("\nFinding minimum witches...")
    for n in range(1,13):
        print(f"  Trying {n} witch{'es' if n>1 else ''}...", end="")
        ok, routes, vols, delivered = simulate_n_witches(n)
        if ok:
            print(" SUCCESS")
            return n, routes, vols, delivered
        print(" failed")
    return None,None,None,None

# --------------------------------------------------------------
# 8. MATPLOTLIB ANIMATION (CLEAR, SMOOTH, NO HTML)
# --------------------------------------------------------------
def animate_matplotlib(n_witches, routes, volumes, delivered):
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor('#f0f0f0')
    ax.set_xlim(-97.138, -97.128)
    ax.set_ylim(33.210, 33.220)
    ax.set_title("Witch Routes (3 Witches)", fontsize=16, pad=20)
    # Plot cauldrons
    for c in cauldrons:
        ratio = volumes.get(c["id"], 0) / c["max_volume"]
        col = "red" if ratio > 0.9 else "orange" if ratio > 0.7 else "limegreen"
        size = 100 + ratio * 300
        ax.scatter(c["lon"], c["lat"], c=col, s=size, edgecolors='black', linewidth=1.5, zorder=5)
        ax.text(c["lon"], c["lat"], c["id"], ha='center', va='center',
                fontsize=9, color='white', weight='bold', zorder=6)

    # Market
    ax.scatter(market["lon"], market["lat"], c='black', s=400, marker='s', edgecolors='white', linewidth=2, zorder=5)
    ax.text(market["lon"], market["lat"], "MARKET", ha='center', va='center', color='white', weight='bold', fontsize=11)

    # Witch paths
    colors = ["magenta", "cyan", "yellow"]
    lines = [ax.plot([], [], color=colors[i], lw=3, alpha=0.9, label=f"Witch {i+1}")[0] for i in range(n_witches)]
    points = [ax.scatter([], [], c=colors[i], s=150, edgecolors='black', zorder=10) for i in range(n_witches)]

    max_frames = max(len(r) for r in routes)

    def update(frame):
        ax.set_title(f"Step {frame} | MIN WITCHES: {n_witches} | Delivered: {delivered:,.0f} L", fontsize=14)
        for i, route in enumerate(routes):
            path = route[:frame+1]
            lats, lons = [], []
            for node in path:
                if node == "market":
                    lats.append(market["lat"]); lons.append(market["lon"])
                else:
                    cc = next(x for x in cauldrons if x["id"] == node)
                    lats.append(cc["lat"]); lons.append(cc["lon"])
            lines[i].set_data(lons, lats)
            if path:
                points[i].set_offsets([[lons[-1], lats[-1]]])
        return lines + points
    ani = FuncAnimation(fig, update, frames=max_frames, interval=600, repeat=False, repeat_delay=5000)
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.show()

# --------------------------------------------------------------
# 9. MAIN
# --------------------------------------------------------------
if __name__ == "__main__":
    print("Using slopes.json fill/pour rates")
    n, routes, vols, delivered = find_min()
    if n:
        print(f"\nMINIMUM WITCHES: {n}")
        print(f"Total Delivered: {delivered:,.0f} L")
        print("All cauldrons visited (c1-c12)")
        animate_matplotlib(n, routes, vols, delivered)
    else:
        print("Failed")
