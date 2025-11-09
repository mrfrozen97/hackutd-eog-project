import React from 'react';

function AnomalyItem({ anomaly }) {
  const isDrain = anomaly.type === 'DRAIN_ANOMALY';
  const isMismatch = anomaly.type === 'mismatch';
  
  // Get display title
  let title = 'Ticket Anomaly';
  if (isDrain) title = 'Drain Anomaly';
  if (isMismatch) title = 'Mismatch Anomaly';
  
  // Get volume or difference value
  const volumeValue = isMismatch ? anomaly.difference : anomaly.volume;
  const volumeLabel = isMismatch ? 'Difference' : 'Volume';
  
  return (
    <div className={`list-item anomaly ${isDrain || isMismatch ? 'drain' : 'ticket'}`}>
      <strong>{title}</strong>
      <p><strong>Date:</strong> {anomaly.date}</p>
      {volumeValue != null && (
        <p>
          <strong>{volumeLabel}:</strong> 
          {isMismatch ? (
            <span style={{ color: '#ff4444', fontWeight: 'bold', fontSize: '1.1em' }}> {volumeValue.toFixed(2)} L</span>
          ) : (
            <span> {volumeValue.toFixed(2)} L</span>
          )}
        </p>
      )}
      {isDrain ? (
        <p><strong>Time:</strong> {new Date(anomaly.time).toLocaleString()}</p>
      ) : isMismatch ? (
        <p><strong>Original Volumes:</strong> {JSON.stringify(anomaly.originalVolumes)}</p>
      ) : (
        <p><strong>Ticket ID:</strong> {anomaly.ticket_id}</p>
      )}
    </div>
  );
}

export default AnomalyItem;