import React from 'react';
import AnomalyItem from './AnomalyItem';
import MatchItem from './MatchItem';

function CauldronDetail({ cauldron, onBack }) {
  const { details, allAnomalies, allMatches } = cauldron;

  return (
    <div className="detail-view">
      <button onClick={onBack} className="back-button">
        &larr; Back to Dashboard
      </button>
      
      <h2>{details.name} ({details.id})</h2>

      <div className="detail-container">
        {/* --- Anomalies Column --- */}
        <div className="column">
          <h3>Anomalies ({allAnomalies.length})</h3>
          <div className="item-list">
            {allAnomalies.length > 0 ? (
              allAnomalies.map((item, index) => (
                <AnomalyItem key={index} anomaly={item} />
              ))
            ) : (
              <p>No anomalies found.</p>
            )}
          </div>
        </div>

        {/* --- Matches Column --- */}
        <div className="column">
          <h3>Matches ({allMatches.length})</h3>
          <div className="item-list">
            {allMatches.length > 0 ? (
              allMatches.map((item, index) => (
                <MatchItem key={index} match={item} />
              ))
            ) : (
              <p>No matches found.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CauldronDetail;