import requests
import pandas as pd
from datetime import date, datetime
import itertools  # <-- 1. IMPORT THIS

# --- Import our custom analyzer tools from the other file ---
from slope_analyzer import SlopeAnalyzer, get_negative_intervals_ending_on

# -----------------------------------------------------------
# 1. SETUP: Define global settings
# -----------------------------------------------------------
BASE_URL = "https://hackutd2025.eog.systems"

# --- You can change these ---
START_DATE = "2025-10-30"
END_DATE = "2025-11-09" # Inclusive
VOLUME_TOLERANCE = 1.5 # +/- 1.5 Liters
# ----------------------------

# -----------------------------------------------------------
# 2. FETCH ALL COMMON DATA (Cauldrons, Tickets, Levels)
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
    level_data = requests.get(f"{BASE_URL}/api/Data?start_date=0&end_date=1762645088").json()
    rows = []
    for entry in level_data:
        timestamp = entry["timestamp"]
        for cid, level in entry["cauldron_levels"].items():
            rows.append([timestamp, cid, level])

    df_all_levels = pd.DataFrame(rows, columns=["timestamp", "cauldron_id", "level"])
    df_all_levels['timestamp'] = pd.to_datetime(df_all_levels['timestamp'])
    df_all_levels = df_all_levels.sort_values(by="timestamp")
    print(f"Fetched {len(df_all_levels)} total level readings.\n")
    
except Exception as e:
    print(f"CRITICAL ERROR fetching level data: {e}")
    exit()


# -----------------------------------------------------------
# 3. MAIN ANALYSIS LOOP
# -----------------------------------------------------------

try:
    date_iterator = pd.date_range(start=START_DATE, end=END_DATE, freq='D')
    print(f"Starting analysis for {len(date_iterator)} days ({START_DATE} to {END_DATE})\n")
except ValueError as e:
    print(f"Error with date range: {e}. Check START_DATE and END_DATE formats.")
    exit()

total_matches_found = 0

# --- OUTER LOOP: Iterate over each date ---
for current_date_dt in date_iterator:
    current_date = current_date_dt.date()
    
    print(f"==================================================")
    print(f"          ANALYZING DATE: {current_date}          ")
    print(f"==================================================\n")

    # --- INNER LOOP: Iterate over each cauldron for this date ---
    for cauldron_id in all_cauldron_ids:
        
        # --- Step 3a: Find Drain Events ---
        df_cauldron = df_all_levels[df_all_levels["cauldron_id"] == cauldron_id]

        if df_cauldron.empty:
            continue

        # Run the analysis
        an = SlopeAnalyzer(df_cauldron["timestamp"], df_cauldron["level"], epsilon=20)
        all_inflection_points = an.inflection_points()

        # --- !! BUG FIX !! ---
        # Pass the growth rate, not the 'an' object
        avg_growth_rate = an.average_positive_slope()
        drain_events = get_negative_intervals_ending_on(
            all_inflection_points, 
            current_date, 
            avg_growth_rate
        )

        # --- Step 3b: Find Relevant Tickets ---
        date_str = current_date.strftime('%Y-%m-%d')
        relevant_tickets = []
        for ticket in all_tickets:
            if ticket['cauldron_id'] == cauldron_id and ticket['date'] == date_str:
                relevant_tickets.append(ticket)

        # --- Step 3c: Skip if no activity ---
        if not drain_events and not relevant_tickets:
            continue
            
        # --- Step 3d: Match Events to Tickets ---
        print(f"--- Analyzing: {cauldron_id} ---")
        print(f"Found {len(drain_events)} drain event(s) and {len(relevant_tickets)} ticket(s).")
        
        unmatched_tickets = list(relevant_tickets) # Full list of tickets to be matched
        unmatched_drains = [] # Drains left over after Phase 1
        cauldron_match_count = 0
        
        print("\n  Phase 1: Attempting 1-to-1 matching...")

        # --- PHASE 1: 1-to-1 Matching ---
        for event in drain_events:
            event_volume = event['drain_volume']
            found_match = False
            
            for ticket in unmatched_tickets:
                ticket_volume = ticket['amount_collected']
                
                if abs(event_volume - ticket_volume) <= VOLUME_TOLERANCE:
                    print("  ✅ [Phase 1] MATCH FOUND!")
                    print(f"    [Drain Event] Volume: {event_volume:.2f} L (Ended: {event['end_point'][0]})")
                    print(f"    [Ticket]      Volume: {ticket_volume:.2f} L (ID: {ticket['ticket_id']})")
                    
                    unmatched_tickets.remove(ticket) 
                    found_match = True
                    cauldron_match_count += 1
                    break 
            
            if not found_match:
                unmatched_drains.append(event) # Add to list for Phase 2

        print(f"  Phase 1 Complete: {cauldron_match_count} match(es) found.")

        # --- PHASE 2: Many-to-One (Sum) Matching ---
        final_unmatched_drains = [] # Drains left over after Phase 2
        if unmatched_drains and unmatched_tickets:
            print("\n  Phase 2: Attempting to match remaining drains by summing tickets...")
            
            # Sort drains largest-first to match big ones first
            for event in sorted(unmatched_drains, key=lambda x: x['drain_volume'], reverse=True):
                event_volume = event['drain_volume']
                found_combo_match = False
                
                # Try combinations from 2 tickets up to all remaining tickets
                for r in range(2, len(unmatched_tickets) + 1):
                    for combo in itertools.combinations(unmatched_tickets, r):
                        combo_sum = sum(ticket['amount_collected'] for ticket in combo)
                        
                        if abs(event_volume - combo_sum) <= VOLUME_TOLERANCE:
                            print("  ✅ [Phase 2] MATCH FOUND (Sum of tickets)")
                            print(f"    [Drain Event] Volume: {event_volume:.2f} L")
                            print(f"    [Tickets Used] Sum: {combo_sum:.2f} L from {len(combo)} tickets:")
                            
                            tickets_in_combo = []
                            for ticket in combo:
                                print(f"      - ID: {ticket['ticket_id']}, Vol: {ticket['amount_collected']:.2f} L")
                                tickets_in_combo.append(ticket)
                            
                            # Rebuild the unmatched_tickets list, removing the ones we used
                            unmatched_tickets = [t for t in unmatched_tickets if t not in tickets_in_combo]
                            
                            found_combo_match = True
                            cauldron_match_count += 1
                            break # Stop checking combos
                    if found_combo_match:
                        break # Stop checking combo sizes (e.g., stop checking r=3 if r=2 worked)

                if not found_combo_match:
                    final_unmatched_drains.append(event) # This drain is truly unmatched
        else:
            final_unmatched_drains = list(unmatched_drains) # No tickets left, all drains are unmatched

        # --- FINAL REPORT for this cauldron/day ---
        if final_unmatched_drains:
            print("\n  ❌ Unmatched Drain Events (No match found in Phase 1 or 2):")
            for event in final_unmatched_drains:
                print(f"    - Drain Event, Volume: {event['drain_volume']:.2f} L (Ended: {event['end_point'][0]})")

        if unmatched_tickets:
            print("\n  ⚠️ Unmatched Tickets (No drain event found):")
            for ticket in unmatched_tickets:
                print(f"    - Ticket ID: {ticket['ticket_id']}, Volume: {ticket['amount_collected']:.2f} L")
        
        print(f"\n  Summary: {cauldron_match_count} total match(es) found for {cauldron_id} on this day.")
        print("--------------------------------" + "-"*len(cauldron_id))
        total_matches_found += cauldron_match_count

    print(f"\n...Finished analysis for {current_date}\n")


print(f"==================================================")
print(f"          ANALYSIS COMPLETE          ")
print(f"Total matches found across all cauldrons")
print(f"from {START_DATE} to {END_DATE}: {total_matches_found}")
print(f"==================================================")