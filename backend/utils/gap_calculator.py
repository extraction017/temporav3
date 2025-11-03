"""
Gap Duration Calculator

Calculates empty time between events (gaps) for health and productivity scoring.
Gaps are important: too short = burnout risk, appropriate = healthy recovery time.
Does NOT create break events - just measures existing gaps for score calculations.
"""

from .datetime_utils import parse_datetime, parse_time_string


def calculate_gap_duration_after_event(event, all_events, preferences):
    """
    Measures the empty time (gap) between this event's end and the next event's start.
    Used by health/productivity scoring to detect insufficient breaks or good spacing.
    
    Strategy:
    1. Find the chronologically next event after this one
    2. Calculate minutes between this event's end and next event's start
    3. Return 0 if gap occurs during sleep (sleep doesn't count as work break)
    
    Example: Meeting ends 14:00, next meeting starts 14:30 → 30 minute gap
    
    Args:
        event: The event to check for gap after it
        all_events: Full event list to find the next event
        preferences: User sleep hours (gaps during sleep don't count)
    
    Returns:
        Gap duration in minutes, or 0 if no next event or gap is during sleep
    """
    event_end = parse_datetime(event['end'])
    
    # Find chronologically next event after this one
    next_event = None
    next_start = None
    
    for e in all_events:
        if e.get('id') == event.get('id'):
            continue  # Skip self
        e_start = parse_datetime(e['start'])
        if e_start > event_end:
            if next_start is None or e_start < next_start:
                next_start = e_start
                next_event = e
    
    if not next_event:
        return 0  # No next event found
    
    # Calculate gap in minutes
    gap_minutes = (next_start - event_end).total_seconds() / 60
    
    # Ignore gaps that occur during sleep hours (sleep ≠ break between work)
    sleep_start = parse_time_string(preferences.get('sleep_start', '23:00'))
    sleep_end = parse_time_string(preferences.get('sleep_end', '07:00'))
    
    gap_start_time = event_end.time()
    
    # Check if gap starts during sleep
    if sleep_start > sleep_end:  # Overnight sleep (23:00 - 07:00)
        if gap_start_time >= sleep_start or gap_start_time < sleep_end:
            return 0  # Gap during sleep doesn't count
    else:  # Daytime sleep
        if sleep_start <= gap_start_time < sleep_end:
            return 0
    
    return max(0, gap_minutes)
