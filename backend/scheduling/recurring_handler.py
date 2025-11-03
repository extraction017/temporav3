"""
Recurring Event Handler Module

Schedules repeating events (e.g., weekly team meeting) with smart fallback strategy.
If the exact preferred time is full, it gradually widens the search window:
1. Try exact preferred window (e.g., 10:00-11:00) - HIGHEST PRIORITY
2. Expand slightly (±1 hour: 09:00-12:00)
3. Expand to full work hours (09:00-18:00)
4. Try entire day (00:00-23:59) - LAST RESORT

Each instance (each week's meeting) tries all 4 levels independently before giving up.
This ensures most instances get the preferred time, while flexible instances find alternatives.
"""

from datetime import datetime, timedelta
from utils.datetime_utils import parse_datetime, parse_time_string, parse_preferred_time
from scheduling.slot_finder import find_available_slot
from database import db


def handle_recurring_event(data, new_event):
    """
    Schedules a recurring event with progressive fallback when preferred times are full.
    
    Example: Weekly team meeting every Monday 10:00-11:00 for next 30 days.
    - Week 1 Monday: Tries 10:00-11:00 → Success!
    - Week 2 Monday: 10:00-11:00 full → Tries 09:00-12:00 → Success at 11:15!
    - Week 3 Monday: 09:00-12:00 full → Tries 09:00-18:00 → Success at 15:00!
    - Week 4 Monday: All day full → Fails (or finds last resort slot)
    
    Fallback strategy per instance:
    1. Exact preferred window (top priority)
    2. Expanded ±1 hour
    3. Full work hours
    4. Entire day (last resort)
    
    Args:
        data: Event details from frontend (title, duration, frequency, preferred_time, etc.)
        new_event: Parent event dict to link instances to
    
    Returns:
        True if at least one instance was scheduled, False if all failed
    """
    # Validate duration
    duration_minutes = int(data["duration"])
    if duration_minutes <= 0:
        print("ERROR: Duration must be greater than 0")
        return False
    
    duration = timedelta(minutes=duration_minutes)
    frequency = int(data["frequency"])
    
    if frequency <= 0:
        print("ERROR: Frequency must be greater than 0")
        return False
    
    start_date = parse_datetime(data.get("start_date"))
    if not start_date:
        return False
    
    # Prevent scheduling in the past - adjust to today if needed
    now = datetime.now()
    if start_date < now:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        print(f"  Note: Adjusted start_date from past to today ({start_date.date()})")
    
    end_date = start_date + timedelta(days=30)  # Schedule 30 days ahead
    scheduled_instances = []
    fallback_stats = {"exact": 0, "expanded": 0, "work_hours": 0, "full_day": 0, "failed": 0}
    current_date = start_date
    preferred_time_config = data.get("preferred_time", {})
    has_preferred_time = preferred_time_config.get("enabled", False)
    
    # Get user's work hours for fallback levels
    prefs = db.get_user_preferences()
    work_start = parse_time_string(prefs.get('work_start', '09:00'))
    work_end = parse_time_string(prefs.get('work_end', '18:00'))
    
    # Loop through each occurrence (every frequency days)
    while current_date <= end_date:
        # Skip past dates
        if current_date < now:
            current_date += timedelta(days=frequency)
            continue
        
        slot = None
        fallback_level = None
        
        if has_preferred_time and preferred_time_config.get("start") and preferred_time_config.get("end"):
            try:
                # Parse preferred time window (e.g., "10:00 - 11:00")
                pref_time_str = f"{preferred_time_config['start']} - {preferred_time_config['end']}"
                pref_start, pref_end, is_overnight = parse_preferred_time(pref_time_str)
                
                # Build time window for this instance's day
                if is_overnight:
                    next_date = current_date.date() + timedelta(days=1)
                    pref_window_start = datetime.combine(current_date.date(), pref_start)
                    pref_window_end = datetime.combine(next_date, pref_end)
                else:
                    pref_window_start = datetime.combine(current_date.date(), pref_start)
                    pref_window_end = datetime.combine(current_date.date(), pref_end)
                
                # === LEVEL 1: Try exact preferred window ===
                # Example: 10:00-11:00 if that's what user requested
                slot = find_available_slot(pref_window_start, pref_window_end, duration)
                if slot:
                    fallback_level = "exact"
                    fallback_stats["exact"] += 1
                
                # === LEVEL 2: Expand ±1 hour ===
                # Example: 09:00-12:00 if 10:00-11:00 was full
                if not slot:
                    expanded_start = pref_window_start - timedelta(hours=1)
                    expanded_end = pref_window_end + timedelta(hours=1)
                    slot = find_available_slot(expanded_start, expanded_end, duration)
                    if slot:
                        fallback_level = "expanded"
                        fallback_stats["expanded"] += 1
                
                # === LEVEL 3: Expand to full work hours ===
                # Example: 09:00-18:00 if expanded window was full
                if not slot:
                    work_window_start = datetime.combine(current_date.date(), work_start)
                    work_window_end = datetime.combine(current_date.date(), work_end)
                    slot = find_available_slot(work_window_start, work_window_end, duration)
                    if slot:
                        fallback_level = "work_hours"
                        fallback_stats["work_hours"] += 1
                
                # === LEVEL 4: Try entire day (last resort) ===
                # Example: 00:00-23:59 if work hours were full
                if not slot:
                    day_start = current_date.replace(hour=0, minute=0, second=0)
                    day_end = current_date.replace(hour=23, minute=59, second=59)
                    slot = find_available_slot(day_start, day_end, duration)
                    if slot:
                        fallback_level = "full_day"
                        fallback_stats["full_day"] += 1
                    
            except ValueError as e:
                print(f"Error parsing preferred time: {e}")
                return False
        else:
            # No preferred time specified - try whole day
            day_start = current_date.replace(hour=0, minute=0, second=0)
            day_end = current_date.replace(hour=23, minute=59, second=59)
            slot = find_available_slot(day_start, day_end, duration)
            if slot:
                fallback_level = "no_preference"
        
        if slot:
            # Found a slot! Create this instance
            instance = {
                "title": data["title"],
                "priority": data["priority"],
                "category": data.get("category", "Personal"),
                "type": "recurring_instance",
                "start": slot[0].isoformat(),
                "end": slot[1].isoformat(),
                "parent_id": new_event.get("id"),
                "duration": int(data["duration"]),
                "frequency": int(data["frequency"]),
                "preferred_time": data.get("preferred_time", {})
            }
            scheduled_instances.append(instance)
            db.create_event(instance)
            
            # Log when fallback was used (not at exact preferred time)
            if fallback_level and fallback_level != "exact" and fallback_level != "no_preference":
                print(f"  Instance on {current_date.date()}: Used {fallback_level} fallback")
        else:
            # No slot found even after all 4 levels - instance failed
            fallback_stats["failed"] += 1
            print(f"  WARNING: Could not schedule instance on {current_date.date()}")
        
        # Move to next occurrence
        current_date += timedelta(days=frequency)
    
    # Print summary showing how well we matched preferred times
    if has_preferred_time and scheduled_instances:
        total = len(scheduled_instances)
        exact_pct = (fallback_stats["exact"] / total * 100) if total > 0 else 0
        print(f"\nRecurring Event Scheduling Summary:")
        print(f"  Total instances: {total}")
        print(f"  Exact preferred time: {fallback_stats['exact']} ({exact_pct:.0f}%)")
        if fallback_stats["expanded"] > 0:
            print(f"  Expanded window (±1 hour): {fallback_stats['expanded']}")
        if fallback_stats["work_hours"] > 0:
            print(f"  Work hours fallback: {fallback_stats['work_hours']}")
        if fallback_stats["full_day"] > 0:
            print(f"  Full day fallback: {fallback_stats['full_day']}")
        if fallback_stats["failed"] > 0:
            print(f"  Failed to schedule: {fallback_stats['failed']}")
    
    return bool(scheduled_instances)  # Success if at least one instance was scheduled
