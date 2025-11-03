"""
Slot Finder Module

Finds available time slots for events and scores them by quality.
Smart scheduling: collects multiple options, scores each, returns the BEST one.
Scoring considers: work hours fit, spacing from other events, workload balance, time of day.
This prevents cramming all events together - creates healthy, balanced schedules.
"""

from datetime import datetime, timedelta
from utils.datetime_utils import parse_datetime, round_to_interval, parse_time_string
from utils.time_validators import is_during_sleep, adjust_to_work_hours
from database import db


def find_available_slot(start_time, end_time, duration, interval_minutes=15):
    """
    Finds the BEST available time slot (not just the first empty one).
    Creates balanced schedules by scoring multiple options and choosing the highest-quality slot.
    
    How it works:
    1. Scans through time range, checking every 15 minutes (or user's preference)
    2. Skips sleep hours and checks for conflicts with existing events
    3. Collects up to 50 valid candidate slots
    4. Scores each based on work hours fit, spacing, workload, time of day
    5. Returns the highest-scoring slot
    
    Result: Events are well-spaced and balanced across days instead of crammed together.
    
    Args:
        start_time: earliest possible start time for event
        end_time: latest possible end time (deadline)
        duration: how long the event needs to be (timedelta object)
        interval_minutes: how often to check for slots (default 15 min)
    
    Returns:
        (start_datetime, end_datetime) tuple of best slot, or None if no valid slot exists
    """
    # Get user preferences and existing events to make smart decisions
    prefs = db.get_user_preferences()
    round_to = prefs['round_to_minutes']
    all_events = db.get_all_events()
    
    work_start = parse_time_string(prefs['work_start'])
    work_end = parse_time_string(prefs['work_end'])
    
    current_time = start_time
    
    # Round to user's preferred interval (cleaner times: 14:15 instead of 14:07)
    current_time = round_to_interval(current_time, round_to)
    
    # Collect up to 50 valid slots for scoring
    candidate_slots = []
    max_candidates = 50
    
    while current_time + duration <= end_time and len(candidate_slots) < max_candidates:
        # Skip sleep hours - jump to wake time
        if is_during_sleep(current_time, prefs):
            wake_time = parse_time_string(prefs['sleep_end'])
            current_time = current_time.replace(
                hour=wake_time.hour,
                minute=wake_time.minute,
                second=0,
                microsecond=0
            )
            # If we jumped backward, move forward a day
            if current_time < start_time:
                current_time += timedelta(days=1)
            current_time = round_to_interval(current_time, round_to)
            continue
        
        # Check if event would extend into sleep hours
        slot_end = current_time + duration
        if is_during_sleep(slot_end, prefs):
            # Skip to next work day
            current_time = adjust_to_work_hours(current_time + timedelta(days=1), prefs)
            current_time = round_to_interval(current_time, round_to)
            continue
        
        proposed_event = {
            "start": current_time.isoformat(),
            "end": slot_end.isoformat()
        }
        
        # Check for conflicts with existing events
        if not db.check_conflicts(proposed_event["start"], proposed_event["end"]):
            candidate_slots.append((current_time, slot_end))
        
        # Move forward by rounding interval
        current_time += timedelta(minutes=round_to)
    
    # No valid slots found
    if not candidate_slots:
        return None
    
    # Only one option - return it
    if len(candidate_slots) == 1:
        return candidate_slots[0]
    
    # Score all candidates and pick the best
    scored_slots = []
    for slot_start, slot_end in candidate_slots:
        score = score_slot_quality(slot_start, slot_end, all_events, prefs, work_start, work_end,
                                    preferred_time_config=None, earliest_start=start_time)
        scored_slots.append((score, slot_start, slot_end))
    
    # Sort by score (highest = best) and return winner
    scored_slots.sort(key=lambda x: x[0], reverse=True)
    best_score, best_start, best_end = scored_slots[0]
    
    return best_start, best_end


def score_slot_quality(slot_start, slot_end, all_events, prefs, work_start, work_end, 
                       preferred_time_config=None, earliest_start=None):
    """
    Rates how good a time slot is by assigning points for quality factors.
    Higher score = better placement = chosen by scheduler.
    
    TWO DIFFERENT SCORING MODES:
    
    MODE 1: When NO preferred time is specified (flexible events):
        Scores based on general schedule quality:
        - Work hours fit (30 pts): Prefer times well within work hours, avoid edges
        - Event spacing (20 pts): Prefer slots with breathing room before/after
        - Workload balance (15 pts): Prefer less busy days to avoid overload
        - Time of day (10 pts): Prefer mid-morning (10am) or mid-afternoon (2pm)
        - Proximity (2 pts): Tiny tiebreaker to prefer earlier days if equal
        Maximum: 77 points
    
    MODE 2: When preferred time IS specified (e.g., "I want this at 10:00-11:00"):
        Scores ONLY based on matching that preferred time:
        - Exact match (50 pts): Slot falls within preferred window
        - Within ±1 hour (35 pts): Close to preferred time
        - Within ±2 hours (20 pts): Somewhat close
        - In work hours (10 pts): At least during work
        - Outside work (0 pts): Last resort
        - Proximity (2 pts): Tiny tiebreaker
        Maximum: 52 points
    
    Why two modes? Preferred time should DOMINATE - we don't want spacing or workload
    interfering with "schedule this at 10am". But flexible events should be smart about
    creating balanced, healthy schedules.
    """
    score = 0
    slot_date = slot_start.date()
    slot_time = slot_start.time()
    
    # === FACTOR 1: Preferred Time Matching (50 pts) - MODE 2 ONLY ===
    # This completely dominates when user says "schedule at 10am"
    if preferred_time_config and preferred_time_config.get("enabled"):
        pref_start_str = preferred_time_config.get("start")
        pref_end_str = preferred_time_config.get("end")
        
        if pref_start_str and pref_end_str:
            pref_start = parse_time_string(pref_start_str)
            pref_end = parse_time_string(pref_end_str)
            
            # Handle overnight ranges (22:00 - 06:00 crosses midnight)
            is_overnight = pref_end <= pref_start
            
            if is_overnight:
                # Check if slot is in overnight range
                in_preferred = slot_time >= pref_start or slot_time < pref_end
            else:
                # Normal range check
                in_preferred = pref_start <= slot_time < pref_end
            
            if in_preferred:
                score += 50  # Perfect! Exactly when user wanted
            else:
                # Calculate minutes away from preferred window
                slot_minutes = slot_time.hour * 60 + slot_time.minute
                pref_start_minutes = pref_start.hour * 60 + pref_start.minute
                pref_end_minutes = pref_end.hour * 60 + pref_end.minute
                
                if is_overnight:
                    # Distance calculation for overnight windows
                    if slot_minutes >= pref_start_minutes:
                        distance = min(slot_minutes - pref_end_minutes, pref_start_minutes - slot_minutes)
                    else:
                        distance = min(pref_start_minutes - slot_minutes, slot_minutes + (24*60 - pref_end_minutes))
                else:
                    # Distance from normal window
                    if slot_minutes < pref_start_minutes:
                        distance = pref_start_minutes - slot_minutes
                    else:
                        distance = slot_minutes - pref_end_minutes
                
                # Score based on how far from preferred time
                if distance <= 60:  # Within ±1 hour: close enough
                    score += 35
                elif distance <= 120:  # Within ±2 hours: somewhat close
                    score += 20
                elif work_start <= slot_time < work_end:  # At least during work
                    score += 10
                else:
                    score += 0  # Far from preferred time
    
    # === FACTOR 2: Work Hours Fit (30 pts) - MODE 1 ONLY ===
    # When no preferred time, prefer center of work day over edges
    if not (preferred_time_config and preferred_time_config.get("enabled")):
        if work_start <= slot_time < work_end:
            # Calculate distance from work hour edges
            minutes_from_start = (slot_start - datetime.combine(slot_date, work_start)).total_seconds() / 60
            minutes_from_end = (datetime.combine(slot_date, work_end) - slot_end).total_seconds() / 60
            
            edge_distance = min(minutes_from_start, minutes_from_end)
            if edge_distance >= 60:
                score += 30  # Well within work hours (1+ hour from edges)
            elif edge_distance >= 30:
                score += 25  # Decent spacing from edges
            else:
                score += 20  # Near edges but acceptable
        else:
            score += 5  # Outside work hours (last resort)
    
    # === FACTOR 3: Event Spacing (20 pts) - MODE 1 ONLY ===
    # Prefer slots with breathing room before/after (avoid back-to-back cramming)
    if not (preferred_time_config and preferred_time_config.get("enabled")):
        gap_before = 999  # Large default (no event nearby)
        gap_after = 999
        
        for event in all_events:
            event_start = parse_datetime(event.get('start'))
            event_end = parse_datetime(event.get('end'))
            
            if not event_start or not event_end:
                continue
            
            # Measure gap before this slot
            if event_end <= slot_start:
                minutes_gap = (slot_start - event_end).total_seconds() / 60
                gap_before = min(gap_before, minutes_gap)
            
            # Measure gap after this slot
            if event_start >= slot_end:
                minutes_gap = (event_start - slot_end).total_seconds() / 60
                gap_after = min(gap_after, minutes_gap)
        
        # Score based on average spacing
        avg_gap = (gap_before + gap_after) / 2
        if avg_gap >= 60:
            score += 20  # Great spacing (1+ hour buffer)
        elif avg_gap >= 30:
            score += 15  # Good spacing (30+ min buffer)
        elif avg_gap >= 15:
            score += 8   # Minimal spacing (15+ min buffer)
        else:
            score += 0   # Crammed (back-to-back events)
    
    # === FACTOR 4: Daily Workload Balance (15 pts) - MODE 1 ONLY ===
    # Prefer days with fewer existing events (avoid overloading single day)
    if not (preferred_time_config and preferred_time_config.get("enabled")):
        same_day_events = [e for e in all_events 
                           if parse_datetime(e.get('start')) and 
                           parse_datetime(e.get('start')).date() == slot_date]
        
        same_day_duration = sum(
            (parse_datetime(e.get('end')) - parse_datetime(e.get('start'))).total_seconds() / 60
            for e in same_day_events
            if parse_datetime(e.get('start')) and parse_datetime(e.get('end'))
        )
        
        # Reward lighter days
        if same_day_duration < 180:  # Less than 3 hours scheduled
            score += 15
        elif same_day_duration < 300:  # Less than 5 hours
            score += 12
        elif same_day_duration < 420:  # Less than 7 hours
            score += 8
        else:  # Very busy day (7+ hours)
            score += 4
    
    # === FACTOR 5: Time of Day Preference (10 pts) - MODE 1 ONLY ===
    # Prefer peak productivity hours: mid-morning and mid-afternoon
    if not (preferred_time_config and preferred_time_config.get("enabled")):
        hour = slot_start.hour
        if 10 <= hour < 11 or 14 <= hour < 16:
            score += 10  # Prime productivity hours (10-11am, 2-4pm)
        elif 9 <= hour < 10 or 11 <= hour < 14 or 16 <= hour < 17:
            score += 7   # Good hours
        else:
            score += 3   # Early morning or late afternoon
    
    # === FACTOR 6: Proximity (2 pts) - BOTH MODES ===
    # Tiny tiebreaker: prefer earlier days when everything else is equal
    # Intentionally small (1.5% of score) to not override quality factors
    if earliest_start:
        days_from_start = (slot_start.date() - earliest_start.date()).days
        
        if days_from_start == 0:
            score += 2.0  # Same day as earliest possible
        elif days_from_start <= 3:
            score += 1.5  # Within 3 days
        elif days_from_start <= 7:
            score += 1.0  # Within a week
        elif days_from_start <= 14:
            score += 0.5  # Within 2 weeks
        else:
            score += 0.0  # Distant future
    
    return score
