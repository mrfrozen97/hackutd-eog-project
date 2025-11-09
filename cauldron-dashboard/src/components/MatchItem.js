import React from 'react';

function MatchItem({ match }) {
  return (
    <div className="list-item match">
      <strong>{match.type} Match</strong>
      <p><strong>Date:</strong> {match.date}</p>
      <p><strong>Drain Event:</strong> {match.drain_volume.toFixed(2)} L</p>
      <p><strong>Ticket Sum:</strong> {match.ticket_sum.toFixed(2)} L</p>
      <p><strong>Ticket IDs:</strong> {match.ticket_ids.join(', ')}</p>
      <p><strong>End Time:</strong> {new Date(match.drain_end_time).toLocaleString()}</p>
    </div>
  );
}

export default MatchItem;