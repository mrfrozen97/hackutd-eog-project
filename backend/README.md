# Witch Route Animation Integration

This directory contains the backend API for the witch route optimization animation.

## Setup

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

Required packages:
- fastapi
- uvicorn
- numpy
- networkx

## Running the Backend

### Option 1: Direct Python
```bash
python3 witch_routes_api.py
```

### Option 2: Using the start script
```bash
chmod +x start.sh
./start.sh
```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET /api/witch-routes

Returns the optimal witch routing simulation data.

**Response:**
```json
{
  "n_witches": 3,
  "routes": [
    [
      {"id": "market", "lat": 33.215, "lon": -97.133},
      {"id": "c1", "lat": 33.2148, "lon": -97.1331},
      ...
    ]
  ],
  "volumes": {
    "c1": 450.5,
    "c2": 320.2,
    ...
  },
  "delivered": 8500.0,
  "cauldrons": [
    {
      "id": "c1",
      "lat": 33.2148,
      "lon": -97.1331,
      "max_volume": 1000,
      "current_volume": 450.5,
      "ratio": 0.4505,
      "status": "ok"
    },
    ...
  ],
  "market": {"id": "market", "lat": 33.215, "lon": -97.133}
}
```

## Frontend Integration

The React component `WitchAnimation.js` fetches from this endpoint and renders the animation using HTML Canvas.

### Running the Full Stack

1. Start the backend (in one terminal):
```bash
cd backend
./start.sh
```

2. Start the React frontend (in another terminal):
```bash
cd cauldron-dashboard
npm start
```

The animation will appear on the main dashboard page.

## How It Works

1. **Q-Learning Training**: The backend uses Q-learning to train agents (witches) to optimize their routes
2. **Simulation**: Simulates 3 witches visiting cauldrons, collecting potion, and delivering to market
3. **Route Optimization**: Finds the minimum number of witches needed to service all cauldrons without overflow
4. **Animation Data**: Returns timestamped route positions for smooth frontend animation

## Dependencies on Other Files

- `AI Model/slopes.json` - Contains fill_rate and pour_rate data for each cauldron
- The simulation uses the same cauldron positions and network graph as `grok_with map_animation.py`

## Troubleshooting

**Backend won't start:**
- Make sure Python 3.8+ is installed
- Check that all dependencies are installed: `pip3 list | grep -E "fastapi|uvicorn|numpy|networkx"`

**Frontend can't connect:**
- Verify backend is running on port 8000
- Check CORS settings allow `localhost:3000`
- Open `http://localhost:8000/api/witch-routes` in browser to test API directly

**Animation not showing:**
- Check browser console for errors
- Verify `WitchAnimation` component is imported in `App.js`
- Ensure backend returns valid JSON data
