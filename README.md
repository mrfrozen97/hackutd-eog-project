# Alchem-AI 🧙‍♀️

> Real-time monitoring for production tanks that tracks levels, detects transfers, and verifies reported output so discrepancies are caught early and every drop is accounted for.

**Submitted to HackUTD 2025: Lost in the Pages**

## 🎯 Inspiration

The production process is dynamic—storage tanks fill at variable rates, materials flow unexpectedly, and transport schedules don't always align with real usage. To complicate things more, differences between recorded output and delivered volume may point to loss, waste, or diversion for other purposes. 

We wanted to create a system that converts this continuously changing process into a transparent and verifiable system, with full visibility into:
- Tank levels in real-time
- Material transfers and drain events
- Flow patterns to prevent overflows
- Efficient logistics operations
- Complete accountability for every drop

## 🔮 What It Does

Alchem-AI provides a comprehensive real-time monitoring and optimization platform:

### Real-Time Tank Monitoring
- **Live Dashboard**: Visualizes current tank levels across all cauldrons
- **Event Detection**: Automatically detects transfer and drain events as they happen
- **Discrepancy Detection**: Compares actual transfers against reported transport records
- **Instant Alerts**: Flags discrepancies immediately for review

### Predictive Analytics
- **Fill Rate Analysis**: Calculates brewing/fill rates from historical data
- **Overflow Forecasting**: Predicts future tank trajectories to prevent overflows
- **Time-to-Overflow**: Provides hard time constraints for pickup scheduling

### Intelligent Logistics
- **Q-Learning Optimization**: Uses Deep Q-Learning to find minimum number of witches (couriers) needed
- **Route Planning**: Generates optimal pickup routes to prevent overflow
- **Dynamic Scheduling**: Automatically creates daily schedules for each witch
- **Map Visualization**: Interactive OpenStreetMap display with real-time animation of witch routes

## 🛠️ How We Built It

### Backend & Data Processing
- **Python**: Data ingestion, transformation, and modeling
  - Time-series forecasting for overflow prediction
  - Q-Learning agent for route optimization (400 episodes training)
  - Slope analysis for detecting fill/drain events
  - FastAPI server for witch routing API

### Data Storage & Search
- **Elasticsearch**: High-performance data repository
  - Stores vast quantities of cauldron telemetry
  - Lightning-fast querying and searching
  - Real-time data indexing

### Visualization & Dashboards
- **Kibana**: Master Brewer's Dashboard
  - Real-time cauldron status visualization
  - Overflow prediction timelines
  - Historical trend analysis

- **React Frontend**: Interactive Cauldron Dashboard
  - Real-time tank level monitoring with color-coded status
  - OpenStreetMap integration with Leaflet.js
  - Animated witch routing visualization
  - Dynamic schedule display for each courier
  - Anomaly detection and matching interface

### Machine Learning & Optimization
- **Q-Learning (Reinforcement Learning)**: 
  - State space: 10×10×10 (position, load, time)
  - Epsilon-greedy exploration (1.0 → 0.01)
  - Discount factor: 0.95, Learning rate: 0.001
  - Minimum 3 witches enforcement

- **Vehicle Routing Problem (VRP-TW)**: 
  - Modeled as VRP with Time Windows
  - Constraints: Tank capacity, witch load limits, time-to-overflow
  - Objective: Minimize number of couriers while preventing overflow

## 🚧 Challenges We Ran Into

1. **Complex Data Dynamics**: Cauldrons fill even while draining, making simple volume measurements inaccurate
2. **Live Dashboard Updates**: Required proper indexing and refresh strategies in Kibana
3. **Optimization Complexity**: Finding minimum witch count while preventing overflow is computationally challenging
4. **Map Integration**: Leaflet layer management with React required careful state handling and error prevention
5. **Real-Time Synchronization**: Coordinating backend Q-learning with frontend animation timing

## 🏆 Accomplishments We're Proud Of

✅ **Real-Time Operational Dashboard** with live tank monitoring and status indicators

✅ **Successful Discrepancy Detection** using inferred flow behaviors from slope analysis

✅ **Beautiful UI Design** with potion level icons and map visuals that are simple, readable, and alive

✅ **Deep Q-Learning Implementation** to identify minimum witches required to prevent overflow

✅ **Full-Stack Integration** connecting Elasticsearch, Python backend, and React frontend seamlessly

✅ **Dynamic Route Visualization** with OpenStreetMap, animated witch movements, and color-coded paths

## 📚 What We Learned

### Integrity Detection
We learned to isolate true drain events from continuous filling using the **SlopeAnalyzer**. We calculate the actual volume collected (tank drop + volume generated during drain time) to flag ticket discrepancies accurately.

### Capacity Forecasting
We determined each cauldron's fill rate from historical positive slope data and used it to forecast **time-to-overflow**, which serves as the hard time constraint for scheduling.

### Logistics Optimization (VRP)
We successfully modeled the challenge as a **Vehicle Routing Problem with Time Windows (VRP-TW)** to find the minimum number of witches required and generate overflow-preventing routes.

### React + Leaflet Integration
We mastered dynamic Leaflet map loading, layer lifecycle management, and safe marker/polyline operations with proper state validation.

## 🚀 What's Next for Alchem-AI

- **Real-Time Alerts**: Slack/SMS notifications for operators when loss or mismatch is detected
- **Dynamic Auto-Scheduling**: Automatically generate optimal pickup routes based on live tank forecasts
- **Predictive Maintenance**: Identify patterns that indicate equipment issues before failure
- **Advanced Analytics**: Machine learning for demand forecasting and capacity planning
- **Multi-Site Support**: Scale to monitor multiple production facilities
- **Mobile App**: On-the-go monitoring and alerts for field operators

## 🏗️ Project Structure

```
hackutd-eog-project/
├── backend/                          # FastAPI witch routing server
│   ├── witch_routes_api.py          # Q-learning optimization & API
│   ├── requirements.txt             # Python dependencies
│   ├── start.sh                     # Startup script
│   └── witch_schedules.json         # Generated schedules
├── cauldron-dashboard/              # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── CauldronDashboard.js # Main dashboard
│   │   │   ├── WitchAnimation.js    # Map & route visualization
│   │   │   ├── AnomalyItem.js       # Anomaly display
│   │   │   └── MatchItem.js         # Match display
│   │   └── utils/
│   │       └── dataProcessor.js     # Data transformation
│   └── public/
│       └── anomalies.json           # Anomaly data
├── AI Model/                        # ML models & data
│   ├── grok_with map_animation.py  # Original matplotlib animation
│   ├── slopes.json                  # Fill/pour rate data
│   └── odata.json                   # Original data
├── elastic-start-local/             # Elasticsearch setup
│   ├── docker-compose.yml           # Container orchestration
│   └── start.sh                     # Elasticsearch startup
├── fill_rate/                       # Fill rate analysis
│   └── fill_rate_calc.py           # Rate calculation
├── slope_analyzer.py                # Slope detection for events
├── anamolies_data_pusher.py        # Push data to Elasticsearch
├── elastic_middleware.py            # Elasticsearch interface
└── find_matches.py                  # Match detection logic
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose (for Elasticsearch)

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
python witch_routes_api.py
# Server runs on http://localhost:8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd cauldron-dashboard

# Install dependencies
npm install

# Start the development server
npm start
# App opens at http://localhost:3000
```

### Elasticsearch Setup

```bash
# Navigate to elastic directory
cd elastic-start-local

# Start Elasticsearch and Kibana
./start.sh

# Elasticsearch: http://localhost:9200
# Kibana: http://localhost:5601
```

## 🔧 API Endpoints

### Witch Routes API
**GET** `/api/witch-routes`

Returns optimized witch routing solution:
```json
{
  "n_witches": 3,
  "routes": [[{lat, lon, id}, ...]],
  "volumes": {"C1": 245.5, "C2": 189.3, ...},
  "delivered": 1250.7,
  "cauldrons": [{id, lat, lon, max_volume, status, ratio}, ...],
  "market": {lat, lon},
  "schedules": [
    {
      "witch_id": 1,
      "path": ["market", "C1", "market", "C2", "market"]
    }
  ]
}
```

## 📊 Key Technologies

- **Python** - Data processing, ML, API server
- **FastAPI** - RESTful API framework
- **NumPy** - Numerical computing for Q-learning
- **NetworkX** - Graph algorithms for routing
- **React** - Frontend framework
- **Leaflet.js** - Interactive map visualization
- **Elasticsearch** - Data storage and search
- **Kibana** - Data visualization dashboards
- **Docker** - Containerization

## 👥 Team

- **Uddesh Singh** - [@uddeshsingh](https://devpost.com/uddeshsingh)
- **Vighanesh Sharma** - [@Vighaneshs](https://devpost.com/Vighaneshs)
- **Tanishq Nimale** - [@mrfrozen97](https://devpost.com/mrfrozen97)
- **Naveen Mathew Georgi** - [@naveengeorgius](https://devpost.com/naveengeorgius)

## 📜 License

This project was created for HackUTD 2025.

## 🔗 Links

- **DevPost**: [https://devpost.com/software/potionfactoryanalysis](https://devpost.com/software/potionfactoryanalysis)
- **HackUTD 2025**: [Lost in the Pages](https://hackutd-2025.devpost.com/)

---

Made with 🧪 and ✨ at HackUTD 2025