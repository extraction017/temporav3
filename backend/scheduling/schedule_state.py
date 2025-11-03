"""
Schedule State Management Module

Manages global schedule state during optimization.
Tracks occupied slots, daily workload, and makes intelligent scheduling decisions.

Used by OptimizationEngine for batch event scheduling with distribution awareness.
"""

from datetime import datetime, timedelta
from utils.datetime_utils import parse_datetime


class ScheduleState:
    """
    Manages the global schedule state during optimization.
    Tracks occupied slots, daily workload, and makes intelligent scheduling decisions.
    """
    
    def __init__(self, start_date, end_date, preferences):
        """Initialize schedule state."""
        self.start_date = start_date
        self.end_date = end_date
        self.preferences = preferences
        self.days = []
        
        # Generate list of days in range
        current = start_date.date()
        end = end_date.date()
        while current <= end:
            self.days.append(current)
            current += timedelta(days=1)
        
        # Track daily workload (minutes of events per day)
        self.daily_workload = {day: 0 for day in self.days}
        
        # Track occupied time slots [(start, end), ...]
        self.occupied_slots = []
        
        # Track scheduled events for each day
        self.daily_events = {day: [] for day in self.days}
        
        # Parse work hours
        self.work_start = datetime.strptime(preferences.get('work_start', '09:00'), '%H:%M').time()
        self.work_end = datetime.strptime(preferences.get('work_end', '18:00'), '%H:%M').time()
        self.sleep_start = datetime.strptime(preferences.get('sleep_start', '23:00'), '%H:%M').time()
        self.sleep_end = datetime.strptime(preferences.get('sleep_end', '07:00'), '%H:%M').time()
    
    def add_locked_event(self, event):
        """Add a locked event to the schedule (immovable anchor)."""
        start = parse_datetime(event['start'])
        end = parse_datetime(event['end'])
        day = start.date()
        
        self.occupied_slots.append((start, end))
        if day in self.daily_workload:
            duration_minutes = (end - start).total_seconds() / 60
            self.daily_workload[day] += duration_minutes
            self.daily_events[day].append({
                'start': start,
                'end': end,
                'title': event['title'],
                'category': event.get('category', 'Personal'),
                'locked': True
            })
    
    def schedule_batch_with_distribution(self, batch_events):
        """
        Schedule a batch of events with global distribution awareness.
        
        Strategy:
        1. For each event, find ALL valid slots across all days
        2. Score each slot based on:
           - Daily workload balance (prefer less busy days)
           - Health score impact (avoid sleep conflicts, maintain breaks)
           - Productivity score impact (create focus blocks, minimize fragmentation)
           - Preferred time matching (for recurring events)
        3. Choose best slot globally
        
        Returns:
            dict with 'scheduled' and 'failed' lists
        """
        scheduled = []
        failed = []
        
        for event in batch_events:
            print(f"  Scheduling: {event['title']} ({event.get('type', 'event')}, {event.get('priority', 'medium')})")
            
            # Find all valid slots
            valid_slots = self._find_all_valid_slots(event)
            
            if not valid_slots:
                failed.append(event)
                print(f"    ✗ No valid slots found")
                continue
            
            # Score each slot
            scored_slots = []
            for slot_start, slot_end in valid_slots:
                score = self._score_slot(event, slot_start, slot_end)
                scored_slots.append((score, slot_start, slot_end))
            
            # Choose best slot (highest score)
            scored_slots.sort(key=lambda x: x[0], reverse=True)
            best_score, best_start, best_end = scored_slots[0]
            
            # Add to schedule
            self._add_event_to_schedule(event, best_start, best_end)
            
            scheduled.append({
                'id': event['id'],
                'title': event['title'],
                'old_start': event['start'],
                'old_end': event['end'],
                'new_start': best_start.isoformat(),
                'new_end': best_end.isoformat(),
                'reason': f"Score: {best_score:.1f} (optimized for health & productivity)"
            })
            
            print(f"    ✓ Scheduled: {best_start.strftime('%a %H:%M')} (score: {best_score:.1f})")
        
        return {'scheduled': scheduled, 'failed': failed}
    
    def _find_all_valid_slots(self, event):
        """Find all valid time slots for an event across all days."""
        event_type = event.get('type', 'event')
        priority = event.get('priority', 'medium')
        category = event.get('category', 'Personal')
        
        # Calculate duration
        orig_start = parse_datetime(event['start'])
        orig_end = parse_datetime(event['end'])
        duration = orig_end - orig_start
        duration_minutes = int(duration.total_seconds() / 60)
        
        # Get preferred time window if it exists
        preferred_time = event.get('preferred_time', {})
        has_preferred = preferred_time.get('enabled', False) and preferred_time.get('start')
        
        valid_slots = []
        
        # Search through each day
        for day in self.days:
            # Determine search window for this day
            if event_type == 'recurring_instance' and has_preferred:
                # Recurring: strongly prefer the preferred time window
                search_windows = self._get_preferred_time_windows(day, preferred_time)
            elif category in ['Work', 'Meeting']:
                # Work/meetings: stay within work hours
                search_windows = [(
                    datetime.combine(day, self.work_start),
                    datetime.combine(day, self.work_end)
                )]
            else:
                # Other: can use any waking hours (avoid sleep time)
                search_windows = self._get_waking_hours_windows(day)
            
            # Search each window for valid slots
            for window_start, window_end in search_windows:
                # Make sure window is within our date range
                window_start = max(window_start, self.start_date)
                window_end = min(window_end, self.end_date)
                
                # Scan through window in 15-minute increments
                current = window_start
                while current + duration <= window_end:
                    slot_end = current + duration
                    
                    # Check if slot is free
                    if not self._has_conflict(current, slot_end):
                        valid_slots.append((current, slot_end))
                    
                    # Move to next 15-minute increment
                    current += timedelta(minutes=15)
        
        return valid_slots
    
    def _get_preferred_time_windows(self, day, preferred_time):
        """Get preferred time windows for a day."""
        try:
            start_time_str = preferred_time['start']
            end_time_str = preferred_time['end']
            
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            window_start = datetime.combine(day, start_time)
            
            # Handle overnight windows
            if end_time < start_time:
                window_end = datetime.combine(day + timedelta(days=1), end_time)
            else:
                window_end = datetime.combine(day, end_time)
            
            return [(window_start, window_end)]
        except:
            # Fallback to work hours if parsing fails
            return [(
                datetime.combine(day, self.work_start),
                datetime.combine(day, self.work_end)
            )]
    
    def _get_waking_hours_windows(self, day):
        """Get waking hours windows (exclude sleep time)."""
        # Handle overnight sleep
        if self.sleep_start > self.sleep_end:
            # Sleep crosses midnight (e.g., 23:00 - 07:00)
            return [
                (
                    datetime.combine(day, self.sleep_end),
                    datetime.combine(day, self.sleep_start)
                )
            ]
        else:
            # Sleep within same day (e.g., 01:00 - 07:00)
            return [
                (
                    datetime.combine(day, datetime.min.time()),
                    datetime.combine(day, self.sleep_start)
                ),
                (
                    datetime.combine(day, self.sleep_end),
                    datetime.combine(day, datetime.max.time())
                )
            ]
    
    def _has_conflict(self, start, end):
        """Check if a time slot conflicts with existing events."""
        for occupied_start, occupied_end in self.occupied_slots:
            # Check for overlap
            if start < occupied_end and end > occupied_start:
                return True
        return False
    
    def _score_slot(self, event, slot_start, slot_end):
        """
        Score a potential time slot for an event.
        Higher score = better slot.
        
        Scoring factors:
        1. Daily workload balance (prefer less busy days) - 40%
        2. Preferred time matching - 25%
        3. Chronological positioning (earlier in day for important tasks) - 15%
        4. Proximity to original time (for recurring) - 10%
        5. Context switching minimization (group similar categories) - 10%
        """
        score = 0
        day = slot_start.date()
        
        # Factor 1: Daily workload balance (40 points)
        # Prefer days with lower workload for even distribution
        if day in self.daily_workload and len(self.daily_workload) > 0:
            avg_workload = sum(self.daily_workload.values()) / len(self.daily_workload)
            current_workload = self.daily_workload[day]
            
            # Score inversely proportional to current workload
            if avg_workload > 0:
                balance_ratio = 1.0 - (current_workload / (avg_workload * 2))
                score += max(0, balance_ratio * 40)
            else:
                score += 40  # Empty days get full points
        else:
            score += 40  # No workload data = give full points
        
        # Factor 2: Preferred time matching (25 points)
        preferred_time = event.get('preferred_time', {})
        if preferred_time.get('enabled') and preferred_time.get('start'):
            try:
                pref_start_str = preferred_time['start']
                pref_start_time = datetime.strptime(pref_start_str, '%H:%M').time()
                
                # How close is this slot to preferred time?
                slot_time = slot_start.time()
                time_diff_minutes = abs(
                    (datetime.combine(day, slot_time) - 
                     datetime.combine(day, pref_start_time)).total_seconds() / 60
                )
                
                # Full points if exact match, decay with distance
                if time_diff_minutes == 0:
                    score += 25
                else:
                    score += 25 * (1 / (1 + time_diff_minutes / 60))  # Exponential decay
            except:
                pass
        
        # Factor 3: Chronological positioning (15 points)
        # High-priority work/meetings benefit from earlier scheduling
        category = event.get('category', 'Personal')
        priority = event.get('priority', 'medium')
        
        if category in ['Work', 'Meeting'] and priority == 'high':
            # Prefer morning/early afternoon for important tasks
            hour = slot_start.hour
            if 9 <= hour <= 12:
                score += 15  # Peak productivity hours
            elif 13 <= hour <= 15:
                score += 10  # Still good
            else:
                score += 5   # Acceptable
        else:
            score += 10  # Neutral for other events
        
        # Factor 4: Proximity to original time for recurring events (10 points)
        event_type = event.get('type', 'event')
        if event_type == 'recurring_instance':
            orig_start = parse_datetime(event['start'])
            time_diff_hours = abs((slot_start - orig_start).total_seconds() / 3600)
            
            # Prefer keeping recurring events close to original time
            if time_diff_hours <= 1:
                score += 10
            elif time_diff_hours <= 3:
                score += 7
            elif time_diff_hours <= 6:
                score += 4
            else:
                score += 2
        else:
            score += 5  # Neutral for non-recurring
        
        # Factor 5: Context switching minimization (10 points)
        # Prefer grouping similar categories together
        if day in self.daily_events:
            event_category = event.get('category', 'Personal')
            same_category_count = sum(
                1 for e in self.daily_events[day]
                if e.get('category') == event_category
            )
            
            # Bonus for grouping with similar events
            if same_category_count > 0:
                score += min(10, same_category_count * 3)
        
        return score
    
    def _add_event_to_schedule(self, event, start, end):
        """Add an event to the schedule state."""
        day = start.date()
        
        # Add to occupied slots
        self.occupied_slots.append((start, end))
        
        # Update daily workload
        if day in self.daily_workload:
            duration_minutes = (end - start).total_seconds() / 60
            self.daily_workload[day] += duration_minutes
        
        # Add to daily events
        if day in self.daily_events:
            self.daily_events[day].append({
                'start': start,
                'end': end,
                'title': event['title'],
                'category': event.get('category', 'Personal'),
                'locked': False
            })
    
    def print_daily_distribution(self):
        """Print daily workload distribution for debugging."""
        print("\nDaily Workload Distribution:")
        for day in self.days:
            workload = self.daily_workload.get(day, 0)
            event_count = len(self.daily_events.get(day, []))
            hours = workload / 60
            bar = "█" * int(hours)
            print(f"  {day.strftime('%A %m/%d'):15s} [{event_count:2d} events, {hours:4.1f}h] {bar}")
    
    def generate_smart_breaks(self):
        """
        DEPRECATED: Breaks are now virtual (calculated from gaps).
        This method is kept for backward compatibility but does nothing.
        
        Returns:
            Number of breaks generated (always 0)
        """
        print("  Note: Breaks are now virtual (calculated from gaps between events)")
        return 0


def classify_events_for_optimization(events):
    """
    Classify events by priority for batch processing.
    
    Returns:
        dict with keys: locked, high, medium, low
    """
    classified = {
        'locked': [],   # Immovable events (never touch these)
        'high': [],     # High-priority events (schedule first)
        'medium': [],   # Medium-priority events (schedule second)
        'low': []       # Low-priority events (schedule last)
    }
    
    for event in events:
        # Locked events are immovable anchors
        if event.get('locked'):
            classified['locked'].append(event)
            continue
        
        # Classify by priority
        priority = event.get('priority', 'medium')
        if priority == 'high':
            classified['high'].append(event)
        elif priority == 'medium':
            classified['medium'].append(event)
        else:
            classified['low'].append(event)
    
    return classified
