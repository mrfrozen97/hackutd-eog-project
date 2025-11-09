# simple_dqn_animation.py
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx
import random
from collections import deque

# --------------------------
# Cauldron data
# --------------------------
cauldrons = [
    {"id": "c1", "lat": 33.2148, "lon": -97.1331, "max_volume": 1000},
    {"id": "c2", "lat": 33.2155, "lon": -97.1325, "max_volume": 800},
    {"id": "c3", "lat": 33.2142, "lon": -97.1338, "max_volume": 1200},
    {"id": "c4", "lat": 33.2160, "lon": -97.1318, "max_volume": 750},
    {"id": "c5", "lat": 33.2135, "lon": -97.1345, "max_volume": 900},
    {"id": "c6", "lat": 33.2165, "lon": -97.1310, "max_volume": 650},
    {"id": "c7", "lat": 33.2128, "lon": -97.1352, "max_volume": 1100},
    {"id": "c8", "lat": 33.2170, "lon": -97.1305, "max_volume": 700},
    {"id": "c9", "lat": 33.2120, "lon": -97.1360, "max_volume": 950},
    {"id": "c10", "lat": 33.2175, "lon": -97.1300, "max_volume": 850},
    {"id": "c11", "lat": 33.2115, "lon": -97.1368, "max_volume": 1050},
    {"id": "c12", "lat": 33.2180, "lon": -97.1295, "max_volume": 600},
]

market = {"id": "market", "lat": 33.215, "lon": -97.133}

# --------------------------
# Create graph
# --------------------------
def build_graph():
    G = nx.Graph()
    nodes = [c["id"] for c in cauldrons] + ["market"]
    for n in nodes:
        G.add_node(n)

    def coords(n):
        if n == "market":
            return (market["lat"], market["lon"])
        c = next(x for x in cauldrons if x["id"] == n)
        return (c["lat"], c["lon"])

    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if i < j:
                lat1, lon1 = coords(n1)
                lat2, lon2 = coords(n2)
                dist = math.sqrt((lat2-lat1)**2 + (lon2-lon1)**2)
                travel = max(5, int(dist * 5000))
                G.add_edge(n1, n2, weight=travel)
    return G

G = build_graph()
all_nodes = [c["id"] for c in cauldrons] + ["market"]

# --------------------------
# Simple DQN Implementation
# --------------------------
class SimpleDQN:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001

        # Simple Q-table instead of neural network
        self.q_table = np.random.uniform(-1, 1, (10, 10, 10, action_size))

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.random() <= self.epsilon:
            return random.randrange(self.action_size)

        # Discretize state
        state_idx = self._discretize_state(state)
        return np.argmax(self.q_table[state_idx])

    def _discretize_state(self, state):
        # Convert continuous state to discrete indices
        return (
            min(int(state[0] * 9), 9),  # position
            min(int(state[1] * 9), 9),  # time
            min(int(state[2] * 9), 9)   # load
        )

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return

        batch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in batch:
            state_idx = self._discretize_state(state)
            next_state_idx = self._discretize_state(next_state)

            target = reward
            if not done:
                target = reward + self.gamma * np.max(self.q_table[next_state_idx])

            current_q = self.q_table[state_idx][action]
            self.q_table[state_idx][action] += self.learning_rate * (target - current_q)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# --------------------------
# Environment
# --------------------------
class WitchEnv:
    def __init__(self):
        self.cauldrons = cauldrons
        self.market = market
        self.nodes = all_nodes
        self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}

        self.fill_rate = 0.25  # L/min per cauldron
        self.drain_rate = 0.5  # L/min collection rate
        self.max_time = 480    # 8-hour day

        # Observation: [position, time, load]
        self.observation_space = (3,)
        self.action_space = len(self.nodes)

        self.reset()

    def reset(self):
        self.current_time = 0
        self.witch_pos = "market"
        self.witch_load = 0
        self.volumes = {c["id"]: 0 for c in self.cauldrons}
        self.total_delivered = 0
        self.overflow_penalty = 0
        self.route = ["market"]
        return self._get_obs()

    def _get_obs(self):
        pos_idx = self.node_to_idx[self.witch_pos] / len(self.nodes)
        time_norm = min(self.current_time / self.max_time, 1.0)
        load_norm = min(self.witch_load / 2000, 1.0)
        return np.array([pos_idx, time_norm, load_norm])

    def _get_travel_time(self, from_node, to_node):
        if from_node == to_node:
            return 0
        return G[from_node][to_node]["weight"]

    def step(self, action):
        next_node = self.nodes[action]

        # Travel
        travel_time = self._get_travel_time(self.witch_pos, next_node)

        # Fill cauldrons during travel
        for c in self.cauldrons:
            self.volumes[c["id"]] = min(
                self.volumes[c["id"]] + self.fill_rate * travel_time,
                c["max_volume"]
            )

        self.current_time += travel_time
        reward = -travel_time * 0.1

        # Handle action
        if next_node == "market":
            # Deliver
            unload_time = 15
            self.current_time += unload_time
            reward += self.witch_load * 0.5
            self.total_delivered += self.witch_load
            self.witch_load = 0
            reward -= unload_time * 0.1
        else:
            # Collect from cauldron
            available = self.volumes[next_node]
            # Calculate collection time needed
            desired_collection = min(available, 2000 - self.witch_load)
            collection_time = desired_collection / self.drain_rate

            # Actually collect
            collected = min(available, self.drain_rate * collection_time)
            self.volumes[next_node] -= collected
            self.witch_load += collected

            self.current_time += collection_time
            reward += collected * 0.2
            reward -= collection_time * 0.1

        self.witch_pos = next_node
        self.route.append(next_node)

        # Check overflow
        overflow = 0
        for c in self.cauldrons:
            if self.volumes[c["id"]] > c["max_volume"]:
                overflow += (self.volumes[c["id"]] - c["max_volume"])

        if overflow > 0:
            reward -= overflow * 10
            self.overflow_penalty += overflow

        # Check done
        done = self.current_time >= self.max_time

        # Bonus for ending well
        if done and self.witch_pos == "market" and self.witch_load == 0:
            reward += 100

        return self._get_obs(), reward, done, {}

# --------------------------
# Training with Animation
# --------------------------
class TrainingAnimation:
    def __init__(self):
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 5))
        self.episode_rewards = []
        self.avg_rewards = []
        self.episode = 0

    def update(self, episode, reward, avg_reward, env, route):
        self.episode = episode
        self.episode_rewards.append(reward)
        self.avg_rewards.append(avg_reward)

        # Keep last 100 points
        if len(self.episode_rewards) > 100:
            self.episode_rewards.pop(0)
            self.avg_rewards.pop(0)

        self.ax1.clear()
        self.ax2.clear()

        # Plot 1: Training progress
        self.ax1.plot(self.episode_rewards, 'b-', alpha=0.3, label='Episode Reward')
        self.ax1.plot(self.avg_rewards, 'r-', linewidth=2, label='Average Reward')
        self.ax1.set_title(f'Training Progress (Episode {episode})')
        self.ax1.set_xlabel('Episode')
        self.ax1.set_ylabel('Reward')
        self.ax1.legend()
        self.ax1.grid(True, alpha=0.3)

        # Plot 2: Current route
        self._plot_route(env, route)

        plt.tight_layout()
        plt.pause(0.01)

    def _plot_route(self, env, route):
        # Plot cauldrons
        xs = [c["lat"] for c in cauldrons]
        ys = [c["lon"] for c in cauldrons]
        self.ax2.scatter(xs, ys, c='blue', s=50)

        # Add cauldron labels and fill levels
        for c in cauldrons:
            fill_ratio = env.volumes[c["id"]] / c["max_volume"]
            color = 'red' if fill_ratio > 0.8 else 'orange' if fill_ratio > 0.5 else 'green'
            self.ax2.text(c["lat"], c["lon"], f"{c['id']}\n{fill_ratio:.0%}",
                         fontsize=8, ha='center')

        # Plot market
        self.ax2.scatter([market["lat"]], [market["lon"]], c='black', s=100, marker='s')
        self.ax2.text(market["lat"], market["lon"], "MARKET", fontsize=10, ha='center')

        # Plot route
        if len(route) > 1:
            route_coords = []
            for node in route:
                if node == "market":
                    route_coords.append((market["lat"], market["lon"]))
                else:
                    c = next(x for x in cauldrons if x["id"] == node)
                    route_coords.append((c["lat"], c["lon"]))

            route_x, route_y = zip(*route_coords)
            self.ax2.plot(route_x, route_y, 'purple', linewidth=2, alpha=0.7)
            self.ax2.scatter(route_x, route_y, c='purple', s=30)

        self.ax2.set_xlim(33.2105, 33.2195)
        self.ax2.set_ylim(-97.1385, -97.128)
        self.ax2.set_xlabel('Latitude')
        self.ax2.set_ylabel('Longitude')
        self.ax2.set_title(f'Current Route (Load: {env.witch_load:.0f}L)')
        self.ax2.grid(True, alpha=0.3)

# --------------------------
# Training Loop
# --------------------------
def train_dqn():
    env = WitchEnv()
    state_size = 3
    action_size = env.action_space

    agent = SimpleDQN(state_size, action_size)
    animation = TrainingAnimation()

    batch_size = 32
    episodes = 20000
    rewards_history = []

    print("Training DQN agent...")

    for e in range(episodes):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            action = agent.act(state)
            next_state, reward, done, _ = env.step(action)

            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward

            if done:
                rewards_history.append(total_reward)
                avg_reward = np.mean(rewards_history[-10:]) if len(rewards_history) >= 10 else total_reward

                if e % 10 == 0:
                    print(f"Episode {e:3d}, Reward: {total_reward:7.2f}, "
                          f"Avg: {avg_reward:7.2f}, Epsilon: {agent.epsilon:.3f}, "
                          f"Delivered: {env.total_delivered:5.0f}L")

                # Update animation every 10 episodes
                if e % 10 == 0:
                    animation.update(e, total_reward, avg_reward, env, env.route)

                break

        if len(agent.memory) > batch_size:
            agent.replay(batch_size)

    plt.show()
    return agent, env

# --------------------------
# Final Animation
# --------------------------
def create_final_animation(agent, env):
    print("\nCreating final route animation...")

    # Run one episode with trained agent
    state = env.reset()
    done = False
    frames = []

    while not done:
        frames.append({
            'route': env.route.copy(),
            'load': env.witch_load,
            'time': env.current_time,
            'volumes': env.volumes.copy()
        })

        action = agent.act(state)
        state, reward, done, _ = env.step(action)

    # Add final state
    frames.append({
        'route': env.route.copy(),
        'load': env.witch_load,
        'time': env.current_time,
        'volumes': env.volumes.copy()
    })

    # Create animation
    fig, ax = plt.subplots(figsize=(8, 6))

    def update(frame):
        ax.clear()
        frame_data = frames[frame]
        route = frame_data['route']

        # Title
        ax.set_title(f"Witch Route - Step {frame}/{len(frames)-1}\n"
                    f"Load: {frame_data['load']:.0f}L, Time: {frame_data['time']:.0f}min")

        # Plot cauldrons with fill levels
        for c in cauldrons:
            fill_ratio = frame_data['volumes'][c["id"]] / c["max_volume"]
            color = 'red' if fill_ratio > 0.8 else 'orange' if fill_ratio > 0.5 else 'green'
            size = 50 + fill_ratio * 100

            ax.scatter(c["lat"], c["lon"], c=color, s=size, alpha=0.7)
            ax.text(c["lat"], c["lon"], f"{c['id']}\n{fill_ratio:.0%}",
                   fontsize=8, ha='center', va='center')

        # Plot market
        ax.scatter(market["lat"], market["lon"], c='black', s=150, marker='s')
        ax.text(market["lat"], market["lon"], "MARKET", fontsize=12,
               ha='center', va='center', weight='bold')

        # Plot route
        if len(route) > 1:
            route_coords = []
            for node in route:
                if node == "market":
                    route_coords.append((market["lat"], market["lon"]))
                else:
                    c = next(x for x in cauldrons if x["id"] == node)
                    route_coords.append((c["lat"], c["lon"]))

            route_x, route_y = zip(*route_coords)
            ax.plot(route_x, route_y, 'purple', linewidth=3, alpha=0.7)

            # Highlight current position
            if frame < len(route):
                current_node = route[frame] if frame < len(route) else route[-1]
                if current_node == "market":
                    current_x, current_y = market["lat"], market["lon"]
                else:
                    c = next(x for x in cauldrons if x["id"] == current_node)
                    current_x, current_y = c["lat"], c["lon"]

                ax.scatter([current_x], [current_y], c='yellow', s=200,
                          edgecolors='red', linewidth=2)

        ax.set_xlim(33.2105, 33.2195)
        ax.set_ylim(-97.1385, -97.128)
        ax.set_xlabel('Latitude')
        ax.set_ylabel('Longitude')
        ax.grid(True, alpha=0.3)

    ani = FuncAnimation(fig, update, frames=len(frames), interval=800, repeat=False)
    plt.show()

    print(f"\nFinal Results:")
    print(f"Total Delivered: {env.total_delivered:.0f}L")
    print(f"Total Time: {env.current_time:.0f}min")
    print(f"Efficiency: {env.total_delivered/env.current_time:.3f} L/min")
    print(f"Overflow Penalty: {env.overflow_penalty:.1f}")

# --------------------------
# Main Execution
# --------------------------
if __name__ == "__main__":
    print("=== Simple DQN Witch Route Optimization ===")
    print("Training with drain rate: 0.5 L/min")
    print("Fill rate: 0.25 L/min per cauldron")

    # Train the agent
    agent, env = train_dqn()

    # Show final animation
    create_final_animation(agent, env)
