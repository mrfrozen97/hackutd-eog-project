import React, { useState, useEffect, useRef } from 'react';
import './WitchAnimation.css';

// Dynamically load Leaflet CSS
const loadLeafletCSS = () => {
  if (!document.getElementById('leaflet-css')) {
    const link = document.createElement('link');
    link.id = 'leaflet-css';
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
    link.crossOrigin = '';
    document.head.appendChild(link);
  }
};

// Dynamically load Leaflet JS
const loadLeafletJS = () => {
  return new Promise((resolve, reject) => {
    if (window.L) {
      resolve(window.L);
      return;
    }
    if (!document.getElementById('leaflet-js')) {
      const script = document.createElement('script');
      script.id = 'leaflet-js';
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
      script.crossOrigin = '';
      script.onload = () => resolve(window.L);
      script.onerror = reject;
      document.head.appendChild(script);
    }
  });
};

const WitchAnimation = () => {
  const [simulationData, setSimulationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [animationFrame, setAnimationFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [leafletLoaded, setLeafletLoaded] = useState(false);
  const [selectedWitch, setSelectedWitch] = useState(null);
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const animationRef = useRef(null);
  const markersRef = useRef({});
  const polylinesRef = useRef([]);

  // Generate dynamic colors for witches
  const generateWitchColors = (numWitches) => {
    const baseColors = [
      '#9b59b6', // Purple
      '#3498db', // Blue
      '#e74c3c', // Red
      '#f39c12', // Orange
      '#2ecc71', // Green
      '#e67e22', // Dark Orange
      '#1abc9c', // Turquoise
      '#34495e', // Dark Gray
      '#16a085', // Dark Turquoise
      '#27ae60', // Dark Green
      '#2980b9', // Dark Blue
      '#8e44ad', // Dark Purple
      '#c0392b'  // Dark Red
    ];
    
    const colors = [];
    for (let i = 0; i < numWitches; i++) {
      if (i < baseColors.length) {
        colors.push(baseColors[i]);
      } else {
        // Generate additional colors using HSL
        const hue = (i * 137.5) % 360; // Golden angle approximation for nice distribution
        colors.push(`hsl(${hue}, 70%, 50%)`);
      }
    }
    return colors;
  };

  // Load Leaflet
  useEffect(() => {
    loadLeafletCSS();
    loadLeafletJS()
      .then(() => {
        setLeafletLoaded(true);
      })
      .catch(err => {
        console.error('Failed to load Leaflet:', err);
        setError('Failed to load map library');
      });
  }, []);

  // Fetch simulation data from backend
  useEffect(() => {
    const fetchSimulation = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/api/witch-routes');
        if (!response.ok) {
          throw new Error('Failed to fetch simulation data');
        }
        const data = await response.json();
        setSimulationData(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchSimulation();
  }, []);

  // Initialize map
  useEffect(() => {
    if (!leafletLoaded || !simulationData || !mapRef.current || mapInstanceRef.current) return;

    const L = window.L;

    // Calculate center from all cauldrons
    const allLats = [...simulationData.cauldrons.map(c => c.lat), simulationData.market.lat];
    const allLons = [...simulationData.cauldrons.map(c => c.lon), simulationData.market.lon];
    const centerLat = (Math.min(...allLats) + Math.max(...allLats)) / 2;
    const centerLon = (Math.min(...allLons) + Math.max(...allLons)) / 2;

    // Create map
    const map = L.map(mapRef.current, {
      zoomControl: true,
      attributionControl: true
    }).setView([centerLat, centerLon], 15);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(map);

    mapInstanceRef.current = map;

    // Add cauldron markers
    simulationData.cauldrons.forEach(cauldron => {
      let color;
      if (cauldron.ratio > 0.9) color = '#ff4444';
      else if (cauldron.ratio > 0.7) color = '#ff9933';
      else color = '#024102ff';

      const radius = 12 + (cauldron.ratio * 18);

      const marker = L.circleMarker([cauldron.lat, cauldron.lon], {
        radius: radius,
        fillColor: color,
        color: '#fff',
        weight: 3,
        opacity: 1,
        fillOpacity: 0.9
      }).addTo(map);

      // Add a pulsing effect with a larger outer circle
      const outerCircle = L.circleMarker([cauldron.lat, cauldron.lon], {
        radius: radius + 6,
        fillColor: color,
        color: color,
        weight: 1,
        opacity: 0.4,
        fillOpacity: 0.2
      }).addTo(map);

      marker.bindPopup(`
        <strong>${cauldron.id}</strong><br/>
        Volume: ${Math.round(cauldron.current_volume)}L / ${cauldron.max_volume}L<br/>
        Status: ${cauldron.status}
      `);

      markersRef.current[cauldron.id] = marker;
      markersRef.current[`${cauldron.id}-outer`] = outerCircle;
    });

    // Add market marker
    const marketMarker = L.marker([simulationData.market.lat, simulationData.market.lon], {
      icon: L.divIcon({
        className: 'market-icon',
        html: '<div style="background: #000; color: #fff; padding: 5px 10px; border: 1px solid #ffd700; font-weight: bold; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.4); border-radius: 1px;">M</div>',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
      })
    }).addTo(map);

    marketMarker.bindPopup('<strong>Market</strong><br/>Delivery point');
    markersRef.current['market'] = marketMarker;

    // Fit bounds to show all markers
    const bounds = L.latLngBounds(
      simulationData.cauldrons.map(c => [c.lat, c.lon]).concat([[simulationData.market.lat, simulationData.market.lon]])
    );
    map.fitBounds(bounds, { padding: [50, 50] });

    return () => {
      if (mapInstanceRef.current) {
        // Clear all markers and polylines before removing map
        try {
          polylinesRef.current.forEach(polyline => {
            if (polyline && mapInstanceRef.current.hasLayer(polyline)) {
              mapInstanceRef.current.removeLayer(polyline);
            }
          });
          polylinesRef.current = [];
          
          Object.keys(markersRef.current).forEach(key => {
            const marker = markersRef.current[key];
            if (marker && mapInstanceRef.current.hasLayer(marker)) {
              mapInstanceRef.current.removeLayer(marker);
            }
          });
          markersRef.current = {};
        } catch (err) {
          console.warn('Error cleaning up map layers:', err);
        }
        
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [leafletLoaded, simulationData]);

  // Update routes on animation frame
  useEffect(() => {
    if (!mapInstanceRef.current || !simulationData || !window.L) return;

    const L = window.L;
    const map = mapInstanceRef.current;
    
    // Check if map is still valid
    if (!map._leaflet_id) return;
    
    const witchColors = generateWitchColors(simulationData.routes.length);

    // Clear previous polylines and witch markers safely
    polylinesRef.current.forEach(polyline => {
      try {
        if (polyline && map._leaflet_id && map.hasLayer(polyline)) {
          map.removeLayer(polyline);
        }
      } catch (err) {
        console.warn('Error removing polyline:', err);
      }
    });
    polylinesRef.current = [];
    
    Object.keys(markersRef.current).forEach(key => {
      if (key.startsWith('witch-')) {
        try {
          const marker = markersRef.current[key];
          if (marker && map._leaflet_id && map.hasLayer(marker)) {
            map.removeLayer(marker);
          }
          delete markersRef.current[key];
        } catch (err) {
          console.warn('Error removing witch marker:', err);
        }
      }
    });

    // Draw routes up to current frame
    simulationData.routes.forEach((route, witchIdx) => {
      // Check if map is still valid before adding layers
      if (!map._leaflet_id) return;
      
      const color = witchColors[witchIdx % witchColors.length];
      const pathLength = Math.min(animationFrame + 1, route.length);

      if (pathLength > 1) {
        try {
          const latLngs = route.slice(0, pathLength).map(node => [node.lat, node.lon]);
          const polyline = L.polyline(latLngs, {
            color: color,
            weight: 5,
            opacity: 0.8,
            dashArray: '10, 5'
          }).addTo(map);
          polylinesRef.current.push(polyline);
        } catch (err) {
          console.warn('Error adding polyline:', err);
        }
      }

      // Draw witch current position
      if (pathLength > 0) {
        try {
          const currentNode = route[Math.min(animationFrame, route.length - 1)];
          
          // Add a glowing outer circle for witch
          const witchGlow = L.circleMarker([currentNode.lat, currentNode.lon], {
            radius: 16,
            fillColor: color,
            color: color,
            weight: 2,
            opacity: 0.5,
            fillOpacity: 0.3
          }).addTo(map);
          
          const witchMarker = L.circleMarker([currentNode.lat, currentNode.lon], {
            radius: 10,
            fillColor: color,
            color: '#fff',
            weight: 3,
            opacity: 1,
            fillOpacity: 1
          }).addTo(map);

          witchMarker.bindPopup(`<strong>Witch ${witchIdx + 1}</strong><br/>At: ${currentNode.id}`);
          markersRef.current[`witch-${witchIdx}`] = witchMarker;
          markersRef.current[`witch-${witchIdx}-glow`] = witchGlow;
        } catch (err) {
          console.warn('Error adding witch marker:', err);
        }
      }
    });
  }, [simulationData, animationFrame]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying || !simulationData) return;

    const maxFrames = Math.max(...simulationData.routes.map(r => r.length));
    
    const animate = () => {
      setAnimationFrame(prev => {
        if (prev >= maxFrames - 1) {
          setIsPlaying(false);
          return maxFrames - 1;
        }
        return prev + 1;
      });
    };

    animationRef.current = setInterval(animate, 600);
    return () => clearInterval(animationRef.current);
  }, [isPlaying, simulationData]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setAnimationFrame(0);
  };

  const handleStepForward = () => {
    if (!simulationData) return;
    const maxFrames = Math.max(...simulationData.routes.map(r => r.length));
    setAnimationFrame(prev => Math.min(prev + 1, maxFrames - 1));
  };

  const handleStepBackward = () => {
    setAnimationFrame(prev => Math.max(prev - 1, 0));
  };

  if (loading || !leafletLoaded) {
    return (
      <div className="witch-animation-container">
        <div className="loading">Loading simulation...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="witch-animation-container">
        <div className="error">Error: {error}</div>
        <div className="error-help">
          Make sure the backend is running:
          <code>cd backend && python witch_routes_api.py</code>
        </div>
      </div>
    );
  }

  const maxFrames = simulationData ? Math.max(...simulationData.routes.map(r => r.length)) : 0;

  return (
    <div className="witch-animation-container">
      <h2>Witch Route Optimization</h2>
      <div className="map-wrapper">
        <div ref={mapRef} className="animation-map" style={{ width: '100%', height: '600px' }} />
        <div className="info-panel">
          <div><strong>Step:</strong> {animationFrame}</div>
          <div><strong>Witches:</strong> {simulationData?.n_witches || 0}</div>
          <div><strong>Delivered:</strong> {simulationData ? Math.round(simulationData.delivered).toLocaleString() : 0} L</div>
        </div>
      </div>
      <div className="controls">
        <button onClick={handleReset} className="control-btn">
          ⏮ Reset
        </button>
        <button onClick={handleStepBackward} className="control-btn" disabled={animationFrame === 0}>
          ⏪ Step Back
        </button>
        <button onClick={handlePlayPause} className="control-btn play-pause">
          {isPlaying ? 'Stop' : 'Forecast'}
        </button>
        <button onClick={handleStepForward} className="control-btn" disabled={animationFrame >= maxFrames - 1}>
          ⏩ Step Forward
        </button>
      </div>
      <div className="legend">
        {/* Dynamic Witch Legend */}
        {simulationData && generateWitchColors(simulationData.routes.length).map((color, idx) => (
          <div className="legend-item" key={`witch-${idx}`}>
            <span className="legend-color" style={{ backgroundColor: color }}></span>
            Witch {idx + 1}
          </div>
        ))}
        
        {/* Cauldron Status Legend */}
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#024102ff' }}></span>
          OK (&lt;70%)
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#ff9933' }}></span>
          Warning (70-90%)
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#ff4444' }}></span>
          Critical (&gt;90%)
        </div>
      </div>

      {/* Witch Paths */}
      {simulationData?.schedules && (
        <div className="schedule-section">
          <h3>Witch Routes</h3>
          <div className="witch-tabs">
            {simulationData.schedules.map((schedule, idx) => {
              const colors = generateWitchColors(simulationData.schedules.length);
              return (
                <button
                  key={idx}
                  className={`witch-tab ${selectedWitch === idx ? 'active' : ''}`}
                  style={{
                    backgroundColor: selectedWitch === idx ? colors[idx] : '#3a3a3a',
                    borderColor: colors[idx]
                  }}
                  onClick={() => setSelectedWitch(idx)}
                >
                  Witch {schedule.witch_id}
                </button>
              );
            })}
          </div>
          
          {selectedWitch !== null && simulationData.schedules[selectedWitch] && (
            <div className="schedule-content">
              <div className="path-display">
                {simulationData.schedules[selectedWitch].path.map((location, idx) => (
                  <span key={idx}>
                    <span className="location-node">{location}</span>
                    {idx < simulationData.schedules[selectedWitch].path.length - 1 && (
                      <span className="path-arrow"> → </span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WitchAnimation;
