// src/utils/dataProcessor.js

/**
 * Merges anomaly pairs of different types by volume difference.
 * Sorts anomalies by volume descending, then pairs different types.
 * Unpaired anomalies are kept as-is.
 */
function mergeAnomalyPairs(anomalies, date) {
  if (!anomalies || anomalies.length === 0) return [];
  
  // Add date to all anomalies
  const datedAnomalies = anomalies.map(a => ({ ...a, date }));
  
  // Sort by volume descending
  datedAnomalies.sort((a, b) => (b.volume || 0) - (a.volume || 0));
  
  const used = new Set();
  const result = [];
  
  // Try to pair anomalies of different types
  for (let i = 0; i < datedAnomalies.length; i++) {
    if (used.has(i)) continue;
    
    const first = datedAnomalies[i];
    let paired = false;
    
    // Look for a partner of different type
    for (let j = i + 1; j < datedAnomalies.length; j++) {
      if (used.has(j)) continue;
      
      const second = datedAnomalies[j];
      
      // Check if types differ
      if (first.type !== second.type) {
        // Merge: create combined anomaly with volume difference
        const volumeDiff = Math.abs((first.volume || 0) - (second.volume || 0));
        const merged = {
          ...first,
          type: 'mismatch',
          difference: volumeDiff,
          volume: undefined, // Remove volume field
          originalVolumes: {
            [first.type]: first.volume || 0,
            [second.type]: second.volume || 0
          },
          merged: true
        };
        result.push(merged);
        used.add(i);
        used.add(j);
        paired = true;
        break;
      }
    }
    
    // If no pair found, keep original
    if (!paired) {
      result.push(first);
      used.add(i);
    }
  }
  
  return result;
}

// 1. Update function signature to accept dates
export function processData(anomaliesData, cauldronsFromApi, startDate, endDate) {
  
  const processedMap = new Map();

  // Initialize all cauldrons
  for (const cauldron of cauldronsFromApi) {
    processedMap.set(cauldron.id, {
      details: cauldron,
      allAnomalies: [],
      allMatches: [],
      anomalyCount: 0,
      matchCount: 0,
    });
  }

  // Loop through all ANOMALIES
  for (const [date, cauldrons] of Object.entries(anomaliesData.anomalies)) {
    // --- 2. ADDED FILTER LOGIC ---
    if (date < startDate || date > endDate) {
      continue; // Skip this date
    }
    // --- END ADDED LOGIC ---

    for (const [cauldronId, anomalies] of Object.entries(cauldrons)) {
      if (processedMap.has(cauldronId)) {
        const data = processedMap.get(cauldronId);
        
        // Process anomalies: merge pairs of different types by volume difference
        const processedAnomalies = mergeAnomalyPairs(anomalies, date);
        
        data.allAnomalies.push(...processedAnomalies);
        data.anomalyCount += processedAnomalies.length;
      }
    }
  }

  // Loop through all MATCHES
  for (const [date, cauldrons] of Object.entries(anomaliesData.matches)) {
    // --- 3. ADDED FILTER LOGIC ---
    if (date < startDate || date > endDate) {
      continue; // Skip this date
    }
    // --- END ADDED LOGIC ---
    
    for (const [cauldronId, matches] of Object.entries(cauldrons)) {
      if (processedMap.has(cauldronId)) {
        const data = processedMap.get(cauldronId);
        data.allMatches.push(...matches);
        data.matchCount += matches.length;
      }
    }
  }

  return Array.from(processedMap.values());
}