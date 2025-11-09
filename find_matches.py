import requests
import pandas as pd
from datetime import date, datetime # Added datetime for date parsing

# --- Import our custom analyzer tools from the other file ---
from slope_analyzer import SlopeAnalyzer, get_negative_intervals_ending_on

# -----------------------------------------------------------
# 1. SETUP: Define global settings
# -----------------------------------------------------------
BASE_URL = "https://hackutd2025.eog.systems"

# --- You can change these ---
# Define the date range to analyze
START_DATE = "2025-10-30"
END_DATE = "2025-11-09" # Inclusive

# How close does the volume need to be to count as a match? (e.g., +/- 1.5 Liters)
VOLUME_TOLERANCE = 1.5
# ----------------------------

# -----------------------------------------------------------
# 2. FETCH ALL COMMON DATA (Cauldrons, Tickets, Levels)
#    We fetch these once to avoid calling the API in a loop.
# -----------------------------------------------------------
print("Fetching all required data one time...")

# Fetch Cauldron List
try:
    cauldrons_response = requests.get(f"{BASE_URL}/api/Information/cauldrons").json()
    all_cauldron_ids = [c['id'] for c in cauldrons_response]
    print(f"Fetched {len(all_cauldron_ids)} cauldrons to analyze.")
except Exception as e:
    print(f"CRITICAL ERROR fetching cauldron list: {e}")
    exit()

# Fetch Transport Tickets
try:
    tickets_response = requests.get(f"{BASE_URL}/api/Tickets").json()
    all_tickets = tickets_response.get('transport_tickets', [])
    print(f"Fetched {len(all_tickets)} total tickets.")
except Exception as e:
    print(f"CRITICAL ERROR fetching tickets: {e}")
    exit()

# Fetch All Cauldron Level Data
try:
    # Fetch all data in one go
    level_data = requests.get(f"{BASE_URL}/api/Data?start_date=0&end_date=1762645088").json()
    
    rows = []
    for entry in level_data:
        timestamp = entry["timestamp"]
        for cid, level in entry["cauldron_levels"].items():
            rows.append([timestamp, cid, level])

    # Load all level data into one big DataFrame
    df_all_levels = pd.DataFrame(rows, columns=["timestamp", "cauldron_id", "level"])
    df_all_levels['timestamp'] = pd.to_datetime(df_all_levels['timestamp'])
    df_all_levels = df_all_levels.sort_values(by="timestamp")
    print(f"Fetched {len(df_all_levels)} total level readings.\n")
    
except Exception as e:
    print(f"CRITICAL ERROR fetching level data: {e}")
    exit()


# -----------------------------------------------------------
# 3. MAIN ANALYSIS LOOP
#    Loop through each DATE, then each CAULDRON.
# -----------------------------------------------------------

# Create a date iterator
try:
    date_iterator = pd.date_range(start=START_DATE, end=END_DATE, freq='D')
    print(f"Starting analysis for {len(date_iterator)} days ({START_DATE} to {END_DATE})\n")
except ValueError as e:
    print(f"Error with date range: {e}. Check START_DATE and END_DATE formats.")
    exit()


total_matches_found = 0

# --- OUTER LOOP: Iterate over each date ---
for current_date_dt in date_iterator:
    # Convert pandas timestamp to a simple datetime.date object
    current_date = current_date_dt.date()
    
    print(f"==================================================")
    print(f"          ANALYZING DATE: {current_date}          ")
    print(f"==================================================\n")

    # --- INNER LOOP: Iterate over each cauldron for this date ---
    for cauldron_id in all_cauldron_ids:
        
        # --- Step 3a: Find Drain Events ---
        
        # Filter the big DataFrame for only this cauldron
        # We use the full df_all_levels, not a pre-filtered one
        df_cauldron = df_all_levels[df_all_levels["cauldron_id"] == cauldron_id]

        if df_cauldron.empty:
            # This is common, so we don't print anything to reduce noise
            continue

        # Run the analysis
        an = SlopeAnalyzer(df_cauldron["timestamp"], df_cauldron["level"], epsilon=20)
        all_inflection_points = an.inflection_points()

        # Find the specific drain events for our *current date in the loop*
        drain_events = get_negative_intervals_ending_on(all_inflection_points, current_date, an)

        # --- Step 3b: Find Relevant Tickets ---
        date_str = current_date.strftime('%Y-%m-%d')
        relevant_tickets = []
        for ticket in all_tickets:
            if ticket['cauldron_id'] == cauldron_id and ticket['date'] == date_str:
                relevant_tickets.append(ticket)

        # --- Step 3c: Skip if no activity ---
        # If there are no drains AND no tickets, skip this cauldron for this day
        if not drain_events and not relevant_tickets:
            continue
            
        # --- Step 3d: Match Events to Tickets ---
        print(f"--- Analyzing: {cauldron_id} ---")
        print(f"Found {len(drain_events)} drain event(s) and {len(relevant_tickets)} ticket(s).")
        
        unmatched_tickets = list(relevant_tickets) # Copy the list for tracking
        cauldron_match_count = 0

        # Loop through each DRAIN event...
        for event in drain_events:
            event_volume = event['drain_volume']
            found_match = False
            
            # ...and compare it to each relevant TICKET
            for ticket in unmatched_tickets:
                ticket_volume = ticket['amount_collected']
                
                if abs(event_volume - ticket_volume) <= VOLUME_TOLERANCE:
                    
                    print("  ✅ MATCH FOUND!")
                    print(f"    [Drain Event] Volume: {event_volume:.2f} L (Ended: {event['end_point'][0]})")
                    print(f"    [Ticket]      Volume: {ticket_volume:.2f} L (ID: {ticket['ticket_id']})")
                    
                    unmatched_tickets.remove(ticket) 
                    found_match = True
                    cauldron_match_count += 1
                    break 
            
            if not found_match:
                print(f"  ❌ NO MATCH for Drain Event (Volume: {event_volume:.2f} L)")
        
        # Print any leftover tickets
        if unmatched_tickets:
            print("\n  ⚠️ Unmatched Tickets (No drain event found):")
            for ticket in unmatched_tickets:
                print(f"    - Ticket ID: {ticket['ticket_id']}, Volume: {ticket['amount_collected']:.2f} L")
        
        if cauldron_match_count > 0:
             print(f"  Summary: {cauldron_match_count} match(es) found for {cauldron_id} on this day.")

        print("--------------------------------" + "-"*len(cauldron_id))
        total_matches_found += cauldron_match_count

    print(f"\n...Finished analysis for {current_date}\n")


print(f"==================================================")
print(f"          ANALYSIS COMPLETE          ")
print(f"Total matches found across all cauldrons")
print(f"from {START_DATE} to {END_DATE}: {total_matches_found}")
print(f"==================================================")