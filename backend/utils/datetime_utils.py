"""
Date/Time Parsing Utilities

Translates text-based timestamps from the frontend into Python datetime objects.
Cleans up different formats (ISO 8601, timezone markers, milliseconds) so the backend can work with them.
"""

from datetime import datetime, timedelta


def parse_datetime(date_string):
    """
    Converts timestamp strings into Python datetime objects for date calculations.
    Cleans formats like '2025-11-03T14:30:00Z' or '14:30:00.123' → clean datetime object.
    
    Args:
        date_string: Timestamp text (ISO format: YYYY-MM-DDTHH:MM:SS)
        
    Returns:
        Python datetime object or None if empty/invalid
    """
    if not date_string:
        return None

    # Remove 'Z' suffix (UTC timezone marker): '2025-11-03T14:30:00Z' → '2025-11-03T14:30:00'
    if date_string.endswith('Z'):
        date_string = date_string[:-1]
    
    # Remove milliseconds for simpler parsing: '14:30:00.123' → '14:30:00'
    if '.' in date_string:
        date_string = date_string.split('.')[0]
        
    try:
        # Parse full timestamp: YYYY-MM-DDTHH:MM:SS
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        try:
            # Fallback: parse without seconds: YYYY-MM-DDTHH:MM
            return datetime.strptime(date_string, "%Y-%m-%dT%H:%M")
        except ValueError:
            # Invalid format
            raise ValueError(f"Invalid datetime format: {date_string}")


def parse_time_string(time_string):
    """
    Converts time-only strings (e.g., '09:00', '18:30') into Python time objects.
    Used for work hours, sleep times, and preferred time windows.
    
    Args:
        time_string: Time text in 24-hour format 'HH:MM'
        
    Returns:
        Python time object (no date attached)
    """
    try:
        return datetime.strptime(time_string, "%H:%M").time()
    except ValueError:
        raise ValueError(f"Invalid time format: {time_string}")


def round_to_interval(dt, minutes):
    """
    Snaps event times to clean intervals (prevents messy times like 14:07, rounds to 14:10).
    Creates neater schedules by rounding to user's preferred interval (5, 10, 15, or 30 minutes).
    
    Example: If interval=15, then 14:07 → 14:15, 14:15 → 14:15, 14:22 → 14:30
    
    Args:
        dt: datetime object to round
        minutes: rounding interval (5, 10, 15, or 30 minutes)
        
    Returns:
        Rounded datetime object (always rounds UP to next interval)
    """
    minute = dt.minute
    remainder = minute % minutes
    
    if remainder == 0:
        return dt  # Already aligned to interval
    
    # Round UP to next interval boundary
    return dt.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=(minute // minutes + 1) * minutes)


def parse_preferred_time(preferred_time):
    """
    Parses preferred time window strings (e.g., '09:00 - 17:00' or '22:00 - 02:00').
    Detects overnight windows where end time is before start time (like '22:00 - 02:00' crosses midnight).
    
    Args:
        preferred_time: Time range text like '09:00 - 17:00' or None
        
    Returns:
        Tuple (start_time, end_time, is_overnight_bool)
        Example: ('09:00', '17:00', False) or ('22:00', '02:00', True)
    """
    if not preferred_time:
        return None, None, False  # No preferred time specified (for fixed events)
    
    try:
        # Split at hyphen: '09:00 - 17:00' → ['09:00', '17:00']
        start_time, end_time = preferred_time.split("-")
        
        # Remove extra spaces and convert to time objects
        start = datetime.strptime(start_time.strip(), "%H:%M").time()
        end = datetime.strptime(end_time.strip(), "%H:%M").time()
        
        # Detect overnight windows: if end ≤ start, it crosses midnight (22:00 - 02:00)
        is_overnight = end <= start
        
        return start, end, is_overnight
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid preferred time format: {preferred_time}")
