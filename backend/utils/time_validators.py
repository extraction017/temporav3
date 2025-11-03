"""
Time Validation Utilities

Checks if a given time falls within user-defined work hours or sleep hours.
Prevents scheduling events during sleep (protects health) and helps prioritize work hours.
Also provides adjustment logic to move times into valid scheduling windows.
"""

from datetime import timedelta
from .datetime_utils import parse_time_string


def is_during_sleep(dt, prefs):
    """
    Checks if a given datetime falls during the user's sleep hours.
    Prevents scheduling events when the user should be sleeping (health protection).
    
    Handles overnight sleep (e.g., 23:00 - 07:00) where end time < start time.
    
    Args:
        dt: datetime to check
        prefs: user preferences containing 'sleep_start' and 'sleep_end' (e.g., '23:00', '07:00')
        
    Returns:
        True if datetime is during sleep hours, False otherwise
    """
    sleep_start = parse_time_string(prefs['sleep_start'])
    sleep_end = parse_time_string(prefs['sleep_end'])
    dt_time = dt.time()
    
    # Handle overnight sleep: if end < start, sleep crosses midnight
    if sleep_start > sleep_end:
        # During sleep if time >= start OR time < end (e.g., 23:00-07:00: true for 00:30)
        return dt_time >= sleep_start or dt_time < sleep_end
    else:
        # Normal daytime sleep range
        return sleep_start <= dt_time < sleep_end


def is_during_work_hours(dt, prefs):
    """
    Checks if a given datetime falls within the user's work hours.
    Used to prioritize scheduling work events during preferred productive times.
    
    Args:
        dt: datetime to check
        prefs: user preferences containing 'work_start' and 'work_end' (e.g., '09:00', '18:00')
        
    Returns:
        True if datetime is during work hours, False otherwise
    """
    work_start = parse_time_string(prefs['work_start'])
    work_end = parse_time_string(prefs['work_end'])
    dt_time = dt.time()
    
    return work_start <= dt_time < work_end


def adjust_to_work_hours(dt, prefs):
    """
    Moves a datetime into valid work hours if it's currently outside them.
    Used when scheduling needs to find the next available work slot.
    
    Logic:
    - If before work hours (e.g., 07:00 when work starts at 09:00): jump to work start same day
    - If after work hours (e.g., 19:00 when work ends at 18:00): jump to next day's work start
    - If already during work hours: no change
    
    Args:
        dt: datetime to adjust
        prefs: user preferences with 'work_start' and 'work_end'
    
    Returns:
        Adjusted datetime that falls within work hours
    """
    work_start = parse_time_string(prefs['work_start'])
    work_end = parse_time_string(prefs['work_end'])
    dt_time = dt.time()
    
    # Before work: jump to today's work start
    if dt_time < work_start:
        return dt.replace(hour=work_start.hour, minute=work_start.minute, second=0, microsecond=0)
    
    # After work: jump to tomorrow's work start
    if dt_time >= work_end:
        next_day = dt + timedelta(days=1)
        return next_day.replace(hour=work_start.hour, minute=work_start.minute, second=0, microsecond=0)
    
    # Already during work hours
    return dt
