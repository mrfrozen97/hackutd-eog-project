// src/App.js

import React, { useState, useEffect } from 'react';
import { processData } from './utils/dataProcessor';
import CauldronDashboard from './components/CauldronDashboard';
import CauldronDetail from './components/CauldronDetail';
import './App.css';

// --- (NEW) IMPORT YOUR IMAGES ---
import eogLogo from './assets/eog-logo.png';
import hackutdBanner from './assets/hackutd-banner.png';

function App() {
  const [loading, setLoading] = useState(true);
  // ... (rest of your state is unchanged) ...
  const [selectedCauldronId, setSelectedCauldronId] = useState(null);
  const [allCauldrons, setAllCauldrons] = useState([]);
  const [allAnomaliesData, setAllAnomaliesData] = useState(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const BASE_URL = "/api"; 

  // ... (your useEffect is unchanged) ...
  useEffect(() => {
    async function loadData() {
      try {
        const [cauldronRes, anomalyRes] = await Promise.all([
          fetch(`${BASE_URL}/api/Information/cauldrons`), // The corrected double /api/api path
          fetch('/anomalies.json')
        ]);
        // ... (rest of useEffect is unchanged) ...
        const cauldronsFromApi = await cauldronRes.json();
        const anomaliesData = await anomalyRes.json();
        
        setAllCauldrons(cauldronsFromApi);
        setAllAnomaliesData(anomaliesData);

        if (anomaliesData?.metadata) {
          setStartDate(anomaliesData.metadata.start_date);
          setEndDate(anomaliesData.metadata.end_date);
        }

      } catch (error) {
        console.error("Failed to load data:", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [BASE_URL]);

  // ... (your handlers are unchanged) ...
  const handleSelectCauldron = (cauldronId) => {
    setSelectedCauldronId(cauldronId);
  };
  const handleBack = () => {
    setSelectedCauldronId(null);
  };

  // ... (your loading guard is unchanged) ...
  if (loading || !allAnomaliesData || allCauldrons.length === 0) {
    return <div className="loading">Loading Cauldron Data...</div>;
  }
  
  // ... (your data processing is unchanged) ...
  const processedData = processData(
    allAnomaliesData, 
    allCauldrons, 
    startDate, 
    endDate
  );
  const selectedCauldronData = selectedCauldronId 
    ? processedData.find(c => c.details.id === selectedCauldronId)
    : null;


  return (
    <div className="App">
      {/* --- (MODIFIED) UPDATE THE HEADER --- */}
      <header>
        <img 
          src={hackutdBanner} 
          alt="HackUTD Banner" 
          className="header-image"
          style={{ width: '250px' }} // You can adjust the size
        />
        <h1>Cauldron Analysis Dashboard</h1>
        <img 
          src={eogLogo} 
          alt="EOG Logo" 
          className="header-image"
          style={{ width: '200px' }} // You can adjust the size
        />
      </header>
      {/* --- (END MODIFICATION) --- */}
      
      <main>
        {selectedCauldronData ? (
          // ... (rest of your app is unchanged) ...
          <CauldronDetail 
            cauldron={selectedCauldronData} 
            onBack={handleBack} 
          />
        ) : (
          <CauldronDashboard 
            cauldrons={processedData} 
            onSelectCauldron={handleSelectCauldron}
            startDate={startDate}
            endDate={endDate}
            onStartDateChange={setStartDate}
            onEndDateChange={setEndDate}
            minDate={allAnomaliesData.metadata.start_date}
            maxDate={allAnomaliesData.metadata.end_date}
          />
        )}
      </main>
    </div>
  );
}

export default App;