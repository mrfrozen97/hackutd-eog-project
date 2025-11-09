import React from 'react';

function AnomalyItem({ anomaly }) {
  const isDrain = anomaly.type === 'DRAIN_ANOMALY';
  
  return (
    <div className={`list-item anomaly ${isDrain ? 'drain' : 'ticket'}`}>
      <strong>{isDrain ? 'Drain Anomaly' : 'Ticket Anomaly'}</strong>
      <p><strong>Date:</strong> {anomaly.date}</p>
      <p><strong>Volume:</strong> {anomaly.volume.toFixed(2)} L</p>
      {isDrain ? (
        <p><strong>Time:</strong> {new Date(anomaly.time).toLocaleString()}</p>
      ) : (
        <p><strong>Ticket ID:</strong> {anomaly.ticket_id}</p>
      )}
    </div>
  );
}

export default AnomalyItem;