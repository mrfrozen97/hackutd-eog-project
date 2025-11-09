import React from 'react';
import CauldronCard from './CauldronCard';

function CauldronDashboard({ cauldrons, onSelectCauldron }) {
  return (
    <div className="dashboard-grid">
      {cauldrons.map(cauldronData => (
        <CauldronCard
          key={cauldronData.details.id}
          cauldronData={cauldronData}
          onSelect={onSelectCauldron}
        />
      ))}
    </div>
  );
}

export default CauldronDashboard;