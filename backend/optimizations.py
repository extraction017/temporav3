"""
TEMPORA Optimization Engine
Provides one-click fixes for common schedule problems identified by scoring systems.

Each optimization function:
1. Analyzes current schedule
2. Applies research-based corrections
3. Returns modified events + predicted score improvement
"""

from datetime import datetime, timedelta
from collections import defaultdict
import copy


class OptimizationEngine:
    """Applies automated optimizations to improve schedule health and productivity."""
    
    def __init__(self, events, preferences):
        """
        Initialize with current schedule.
        
        Args:
            events: List of event dictionaries
            preferences: User preferences dictionary
        """
        self.events = events
        self.preferences = preferences
        self.today = datetime.now().date()  # Track current date to prevent past modifications
        self.work_events = [e for e in events if e.get('category') == 'Work']
        self.meetings = [e for e in events if e.get('category') == 'Meeting']
        self.personal_events = [e for e in events if e.get('category') == 'Personal']
        self.recreational = [e for e in events if e.get('category') == 'Recreational']
    
    def _is_past_event(self, event):
        """Check if an event is in the past (cannot be modified)."""
        start = self._parse_iso(event['start'])
        return start.date() < self.today
    
    def smart_optimize_week(self):
        """
        WORKLOAD BALANCING: Distribute events evenly across the week by total duration,
        while respecting preferred times and using intelligent slot scoring.
        
        PURPOSE: Balance workload to prevent asymmetrical schedules (e.g., 8 hours Mon, 2 hours Tue).
        This is LOAD BALANCING by duration, not score optimization.
        
        ALGORITHM:
        1. Start with locked events in simulation (immovable anchors)
        2. Sort moveable events by priority/type/category
        3. For EACH event:
           a) Calculate total DURATION on each day in simulation
           b) Choose day with LEAST total duration (CRITICAL for workload balancing)
           c) Find best-fit time slot on that day using:
              - Progressive fallback (preferred time → ±1hr → work hours → full day)
              - Multi-criteria scoring (preferred time match, work hours, spacing, category fit)
           d) Add to simulation
        4. Result: Events distributed evenly across days by total hours
        
        WORKLOAD BALANCING GUARANTEE:
        Line 149: `best_day = min(week_days, key=lambda d: daily_durations[d])`
        This ensures each event goes to the day with lowest total duration, preventing
        asymmetrical workloads (e.g., prevents 8h Mon + 1h Tue, ensures ~4.5h Mon + 4.5h Tue).
        
        NOTE: Break events no longer exist in the system. Gaps are implicit.
        
        Returns:
            dict with modifications and even workload distribution
        """
        modifications = []
        recommendations = []
        
        # Get preferences
        work_start = datetime.strptime(self.preferences.get('work_start', '09:00'), '%H:%M').time()
        work_end = datetime.strptime(self.preferences.get('work_end', '18:00'), '%H:%M').time()
        
        # Get week date range
        all_dates = sorted(set(self._parse_iso(e['start']).date() for e in self.events))
        if not all_dates:
            return {'modifications': [], 'recommendations': [], 'message': 'No events to optimize'}
        
        week_start = all_dates[0]
        week_days = [week_start + timedelta(days=i) for i in range(7)]
        
        # Separate events: locked (never move) vs moveable (reschedule)
        # NOTE: Break events were completely removed from the system
        locked_events = [e for e in self.events if e.get('locked')]
        
        # CRITICAL: Filter out past events - they cannot be modified
        moveable_events = [e for e in self.events 
                          if not e.get('locked') 
                          and not self._is_past_event(e)]
        
        # Track how many events were excluded for being in the past
        past_events_count = len([e for e in self.events 
                                if not e.get('locked') 
                                and self._is_past_event(e)])
        
        if not moveable_events:
            msg = 'No moveable events'
            if past_events_count > 0:
                msg += f' (excluded {past_events_count} past events - cannot modify history)'
            return {'modifications': [], 'recommendations': [], 'message': msg}
        
        print(f"\n=== WORKLOAD BALANCING START ===")
        print(f"Total events: {len(self.events)}")
        print(f"  Locked: {len(locked_events)}")
        print(f"  Moveable: {len(moveable_events)}")
        print(f"Target: {len(moveable_events)/7.0:.1f} moveable events/day")
        
        # STEP 1: Create simulation with ONLY locked events
        simulated_schedule = []
        for event in locked_events:
            simulated_schedule.append(copy.deepcopy(event))
        
        print(f"\nStarting simulation with {len(simulated_schedule)} locked events")
        
        # STEP 2: Sort moveable events
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        type_order = {'fixed': 0, 'recurring': 1, 'floating': 2}
        category_order = {'Work': 0, 'Meeting': 1, 'Recreational': 2, 'Meal': 3, 'Personal': 4}
        
        def sort_key(event):
            priority = priority_order.get(event.get('priority', 'medium'), 1)
            event_type = type_order.get(event.get('type', 'floating'), 2)
            category = category_order.get(event.get('category', 'Personal'), 4)
            original_time = self._parse_iso(event['start'])
            return (priority, event_type, category, original_time)
        
        sorted_events = sorted(moveable_events, key=sort_key)
        
        print(f"\n=== SCHEDULING {len(sorted_events)} EVENTS ===\n")
        
        # STEP 3: Schedule ONE event at a time
        for idx, event in enumerate(sorted_events):
            orig_start = self._parse_iso(event['start'])
            orig_end = self._parse_iso(event['end'])
            duration = orig_end - orig_start
            category = event.get('category', 'Personal')
            
            # CRITICAL FIX: Track TOTAL DURATION on each day, not just event count
            # (includes both locked events AND already-scheduled moveable events)
            daily_durations = defaultdict(int)  # minutes per day
            for sim_event in simulated_schedule:
                day = self._parse_iso(sim_event['start']).date()
                if day in week_days:  # Only count events in this week
                    event_start = self._parse_iso(sim_event['start'])
                    event_end = self._parse_iso(sim_event['end'])
                    duration_minutes = (event_end - event_start).total_seconds() / 60
                    daily_durations[day] += duration_minutes
            
            # Initialize days with 0 if not present
            for day in week_days:
                if day not in daily_durations:
                    daily_durations[day] = 0
            
            # Find day with LEAST total time scheduled (true workload balancing)
            best_day = min(week_days, key=lambda d: daily_durations[d])
            
            # Time preference by category
            if category in ['Work', 'Meeting']:
                search_time = work_start
            elif category == 'Meal':
                search_time = datetime.strptime('12:00', '%H:%M').time()
            else:
                search_time = datetime.strptime('14:00', '%H:%M').time()
            
            search_start = datetime.combine(best_day, search_time)
            
            # Extract preferred time window if event has one
            preferred_time_window = None
            preferred_time = event.get('preferred_time', {})
            if preferred_time and preferred_time.get('enabled') and preferred_time.get('start') and preferred_time.get('end'):
                try:
                    pref_start_str = preferred_time['start']
                    pref_end_str = preferred_time['end']
                    pref_start_time = datetime.strptime(pref_start_str, '%H:%M').time()
                    pref_end_time = datetime.strptime(pref_end_str, '%H:%M').time()
                    preferred_time_window = (pref_start_time, pref_end_time)
                except (ValueError, KeyError):
                    # If preferred time parsing fails, continue without it
                    pass
            
            # Find available slot using simulation
            old_events = self.events
            self.events = simulated_schedule
            
            available_slot = self._find_next_available_slot(
                search_start, duration, best_day, work_start, work_end, event['id'],
                event_category=category, event_priority=event.get('priority', 'medium'),
                preferred_time_window=preferred_time_window
            )
            
            self.events = old_events
            
            if available_slot:
                new_start = available_slot
                new_end = available_slot + duration
                
                # Always add modification (we're rescheduling everything)
                modifications.append({
                    'id': event['id'],
                    'title': event['title'],
                    'old_start': event['start'],
                    'old_end': event['end'],
                    'new_start': new_start.isoformat(),
                    'new_end': new_end.isoformat(),
                    'reason': f'{category} ({best_day.strftime("%a")} had {daily_durations[best_day]:.0f}min scheduled)'
                })
                
                # Add to simulation
                simulated_schedule.append({
                    'id': event['id'],
                    'title': event['title'],
                    'start': new_start.isoformat(),
                    'end': new_end.isoformat(),
                    'category': category,
                    'priority': event.get('priority'),
                    'type': event.get('type'),
                    'locked': False
                })
                
                if (idx + 1) <= 5 or (idx + 1) % 10 == 0:
                    durations_str = f"[{','.join(f'{daily_durations[d]:.0f}' for d in week_days)}]"
                    print(f"[{idx+1:2d}/{len(sorted_events)}] {event['title']:30s} → {best_day.strftime('%a'):3s} {new_start.strftime('%H:%M')} durations(min):{durations_str} chose:{daily_durations[best_day]:.0f}→{daily_durations[best_day]+(duration.total_seconds()/60):.0f}")
        
        # Show final distribution
        print(f"\n=== FINAL DISTRIBUTION ===")
        final_durations = defaultdict(int)  # Track total duration per day
        final_counts = defaultdict(int)     # Track event count per day
        for sim_event in simulated_schedule:
            day = self._parse_iso(sim_event['start']).date()
            if day in week_days:
                final_counts[day] += 1
                # Calculate duration
                start = self._parse_iso(sim_event['start'])
                end = self._parse_iso(sim_event['end'])
                duration_min = (end - start).total_seconds() / 60
                final_durations[day] += duration_min
        
        for day in week_days:
            count = final_counts[day]
            duration_hours = final_durations[day] / 60
            bar = "█" * int(duration_hours)  # Bar represents hours
            print(f"{day.strftime('%A'):10s} [{count:2d} events, {duration_hours:5.1f}h] {bar}")
        
        # NOTE: Breaks were completely removed as events. No break deletion needed.
        # The system no longer uses break events (neither physical nor virtual).
        
        return {
            'modifications': modifications,
            'recommendations': recommendations,
            'events_modified': len(modifications),
            'message': f'Distributed {len(moveable_events)} events evenly across {len(week_days)} days by workload duration'
        }
    
    def consolidate_schedule(self):
        """
        Reduce context switches by grouping similar tasks together WHILE distributing across week.
        
        Research: Context switches cost 15 min each (Mark et al., 2008)
        Target: Minimize category transitions, group same-category events, but spread across week
        
        Returns:
            dict with 'modifications', 'events_modified', 'improvement_estimate'
        """
        modifications = []
        
        # Get working hours from preferences
        work_start = datetime.strptime(self.preferences.get('work_start', '09:00'), '%H:%M').time()
        work_end = datetime.strptime(self.preferences.get('work_end', '18:00'), '%H:%M').time()
        
        # Group events by category
        events_by_category = defaultdict(list)
        for event in self.events:
            if event.get('locked') or event.get('title') == 'Break':
                continue  # Skip locked events and breaks
            if self._is_past_event(event):
                continue  # CRITICAL: Skip past events - cannot modify history
            category = event.get('category', 'Personal')
            events_by_category[category].append(event)
        
        # Get date range for the week
        all_dates = sorted(set(self._parse_iso(e['start']).date() for e in self.events))
        if not all_dates:
            return {'modifications': [], 'message': 'No events to optimize'}
        
        week_start = all_dates[0]
        week_days = [week_start + timedelta(days=i) for i in range(7)]
        
        # For each category, distribute events across the week intelligently
        for category, category_events in events_by_category.items():
            if len(category_events) <= 1:
                continue  # No consolidation needed
            
            # Calculate ideal time slots for this category across the week
            # Strategy: Group on same days, but don't cram all into one day
            events_per_day = max(1, len(category_events) // 5)  # Spread across workweek
            
            # Sort events by current time
            category_events.sort(key=lambda e: self._parse_iso(e['start']))
            
            # Try to schedule events in batches per day
            day_index = 0
            events_scheduled_today = 0
            current_time = datetime.combine(week_days[day_index], work_start)
            
            for event in category_events:
                start = self._parse_iso(event['start'])
                duration = self._parse_iso(event['end']) - start
                
                # Check if we should move to next day
                if events_scheduled_today >= events_per_day or current_time.time() > work_end:
                    day_index = (day_index + 1) % 7
                    if day_index >= len(week_days):
                        break  # Week is full
                    current_time = datetime.combine(week_days[day_index], work_start)
                    events_scheduled_today = 0
                
                # Extract preferred time window if event has one
                preferred_time_window = None
                preferred_time = event.get('preferred_time', {})
                if preferred_time and preferred_time.get('enabled') and preferred_time.get('start') and preferred_time.get('end'):
                    try:
                        pref_start_str = preferred_time['start']
                        pref_end_str = preferred_time['end']
                        pref_start_time = datetime.strptime(pref_start_str, '%H:%M').time()
                        pref_end_time = datetime.strptime(pref_end_str, '%H:%M').time()
                        preferred_time_window = (pref_start_time, pref_end_time)
                    except (ValueError, KeyError):
                        pass
                
                # Find next available slot on current day
                new_start = self._find_next_available_slot(
                    current_time, 
                    duration, 
                    week_days[day_index],
                    work_start,
                    work_end,
                    event['id'],
                    event_category=category,
                    event_priority=event.get('priority', 'medium'),
                    preferred_time_window=preferred_time_window
                )
                
                if new_start and new_start.date() == week_days[day_index]:
                    new_end = new_start + duration
                    
                    # Only modify if it's actually changing
                    if abs((new_start - start).total_seconds()) > 60:  # More than 1 min difference
                        modifications.append({
                            'id': event['id'],
                            'title': event['title'],
                            'old_start': event['start'],
                            'old_end': event['end'],
                            'new_start': new_start.isoformat(),
                            'new_end': new_end.isoformat(),
                            'reason': f'Grouping {category} events while distributing across week'
                        })
                    
                    current_time = new_end + timedelta(minutes=15)  # Add buffer
                    events_scheduled_today += 1
        
        return {
            'modifications': modifications,
            'events_modified': len(modifications),
            'improvement_estimate': self._estimate_fragmentation_improvement(len(modifications))
        }
    
    def group_deep_work(self):
        """
        Merge Work events into 90+ minute deep work blocks while respecting max 4h continuous work.
        
        Research: Deep work requires 90+ min uninterrupted (Newport, 2016)
        Max continuous work: 4 hours before break needed (cognitive fatigue research)
        Target: Create 2-3 deep work blocks per day, with breaks between
        
        Returns:
            dict with modifications and improvement estimate
        """
        modifications = []
        MAX_CONTINUOUS_WORK_MINUTES = 240  # 4 hours
        
        # Group work events by day
        work_by_day = defaultdict(list)
        for event in self.work_events:
            if event.get('locked') or event.get('title') == 'Break':
                continue
            if self._is_past_event(event):
                continue  # CRITICAL: Skip past events - cannot modify history
            start = self._parse_iso(event['start'])
            work_by_day[start.date()].append(event)
        
        # For each day, try to create deep work blocks
        for day, day_events in work_by_day.items():
            if len(day_events) < 2:
                continue
            
            # Sort by start time
            day_events.sort(key=lambda e: self._parse_iso(e['start']))
            
            # Build deep work blocks, respecting max continuous work time
            i = 0
            while i < len(day_events) - 1:
                current = day_events[i]
                next_event = day_events[i + 1]
                
                current_start = self._parse_iso(current['start'])
                current_end = self._parse_iso(current['end'])
                next_start = self._parse_iso(next_event['start'])
                next_end = self._parse_iso(next_event['end'])
                
                gap = (next_start - current_end).total_seconds() / 60
                current_duration = (current_end - current_start).total_seconds() / 60
                next_duration = (next_end - next_start).total_seconds() / 60
                
                # Check if merging would exceed max continuous work time
                combined_duration = current_duration + next_duration
                
                # If gap < 60 min and combined duration < 240 min, merge by moving next event closer
                if 0 < gap < 60 and combined_duration < MAX_CONTINUOUS_WORK_MINUTES:
                    # Move next event to start right after current (with small 5 min buffer)
                    new_start = current_end + timedelta(minutes=5)
                    duration = next_end - next_start
                    new_end = new_start + duration
                    
                    # Ensure no conflicts
                    if self._has_no_conflicts(new_start, new_end, next_event['id']):
                        modifications.append({
                            'id': next_event['id'],
                            'title': next_event['title'],
                            'old_start': next_event['start'],
                            'old_end': next_event['end'],
                            'new_start': new_start.isoformat(),
                            'new_end': new_end.isoformat(),
                            'reason': f'Creating deep work block (closing {int(gap)} min gap, total: {int(combined_duration)} min)'
                        })
                elif gap >= 60:
                    # Gap is already good - this is a natural break between work blocks
                    pass
                
                i += 1
        
        return {
            'modifications': modifications,
            'events_modified': len(modifications),
            'improvement_estimate': self._estimate_block_improvement(len(modifications))
        }
    
    def add_planning_buffer(self):
        """
        Add 10-minute buffer between back-to-back meetings.
        
        Research: <10min gaps cause stress (Microsoft, 2021)
        Target: At least 10 minutes between meetings
        
        Returns:
            dict with modifications to shift meetings apart
        """
        modifications = []
        
        # Sort meetings by start time
        meetings_sorted = sorted(self.meetings, key=lambda x: self._parse_iso(x['start']))
        
        if len(meetings_sorted) < 2:
            return {
                'modifications': [],
                'message': 'No back-to-back meetings to optimize'
            }
        
        # Find back-to-back meetings (gap < 10 minutes)
        for i in range(len(meetings_sorted) - 1):
            current = meetings_sorted[i]
            next_meeting = meetings_sorted[i + 1]
            
            if current.get('locked') or next_meeting.get('locked'):
                continue
            
            # CRITICAL: Skip past events - cannot modify history
            if self._is_past_event(current) or self._is_past_event(next_meeting):
                continue
            
            current_end = self._parse_iso(current['end'])
            next_start = self._parse_iso(next_meeting['start'])
            
            gap_minutes = (next_start - current_end).total_seconds() / 60
            
            # If gap is less than 10 minutes, push the next meeting later
            if 0 <= gap_minutes < 10:
                buffer_needed = 10 - gap_minutes
                new_start = next_start + timedelta(minutes=buffer_needed)
                duration = self._parse_iso(next_meeting['end']) - next_start
                new_end = new_start + duration
                
                # Check if new time slot is free - if not, try to find next available slot
                if self._has_no_conflicts(new_start, new_end, next_meeting['id']):
                    modifications.append({
                        'id': next_meeting['id'],
                        'title': next_meeting['title'],
                        'old_start': next_meeting['start'],
                        'old_end': next_meeting['end'],
                        'new_start': new_start.isoformat(),
                        'new_end': new_end.isoformat(),
                        'reason': f'Adding {int(buffer_needed)}-min buffer after {current["title"]}'
                    })
                else:
                    # Try to find next available slot after the desired buffer time
                    work_start = datetime.strptime(self.preferences.get('work_start', '09:00'), '%H:%M').time()
                    work_end = datetime.strptime(self.preferences.get('work_end', '18:00'), '%H:%M').time()
                    
                    # Extract preferred time window if event has one
                    preferred_time_window = None
                    preferred_time = next_meeting.get('preferred_time', {})
                    if preferred_time and preferred_time.get('enabled') and preferred_time.get('start') and preferred_time.get('end'):
                        try:
                            pref_start_str = preferred_time['start']
                            pref_end_str = preferred_time['end']
                            pref_start_time = datetime.strptime(pref_start_str, '%H:%M').time()
                            pref_end_time = datetime.strptime(pref_end_str, '%H:%M').time()
                            preferred_time_window = (pref_start_time, pref_end_time)
                        except (ValueError, KeyError):
                            pass
                    
                    available_slot = self._find_next_available_slot(
                        new_start,
                        duration,
                        new_start.date(),
                        work_start,
                        work_end,
                        next_meeting['id'],
                        event_category='Meeting',
                        event_priority=next_meeting.get('priority', 'medium'),
                        preferred_time_window=preferred_time_window
                    )
                    
                    if available_slot:
                        modifications.append({
                            'id': next_meeting['id'],
                            'title': next_meeting['title'],
                            'old_start': next_meeting['start'],
                            'old_end': next_meeting['end'],
                            'new_start': available_slot.isoformat(),
                            'new_end': (available_slot + duration).isoformat(),
                            'reason': f'Adding buffer after {current["title"]} (moved to next available slot)'
                        })
        
        return {
            'modifications': modifications,
            'events_modified': len(modifications),
            'improvement_estimate': {'meeting_efficiency': min(len(modifications) * 3, 15)}
        }
    
    def reduce_meeting_load(self):
        """
        Identify meetings that can be consolidated or moved.
        
        Research: >30% meeting time hurts productivity (Microsoft, 2021)
        Target: Keep meetings under 30% of work time
        
        Returns:
            dict with recommendations for meeting consolidation
        """
        recommendations = []
        
        # Group meetings by day
        meetings_by_day = defaultdict(list)
        for meeting in self.meetings:
            if meeting.get('locked'):
                continue
            if self._is_past_event(meeting):
                continue  # CRITICAL: Skip past events - cannot modify history
            start = self._parse_iso(meeting['start'])
            meetings_by_day[start.date()].append(meeting)
        
        # Find days with excessive meetings
        for day, day_meetings in meetings_by_day.items():
            if len(day_meetings) >= 3:
                # Suggest consolidating meetings on this day
                total_meeting_mins = sum(
                    (self._parse_iso(m['end']) - self._parse_iso(m['start'])).total_seconds() / 60
                    for m in day_meetings
                )
                
                # Find shortest meetings (candidates for combination)
                short_meetings = sorted(
                    day_meetings,
                    key=lambda m: (self._parse_iso(m['end']) - self._parse_iso(m['start'])).total_seconds() / 60
                )[:3]
                
                if len(short_meetings) >= 2:
                    recommendations.append({
                        'type': 'consolidate',
                        'meetings': [m['title'] for m in short_meetings],
                        'meeting_ids': [m['id'] for m in short_meetings],
                        'day': day.isoformat(),
                        'reason': f'{len(day_meetings)} meetings on {day.strftime("%A")} - consider combining related ones'
                    })
        
        return {
            'modifications': [],
            'recommendations': recommendations,
            'improvement_estimate': {'meeting_efficiency': 12} if recommendations else {}
        }
    
    def add_recovery_time(self):
        """
        Add recreational/personal time blocks by intelligently reducing work overload.
        
        Research: 7-14h/week recreational time optimal (Lancet, 2018)
        Target: At least 10h/week
        
        Returns:
            dict with modifications to create recovery time blocks
        """
        # Calculate current recreational time
        recreational_minutes = sum(
            (self._parse_iso(e['end']) - self._parse_iso(e['start'])).total_seconds() / 60
            for e in self.recreational + self.personal_events
        )
        
        target_minutes = 10 * 60  # 10 hours
        deficit_minutes = target_minutes - recreational_minutes
        
        if deficit_minutes <= 0:
            return {
                'modifications': [],
                'message': f'Recovery time is adequate ({int(recreational_minutes / 60)}h/week)'
            }
        
        # Strategy: Reduce work overload to create recovery time
        modifications = []
        recommendations = []
        
        # Find excessively long work events (> 3 hours)
        long_work_events = []
        for event in self.work_events + self.meetings:
            if event.get('locked'):
                continue
            if self._is_past_event(event):
                continue  # CRITICAL: Skip past events - cannot modify history
            start = self._parse_iso(event['start'])
            end = self._parse_iso(event['end'])
            duration_minutes = (end - start).total_seconds() / 60
            
            if duration_minutes >= 180:  # 3+ hours
                long_work_events.append((event, duration_minutes))
        
        # Sort by duration (longest first) to reduce the biggest blocks
        long_work_events.sort(key=lambda x: x[1], reverse=True)
        
        for event, duration_minutes in long_work_events:
            if deficit_minutes <= 0:
                break
            
            start = self._parse_iso(event['start'])
            end = self._parse_iso(event['end'])
            
            # Reduce by min(30 min, deficit_needed)
            reduction = min(30, deficit_minutes)
            new_end = end - timedelta(minutes=reduction)
            
            # Ensure we don't make it too short (keep at least 60 min)
            if (new_end - start).total_seconds() / 60 >= 60:
                # Check this wouldn't create conflicts
                if self._has_no_conflicts(start, new_end, event['id']):
                    modifications.append({
                        'id': event['id'],
                        'title': event['title'],
                        'old_start': event['start'],
                        'old_end': event['end'],
                        'new_start': start.isoformat(),
                        'new_end': new_end.isoformat(),
                        'reason': f'Reducing {int(duration_minutes)}-min work block by {int(reduction)} min to create recovery time'
                    })
                    deficit_minutes -= reduction
        
        # Always provide recommendation about current state
        if deficit_minutes > 0:
            recommendations.append({
                'action': 'add_free_time',
                'duration_hours': round(deficit_minutes / 60, 1),
                'reason': f'Current recreational time: {int(recreational_minutes / 60)}h, target: 10h+. Consider adding {round(deficit_minutes / 60, 1)}h of personal/recreational activities.'
            })
        else:
            recommendations.append({
                'action': 'schedule_achieved',
                'duration_hours': round(target_minutes / 60, 1),
                'reason': f'Optimizations will bring recovery time to target (10h+/week). Consider scheduling specific personal/recreational activities in the freed time.'
            })
        
        return {
            'modifications': modifications,
            'recommendations': recommendations,
            'improvement_estimate': {'recovery_support': min(len(modifications) * 5, 20)}
        }
    
    def fix_sleep_schedule(self):
        """
        Move events out of sleep hours to protect sleep quality.
        
        Research: Sleep protection critical for health (AASM)
        Target: Zero events during sleep hours
        
        Returns:
            dict with modifications to move conflicting events
        """
        modifications = []
        sleep_start_str = self.preferences.get('sleep_start', '23:00')
        sleep_end_str = self.preferences.get('sleep_end', '07:00')
        work_start_str = self.preferences.get('work_start', '09:00')
        work_end_str = self.preferences.get('work_end', '18:00')
        
        sleep_start = datetime.strptime(sleep_start_str, '%H:%M').time()
        sleep_end = datetime.strptime(sleep_end_str, '%H:%M').time()
        work_start = datetime.strptime(work_start_str, '%H:%M').time()
        work_end = datetime.strptime(work_end_str, '%H:%M').time()
        
        # Find events during sleep hours
        for event in self.events:
            if event.get('locked') or event.get('title') == 'Break':
                continue
            
            # CRITICAL: Skip past events - cannot modify history
            if self._is_past_event(event):
                continue
            
            start = self._parse_iso(event['start'])
            end = self._parse_iso(event['end'])
            duration = end - start
            
            if self._is_during_sleep(start, sleep_start, sleep_end):
                # Try to find next available slot after wake time
                # Start searching from work start time (more reasonable than wake time)
                search_start = start.replace(hour=work_start.hour, minute=work_start.minute)
                
                # Extract preferred time window if event has one
                preferred_time_window = None
                preferred_time = event.get('preferred_time', {})
                if preferred_time and preferred_time.get('enabled') and preferred_time.get('start') and preferred_time.get('end'):
                    try:
                        pref_start_str = preferred_time['start']
                        pref_end_str = preferred_time['end']
                        pref_start_time = datetime.strptime(pref_start_str, '%H:%M').time()
                        pref_end_time = datetime.strptime(pref_end_str, '%H:%M').time()
                        preferred_time_window = (pref_start_time, pref_end_time)
                    except (ValueError, KeyError):
                        pass
                
                available_slot = self._find_next_available_slot(
                    search_start,
                    duration,
                    start.date(),
                    work_start,
                    work_end,
                    event['id'],
                    event_category=event.get('category', 'Personal'),
                    event_priority=event.get('priority', 'medium'),
                    preferred_time_window=preferred_time_window
                )
                
                if available_slot:
                    modifications.append({
                        'id': event['id'],
                        'title': event['title'],
                        'old_start': event['start'],
                        'old_end': event['end'],
                        'new_start': available_slot.isoformat(),
                        'new_end': (available_slot + duration).isoformat(),
                        'reason': 'Moving out of sleep hours to protect sleep quality'
                    })
                else:
                    # Try next day if current day is full
                    next_day = start.date() + timedelta(days=1)
                    search_start_next = datetime.combine(next_day, work_start)
                    
                    # Extract preferred time window if event has one (reuse from above)
                    preferred_time_window = None
                    preferred_time = event.get('preferred_time', {})
                    if preferred_time and preferred_time.get('enabled') and preferred_time.get('start') and preferred_time.get('end'):
                        try:
                            pref_start_str = preferred_time['start']
                            pref_end_str = preferred_time['end']
                            pref_start_time = datetime.strptime(pref_start_str, '%H:%M').time()
                            pref_end_time = datetime.strptime(pref_end_str, '%H:%M').time()
                            preferred_time_window = (pref_start_time, pref_end_time)
                        except (ValueError, KeyError):
                            pass
                    
                    available_slot = self._find_next_available_slot(
                        search_start_next,
                        duration,
                        next_day,
                        work_start,
                        work_end,
                        event['id'],
                        event_category=event.get('category', 'Personal'),
                        event_priority=event.get('priority', 'medium'),
                        preferred_time_window=preferred_time_window
                    )
                    
                    if available_slot:
                        modifications.append({
                            'id': event['id'],
                            'title': event['title'],
                            'old_start': event['start'],
                            'old_end': event['end'],
                            'new_start': available_slot.isoformat(),
                            'new_end': (available_slot + duration).isoformat(),
                            'reason': 'Moving out of sleep hours to next available day'
                        })
        
        return {
            'modifications': modifications,
            'events_modified': len(modifications),
            'improvement_estimate': {'sleep_respect': 25} if modifications else {}
        }
    
    # Helper methods
    
    def _parse_iso(self, iso_string):
        """Parse ISO datetime string."""
        if isinstance(iso_string, datetime):
            return iso_string
        if 'T' in iso_string:
            return datetime.fromisoformat(iso_string.replace('Z', ''))
        return datetime.fromisoformat(iso_string)
    
    def _has_no_conflicts(self, start, end, exclude_id=None):
        """Check if time slot has no conflicts with existing events."""
        for event in self.events:
            if event['id'] == exclude_id:
                continue
            event_start = self._parse_iso(event['start'])
            event_end = self._parse_iso(event['end'])
            
            # Check overlap: two events overlap if one starts before the other ends
            # Events overlap if: start1 < end2 AND end1 > start2
            if start < event_end and end > event_start:
                return False
        return True
    
    def _find_all_available_slots(self, target_date, duration, work_start, work_end, exclude_id=None):
        """
        Find ALL available slots on a specific date.
        
        Args:
            target_date: Date to search on
            duration: Event duration as timedelta
            work_start: Start of work day (time object)
            work_end: End of work day (time object)
            exclude_id: Event ID to exclude from conflict checking
            
        Returns:
            List of (start, end) datetime tuples
        """
        slots = []
        search_start = datetime.combine(target_date, work_start)
        work_end_dt = datetime.combine(target_date, work_end)
        
        current = search_start
        while current + duration <= work_end_dt:
            slot_end = current + duration
            if self._has_no_conflicts(current, slot_end, exclude_id):
                slots.append((current, slot_end))
            current += timedelta(minutes=15)
        
        return slots
    
    def _score_slot(self, slot_start, slot_end, event_category, event_priority, exclude_id=None):
        """
        Score a time slot based on optimality criteria.
        
        Higher score = better slot
        
        Scoring factors:
        - Time of day fit for category (Work→morning, Personal→evening, etc.)
        - Centrality within work hours
        - Spacing from other events
        """
        score = 0
        slot_hour = slot_start.hour
        slot_date = slot_start.date()
        
        # 1. TIME OF DAY FIT (0-50 points)
        if event_category in ['Work', 'Meeting']:
            # Work/meetings prefer morning-midday (9-14)
            if 9 <= slot_hour <= 14:
                score += 50
            elif 14 < slot_hour <= 17:
                score += 30  # Afternoon is OK
            else:
                score += 10  # Early morning or late
        elif event_category in ['Personal', 'Recreational']:
            # Personal prefers afternoon-evening (14-20)
            if 14 <= slot_hour <= 20:
                score += 50
            elif 12 <= slot_hour < 14 or 20 < slot_hour <= 22:
                score += 30  # Close to ideal
            else:
                score += 10
        elif event_category == 'Meal':
            # Meals prefer standard meal times
            if slot_hour in [7, 8, 12, 13, 18, 19]:  # Breakfast, lunch, dinner times
                score += 50
            elif slot_hour in [6, 9, 11, 14, 17, 20]:  # Close to meal times
                score += 30
            else:
                score += 10
        else:
            # Default: prefer work hours
            if 9 <= slot_hour <= 17:
                score += 30
            else:
                score += 10
        
        # 2. WORK HOUR CENTRALITY (0-30 points)
        # Prefer slots in middle of workday to avoid edge effects
        work_start_dt = datetime.combine(slot_date, datetime.strptime(
            self.preferences.get('work_start', '09:00'), '%H:%M').time())
        work_end_dt = datetime.combine(slot_date, datetime.strptime(
            self.preferences.get('work_end', '18:00'), '%H:%M').time())
        
        if slot_start >= work_start_dt and slot_end <= work_end_dt:
            work_center = work_start_dt + (work_end_dt - work_start_dt) / 2
            slot_center = slot_start + (slot_end - slot_start) / 2
            distance_hours = abs((slot_center - work_center).total_seconds()) / 3600
            centrality_score = max(0, 30 - (distance_hours * 5))
            score += centrality_score
        
        # 3. SPACING FROM OTHER EVENTS (0-20 points)
        # Count events within 2 hours before/after
        nearby_events = 0
        for event in self.events:
            if event.get('id') == exclude_id:
                continue
            event_start = self._parse_iso(event['start'])
            event_end = self._parse_iso(event['end'])
            
            # Check if event is within 2 hours of this slot
            time_diff = min(
                abs((event_start - slot_end).total_seconds()),
                abs((event_end - slot_start).total_seconds())
            ) / 3600
            
            if time_diff < 2:
                nearby_events += 1
        
        # Prefer slots with fewer nearby events (less cramming)
        spacing_score = max(0, 20 - (nearby_events * 5))
        score += spacing_score
        
        return score
    
    def _find_next_available_slot(self, preferred_start, duration, target_date, work_start, work_end, exclude_id=None, event_category=None, event_priority=None, preferred_time_window=None):
        """
        Find BEST-FIT time slot on target_date using multi-criteria scoring with progressive fallback.
        
        STRATEGY (matches recurring/floating event logic):
        1. Collect ALL candidate slots across 4 fallback levels:
           - Level 1: Exact preferred time window (if specified)
           - Level 2: Expanded preferred time (±1 hour)
           - Level 3: Work hours (full work day)
           - Level 4: Any waking hours (last resort)
        2. Score ALL candidates using _score_slot() (work hours, spacing, centrality)
        3. Add preferred time bonus (50 points) for slots in exact/expanded window
        4. Return HIGHEST-SCORING slot (not first-fit)
        
        This ensures preferred time is ABSOLUTE PRIORITY while using best-fit scoring.
        
        Args:
            preferred_start: Preferred start datetime (used as fallback)
            duration: Event duration as timedelta
            target_date: Target date to schedule on
            work_start: Start of work day (time object)
            work_end: End of work day (time object)
            exclude_id: Event ID to exclude from conflict checking
            event_category: Event category for optimal time selection
            event_priority: Event priority for scheduling preference
            preferred_time_window: Tuple of (start_time, end_time) as time objects for preferred window
            
        Returns:
            datetime of optimal slot or None if no slot found
        """
        candidate_slots = []
        
        # LEVEL 1: Try exact preferred time window (HIGHEST PRIORITY)
        if preferred_time_window:
            pref_start_time, pref_end_time = preferred_time_window
            
            pref_slots = self._find_all_available_slots(
                target_date, duration, pref_start_time, pref_end_time, exclude_id
            )
            
            # Score preferred time slots with 50-point bonus
            for slot_start, slot_end in pref_slots:
                base_score = self._score_slot(slot_start, slot_end, event_category, event_priority, exclude_id)
                candidate_slots.append({
                    'start': slot_start,
                    'end': slot_end,
                    'score': base_score + 50,  # Preferred time bonus (dominant factor)
                    'level': 'exact_preferred'
                })
            
            # LEVEL 2: Try expanded window (±1 hour) if preferred time specified
            if pref_start_time.hour > 0:  # Can expand backward
                expanded_start = (datetime.combine(target_date, pref_start_time) - timedelta(hours=1)).time()
            else:
                expanded_start = pref_start_time
            
            if pref_end_time.hour < 23:  # Can expand forward
                expanded_end = (datetime.combine(target_date, pref_end_time) + timedelta(hours=1)).time()
            else:
                expanded_end = pref_end_time
            
            # Only search expanded area (exclude slots already found in exact window)
            if expanded_start != pref_start_time or expanded_end != pref_end_time:
                expanded_slots = self._find_all_available_slots(
                    target_date, duration, expanded_start, expanded_end, exclude_id
                )
                
                for slot_start, slot_end in expanded_slots:
                    slot_time = slot_start.time()
                    # Skip if already in exact preferred window
                    is_overnight = pref_end_time <= pref_start_time
                    if is_overnight:
                        in_exact = slot_time >= pref_start_time or slot_time < pref_end_time
                    else:
                        in_exact = pref_start_time <= slot_time < pref_end_time
                    
                    if not in_exact:
                        base_score = self._score_slot(slot_start, slot_end, event_category, event_priority, exclude_id)
                        candidate_slots.append({
                            'start': slot_start,
                            'end': slot_end,
                            'score': base_score + 35,  # Expanded window bonus (still high priority)
                            'level': 'expanded_preferred'
                        })
        
        # LEVEL 3: Work hours (standard work day)
        work_slots = self._find_all_available_slots(
            target_date, duration, work_start, work_end, exclude_id
        )
        
        for slot_start, slot_end in work_slots:
            # Skip if already scored in preferred/expanded window
            slot_time = slot_start.time()
            already_scored = False
            
            if preferred_time_window:
                pref_start_time, pref_end_time = preferred_time_window
                is_overnight = pref_end_time <= pref_start_time
                
                # Check exact preferred
                if is_overnight:
                    in_exact = slot_time >= pref_start_time or slot_time < pref_end_time
                else:
                    in_exact = pref_start_time <= slot_time < pref_end_time
                
                # Check expanded window
                expanded_start = max((datetime.combine(target_date, pref_start_time) - timedelta(hours=1)).time(), datetime.min.time())
                expanded_end = min((datetime.combine(target_date, pref_end_time) + timedelta(hours=1)).time(), datetime.max.time())
                
                if is_overnight:
                    in_expanded = slot_time >= expanded_start or slot_time < expanded_end
                else:
                    in_expanded = expanded_start <= slot_time < expanded_end
                
                already_scored = in_exact or in_expanded
            
            if not already_scored:
                base_score = self._score_slot(slot_start, slot_end, event_category, event_priority, exclude_id)
                candidate_slots.append({
                    'start': slot_start,
                    'end': slot_end,
                    'score': base_score + 10,  # Work hours bonus (moderate priority)
                    'level': 'work_hours'
                })
        
        # LEVEL 4: Full day (any waking hours - last resort)
        # Use midnight to midnight, excluding sleep hours
        full_day_slots = self._find_all_available_slots(
            target_date, duration, datetime.min.time(), datetime.max.time(), exclude_id
        )
        
        for slot_start, slot_end in full_day_slots:
            # Skip if already scored in any previous level
            slot_time = slot_start.time()
            already_scored = False
            
            # Check work hours
            if work_start <= slot_time < work_end:
                already_scored = True
            
            # Check preferred windows
            if preferred_time_window and not already_scored:
                pref_start_time, pref_end_time = preferred_time_window
                is_overnight = pref_end_time <= pref_start_time
                
                expanded_start = max((datetime.combine(target_date, pref_start_time) - timedelta(hours=1)).time(), datetime.min.time())
                expanded_end = min((datetime.combine(target_date, pref_end_time) + timedelta(hours=1)).time(), datetime.max.time())
                
                if is_overnight:
                    already_scored = slot_time >= expanded_start or slot_time < expanded_end
                else:
                    already_scored = expanded_start <= slot_time < expanded_end
            
            if not already_scored:
                base_score = self._score_slot(slot_start, slot_end, event_category, event_priority, exclude_id)
                candidate_slots.append({
                    'start': slot_start,
                    'end': slot_end,
                    'score': base_score,  # No bonus (fallback only)
                    'level': 'full_day'
                })
        
        # Return best-scoring slot across all levels
        if not candidate_slots:
            return None
        
        best_slot = max(candidate_slots, key=lambda s: s['score'])
        return best_slot['start']
    
    def _is_during_sleep(self, dt, sleep_start, sleep_end):
        """Check if datetime is during sleep hours."""
        dt_time = dt.time()
        if sleep_start > sleep_end:  # Overnight sleep
            return dt_time >= sleep_start or dt_time < sleep_end
        return sleep_start <= dt_time < sleep_end
    
    def _find_original_time(self, event_id, field):
        """Find original start/end time for an event from self.events."""
        for event in self.events:
            if event['id'] == event_id:
                return event.get(field if field != 'start' else 'start', event.get('start_time', ''))
        return None
    
    def _calculate_sleep_hours(self):
        """Calculate total sleep hours per week."""
        sleep_start_str = self.preferences.get('sleep_start', '23:00')
        sleep_end_str = self.preferences.get('sleep_end', '07:00')
        
        sleep_start = datetime.strptime(sleep_start_str, '%H:%M')
        sleep_end = datetime.strptime(sleep_end_str, '%H:%M')
        
        if sleep_end < sleep_start:
            sleep_end += timedelta(days=1)
        
        hours_per_night = (sleep_end - sleep_start).total_seconds() / 3600
        return hours_per_night * 7
    
    def _estimate_fragmentation_improvement(self, moves):
        """Estimate fragmentation score improvement."""
        # Each consolidation move reduces ~2 context switches
        # Each switch = 15 min cost
        # Score improvement roughly: moves * 2 points
        return {'fragmentation': min(moves * 2, 20)}
    
    def _estimate_block_improvement(self, merges):
        """Estimate block structure score improvement."""
        # Each merge creates a longer block
        # Score improvement: merges * 3 points
        return {'block_structure': min(merges * 3, 25)}
