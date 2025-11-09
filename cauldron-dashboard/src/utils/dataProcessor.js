/**
 * This function takes the raw API and JSON data and combines them
 * into a single, easy-to-use array.
 */
export function processData(anomaliesData, cauldronsFromApi) {
  // 1. Create a lookup map for our processed data
  const processedMap = new Map();

  // 2. Initialize the map with data from the cauldron API
  for (const cauldron of cauldronsFromApi) {
    processedMap.set(cauldron.id, {
      details: cauldron,
      allAnomalies: [],
      allMatches: [],
      anomalyCount: 0,
      matchCount: 0,
    });
  }

  // 3. Loop through all ANOMALIES and add them to the correct cauldron
  for (const [date, cauldrons] of Object.entries(anomaliesData.anomalies)) {
    for (const [cauldronId, anomalies] of Object.entries(cauldrons)) {
      if (processedMap.has(cauldronId)) {
        const data = processedMap.get(cauldronId);
        
        // Add the date to each anomaly for context
        const datedAnomalies = anomalies.map(a => ({ ...a, date }));

        data.allAnomalies.push(...datedAnomalies);
        data.anomalyCount += anomalies.length;
      }
    }
  }

  // 4. Loop through all MATCHES and add them to the correct cauldron
  for (const [date, cauldrons] of Object.entries(anomaliesData.matches)) {
    for (const [cauldronId, matches] of Object.entries(cauldrons)) {
      if (processedMap.has(cauldronId)) {
        const data = processedMap.get(cauldronId);
        data.allMatches.push(...matches);
        data.matchCount += matches.length;
      }
    }
  }

  // 5. Return the processed data as a single array
  return Array.from(processedMap.values());
}