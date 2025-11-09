import React from 'react';

function CauldronCard({ cauldronData, onSelect }) {
  const { details, anomalyCount, matchCount } = cauldronData;

  return (
    // This whole card is clickable
    <div className="card" onClick={() => onSelect(details.id)}>
      <h3>{details.name}</h3>
      <p className="card-id">{details.id}</p>
      
      <div className="card-details">
        <p><strong>Max Volume:</strong> {details.max_volume.toFixed(0)} L</p>
        <p><strong>Location:</strong> ({details.latitude}, {details.longitude})</p>
        
        {/* As you noted, 'fill rate' isn't in anomalies.json.
            To get this, you'd need to modify your Python script 
            to also output the 'average_positive_slope' for each cauldron.
        */}
      </div>

      <div className="card-stats">
        <div className="stat-box matches">
          <strong>{matchCount}</strong>
          <span>Matches</span>
        </div>
        <div className="stat-box anomalies">
          <strong>{anomalyCount}</strong>
          <span>Anomalies</span>
        </div>
      </div>
    </div>
  );
}

export default CauldronCard;