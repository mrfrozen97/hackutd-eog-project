// src/components/CauldronDashboard.js

import React from 'react';
import CauldronCard from './CauldronCard';

// 1. Get all the new date-related props
function CauldronDashboard({ 
  cauldrons, onSelectCauldron,
  startDate, endDate, onStartDateChange, onEndDateChange,
  minDate, maxDate
}) {
  
  return (
    // 2. Use a React Fragment to wrap the filter and grid
    <>
      {/* 3. Add the new filter bar */}
      <div className="filter-bar">
        <div className="filter-group">
          <label htmlFor="start-date">Start Date</label>
          <input 
            type="date" 
            id="start-date"
            value={startDate}
            min={minDate}
            max={endDate} // Prevent start date from being after end date
            onChange={(e) => onStartDateChange(e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label htmlFor="end-date">End Date</label>
          <input 
            type="date" 
            id="end-date"
            value={endDate}
            min={startDate} // Prevent end date from being before start date
            max={maxDate}
            onChange={(e) => onEndDateChange(e.target.value)}
          />
        </div>
      </div>

      {/* 4. The existing dashboard grid */}
      <div className="dashboard-grid">
        {cauldrons.map(cauldronData => (
          <CauldronCard
            key={cauldronData.details.id}
            cauldronData={cauldronData}
            onSelect={onSelectCauldron}
          />
        ))}
      </div>
    </>
  );
}

export default CauldronDashboard;