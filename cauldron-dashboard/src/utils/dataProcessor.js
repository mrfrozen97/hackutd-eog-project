// src/utils/dataProcessor.js

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
        const datedAnomalies = anomalies.map(a => ({ ...a, date }));
        data.allAnomalies.push(...datedAnomalies);
        data.anomalyCount += anomalies.length;
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