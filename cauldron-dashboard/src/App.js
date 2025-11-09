import React, { useState, useEffect } from 'react';
import { processData } from './utils/dataProcessor';
import CauldronDashboard from './components/CauldronDashboard';
import CauldronDetail from './components/CauldronDetail';
import './App.css'; // We'll create this file for styling

function App() {
  const [loading, setLoading] = useState(true);
  const [processedData, setProcessedData] = useState([]);
  const [selectedCauldron, setSelectedCauldron] = useState(null);

  // This is the base URL for your API
  const BASE_URL = "/api";

  useEffect(() => {
    // This function runs once on component mount
    async function loadData() {
      try {
        // 1. Fetch both data sources at the same time
        const [cauldronRes, anomalyRes] = await Promise.all([
          fetch(`${BASE_URL}/api/Information/cauldrons`),
          fetch('/anomalies.json') // Fetches from the 'public' folder
        ]);

        const cauldronsFromApi = await cauldronRes.json();
        const anomaliesData = await anomalyRes.json();

        // 2. Process the data using our utility
        const data = processData(anomaliesData, cauldronsFromApi);
        setProcessedData(data);

      } catch (error) {
        console.error("Failed to load data:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [BASE_URL]); // Empty dependency array means this runs once

  // --- Handlers for view switching ---
  const handleSelectCauldron = (cauldronId) => {
    const cauldron = processedData.find(c => c.details.id === cauldronId);
    setSelectedCauldron(cauldron);
  };

  const handleBack = () => {
    setSelectedCauldron(null);
  };

  // --- Render Logic ---
  if (loading) {
    return <div className="loading">Loading Cauldron Data...</div>;
  }

  return (
    <div className="App">
      <header>
        <h1>Cauldron Analysis Dashboard</h1>
      </header>
      <main>
        {selectedCauldron ? (
          <CauldronDetail cauldron={selectedCauldron} onBack={handleBack} />
        ) : (
          <CauldronDashboard 
            cauldrons={processedData} 
            onSelectCauldron={handleSelectCauldron} 
          />
        )}
      </main>
    </div>
  );
}

export default App;