"""
Event Validator
Provides real-time validation for event creation and editing.
Detects conflicts, violations, and provides helpful warnings.
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional


class EventValidator:
    """Validates events against schedule constraints and best practices."""
    
    # Validation severity levels
    ERROR = 'error'      # Blocking issue - event should not be saved
    WARNING = 'warning'  # Best practice violation - can be saved but not recommended
    INFO = 'info'        # Helpful suggestion - no issue
    
    def __init__(self, existing_events: List[Dict], preferences: Dict):
        """
        Initialize validator with current schedule context.
        
        Args:
            existing_events: List of all events in the schedule
            preferences: User preferences (sleep hours, work hours, etc.)
        """
        self.existing_events = existing_events
        self.preferences = preferences
        
        # Extract preference values with defaults
        self.sleep_start = self._parse_time(preferences.get('sleep_start', '23:00'))
        self.sleep_end = self._parse_time(preferences.get('sleep_end', '07:00'))
        self.work_start = self._parse_time(preferences.get('work_start', '09:00'))
        self.work_end = self._parse_time(preferences.get('work_end', '18:00'))
        self.max_work_hours = preferences.get('max_work_hours_per_day', 10)
        self.min_break_interval = preferences.get('min_break_interval_minutes', 120)
    
    def validate_event(self, event: Dict, event_id: Optional[int] = None) -> Dict:
        """
        Validate an event and return validation results.
        
        Args:
            event: Event data to validate (must have start, end, title, category)
            event_id: ID of event being edited (None for new events)
        
        Returns:
            {
                'valid': bool,
                'errors': [{'type': str, 'message': str, 'severity': 'error'}, ...],
                'warnings': [{'type': str, 'message': str, 'severity': 'warning'}, ...],
                'suggestions': [{'type': str, 'message': str, 'severity': 'info'}, ...]
            }
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Parse event times
        try:
            start = self._parse_iso(event['start'])
            end = self._parse_iso(event['end'])
        except (ValueError, KeyError) as e:
            return {
                'valid': False,
                'errors': [{'type': 'invalid_time', 'message': f'Invalid time format: {str(e)}', 'severity': self.ERROR}],
                'warnings': [],
                'suggestions': []
            }
        
        # Basic validation
        if end <= start:
            errors.append({
                'type': 'invalid_duration',
                'message': 'Event end time must be after start time',
                'severity': self.ERROR
            })
        
        duration_minutes = (end - start).total_seconds() / 60
        
        # Check for extremely short events
        if duration_minutes < 5:
            warnings.append({
                'type': 'too_short',
                'message': f'Event is very short ({int(duration_minutes)} min). Consider extending it.',
                'severity': self.WARNING
            })
        
        # Check for extremely long events
        if duration_minutes > 480:  # 8 hours
            warnings.append({
                'type': 'too_long',
                'message': f'Event is very long ({duration_minutes / 60:.1f} hours). Consider breaking it into smaller blocks.',
                'severity': self.WARNING
            })
        
        # Check for overlapping events
        overlaps = self._check_overlaps(start, end, event_id)
        if overlaps:
            for overlap in overlaps:
                errors.append({
                    'type': 'overlap',
                    'message': f'Overlaps with "{overlap["title"]}" ({overlap["start"]} - {overlap["end"]})',
                    'severity': self.ERROR,
                    'conflicting_event': overlap
                })
        
        # Check sleep hour conflicts
        sleep_conflict = self._check_sleep_conflict(start, end)
        if sleep_conflict:
            warnings.append({
                'type': 'sleep_conflict',
                'message': f'Event occurs during sleep hours ({self.sleep_start.strftime("%H:%M")} - {self.sleep_end.strftime("%H:%M")}). This may impact your health score.',
                'severity': self.WARNING
            })
        
        # Category-specific validations
        category = event.get('category', 'Personal')
        
        if category in ['Work', 'Meeting']:
            # Check if work event is outside work hours
            if not self._is_during_work_hours(start, end):
                suggestions.append({
                    'type': 'outside_work_hours',
                    'message': f'Work event scheduled outside typical work hours ({self.work_start.strftime("%H:%M")} - {self.work_end.strftime("%H:%M")})',
                    'severity': self.INFO
                })
            
            # Check total work time for the day
            day_work_minutes = self._calculate_day_work_time(start.date(), event_id)
            total_work_minutes = day_work_minutes + duration_minutes
            
            if total_work_minutes > self.max_work_hours * 60:
                warnings.append({
                    'type': 'excessive_work',
                    'message': f'Total work time for {start.strftime("%A")} would be {total_work_minutes / 60:.1f} hours (limit: {self.max_work_hours}h). Consider rescheduling.',
                    'severity': self.WARNING
                })
            
            # Check for breaks if long work session
            if duration_minutes >= self.min_break_interval:
                suggestions.append({
                    'type': 'break_needed',
                    'message': f'Work session is {duration_minutes / 60:.1f} hours long. Consider adding breaks every {self.min_break_interval} minutes.',
                    'severity': self.INFO
                })
        
        # Check if event crosses midnight
        if start.date() != end.date():
            warnings.append({
                'type': 'crosses_midnight',
                'message': 'Event crosses midnight. Consider splitting into separate events for each day.',
                'severity': self.WARNING
            })
        
        # Additional proactive checks from Feature 2
        if category == 'Meeting':
            meeting_load_warnings = self._check_meeting_load(start, end, duration_minutes, event_id)
            warnings.extend(meeting_load_warnings)
        
        context_switch_suggestions = self._check_context_switches(start, end, category, event_id)
        suggestions.extend(context_switch_suggestions)
        
        fragmentation_suggestions = self._check_fragmentation(start, end, event_id)
        suggestions.extend(fragmentation_suggestions)
        
        buffer_warnings = self._check_planning_buffer(start, end, duration_minutes, event_id)
        warnings.extend(buffer_warnings)
        
        deep_work_warnings = self._check_deep_work_disruption(start, end, event_id)
        warnings.extend(deep_work_warnings)
        
        # Determine overall validity
        valid = len(errors) == 0
        
        return {
            'valid': valid,
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }
    
    def _check_meeting_load(self, start: datetime, end: datetime, duration_minutes: float, exclude_id: Optional[int] = None) -> List[Dict]:
        """Check if adding this meeting creates excessive meeting load (>30% of work time)."""
        warnings = []
        event_day = start.date()
        
        # Count meetings on the same day
        same_day_meetings = []
        for event in self.existing_events:
            if exclude_id and event.get('id') == exclude_id:
                continue
            if event.get('category') == 'Meeting':
                event_start = self._parse_iso(event['start'])
                if event_start.date() == event_day:
                    same_day_meetings.append(event)
        
        # Calculate total meeting time
        total_meeting_mins = sum(
            (self._parse_iso(e['end']) - self._parse_iso(e['start'])).total_seconds() / 60
            for e in same_day_meetings
        )
        total_meeting_mins += duration_minutes
        
        # Calculate work hours for the day
        work_hours = (datetime.combine(event_day, self.work_end) - 
                     datetime.combine(event_day, self.work_start)).total_seconds() / 3600
        
        meeting_percentage = (total_meeting_mins / 60) / work_hours * 100
        
        if meeting_percentage > 30:
            warnings.append({
                'type': 'meeting_load',
                'message': f'Meeting #{len(same_day_meetings) + 1} today ({int(meeting_percentage)}% of work time). Optimal: <30%',
                'severity': self.WARNING
            })
        
        return warnings
    
    def _check_context_switches(self, start: datetime, end: datetime, category: str, exclude_id: Optional[int] = None) -> List[Dict]:
        """Check if event creates context switches between different categories."""
        suggestions = []
        
        # Find adjacent events
        adjacent_before = None
        adjacent_after = None
        
        for event in self.existing_events:
            if exclude_id and event.get('id') == exclude_id:
                continue
            
            event_start = self._parse_iso(event['start'])
            event_end = self._parse_iso(event['end'])
            
            # Event right before (within 30 min)
            if event_end <= start and (start - event_end).total_seconds() / 60 <= 30:
                if not adjacent_before or event_end > self._parse_iso(adjacent_before['end']):
                    adjacent_before = event
            
            # Event right after (within 30 min)
            if event_start >= end and (event_start - end).total_seconds() / 60 <= 30:
                if not adjacent_after or event_start < self._parse_iso(adjacent_after['start']):
                    adjacent_after = event
        
        # Check for context switches
        if adjacent_before and adjacent_before.get('category') != category:
            suggestions.append({
                'type': 'context_switch',
                'message': f'Context switch from {adjacent_before.get("category")} to {category}',
                'severity': self.INFO
            })
        
        if adjacent_after and adjacent_after.get('category') != category:
            suggestions.append({
                'type': 'context_switch',
                'message': f'Context switch from {category} to {adjacent_after.get("category")}',
                'severity': self.INFO
            })
        
        return suggestions
    
    def _check_fragmentation(self, start: datetime, end: datetime, exclude_id: Optional[int] = None) -> List[Dict]:
        """Check if event creates small gaps (<15 min) that waste time."""
        suggestions = []
        
        for event in self.existing_events:
            if exclude_id and event.get('id') == exclude_id:
                continue
            
            event_start = self._parse_iso(event['start'])
            event_end = self._parse_iso(event['end'])
            
            # Check gap before new event
            if event_end < start:
                gap_minutes = (start - event_end).total_seconds() / 60
                if 0 < gap_minutes < 15:
                    suggestions.append({
                        'type': 'fragmentation',
                        'message': f'{int(gap_minutes)} min gap after "{event.get("title")}". Consider starting at {event_end.strftime("%H:%M")}',
                        'severity': self.INFO
                    })
            
            # Check gap after new event
            if event_start > end:
                gap_minutes = (event_start - end).total_seconds() / 60
                if 0 < gap_minutes < 15:
                    suggestions.append({
                        'type': 'fragmentation',
                        'message': f'{int(gap_minutes)} min gap before "{event.get("title")}". Consider ending at {event_start.strftime("%H:%M")}',
                        'severity': self.INFO
                    })
        
        return suggestions
    
    def _check_planning_buffer(self, start: datetime, end: datetime, duration_minutes: float, exclude_id: Optional[int] = None) -> List[Dict]:
        """Check if adding event reduces planning buffer below healthy level (<5%)."""
        warnings = []
        
        # Get week boundaries
        week_start = start - timedelta(days=start.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        # Calculate total scheduled time
        total_minutes = 0
        for event in self.existing_events:
            if exclude_id and event.get('id') == exclude_id:
                continue
            
            event_start = self._parse_iso(event['start'])
            if week_start <= event_start < week_end:
                event_end = self._parse_iso(event['end'])
                total_minutes += (event_end - event_start).total_seconds() / 60
        
        total_minutes += duration_minutes
        
        # Calculate available time
        daily_work_hours = (datetime.combine(start.date(), self.work_end) -
                          datetime.combine(start.date(), self.work_start)).total_seconds() / 3600
        available_minutes = 7 * daily_work_hours * 60
        
        slack_percent = ((available_minutes - total_minutes) / available_minutes) * 100
        
        if slack_percent < 5:
            warnings.append({
                'type': 'planning_buffer',
                'message': f'Low planning buffer ({slack_percent:.1f}% slack). Optimal: 8-10%',
                'severity': self.WARNING
            })
        
        return warnings
    
    def _check_deep_work_disruption(self, start: datetime, end: datetime, exclude_id: Optional[int] = None) -> List[Dict]:
        """Check if event disrupts existing deep work blocks (90+ min)."""
        warnings = []
        
        # Find work blocks of 90+ minutes
        for event in self.existing_events:
            if exclude_id and event.get('id') == exclude_id:
                continue
            
            if event.get('category') != 'Work':
                continue
            
            event_start = self._parse_iso(event['start'])
            event_end = self._parse_iso(event['end'])
            duration = (event_end - event_start).total_seconds() / 60
            
            if duration < 90:
                continue
            
            # Check if new event is too close (within 15 min)
            if end <= event_start and (event_start - end).total_seconds() / 60 < 15:
                warnings.append({
                    'type': 'deep_work_disruption',
                    'message': f'Too close to deep work block "{event.get("title")}". Leave 15+ min buffer',
                    'severity': self.WARNING
                })
            
            if start >= event_end and (start - event_end).total_seconds() / 60 < 15:
                warnings.append({
                    'type': 'deep_work_disruption',
                    'message': f'Too close after deep work block "{event.get("title")}". Leave buffer time',
                    'severity': self.WARNING
                })
        
        return warnings
    
    def _check_overlaps(self, start: datetime, end: datetime, exclude_id: Optional[int] = None) -> List[Dict]:
        """Find events that overlap with the given time range."""
        overlaps = []
        
        for event in self.existing_events:
            # Skip the event being edited
            if exclude_id and event.get('id') == exclude_id:
                continue
            
            event_start = self._parse_iso(event['start'])
            event_end = self._parse_iso(event['end'])
            
            # Check for overlap
            if start < event_end and end > event_start:
                overlaps.append({
                    'id': event.get('id'),
                    'title': event.get('title'),
                    'start': event_start.strftime('%Y-%m-%d %H:%M'),
                    'end': event_end.strftime('%Y-%m-%d %H:%M'),
                    'category': event.get('category')
                })
        
        return overlaps
    
    def _check_sleep_conflict(self, start: datetime, end: datetime) -> bool:
        """Check if event occurs during sleep hours."""
        # Handle sleep period that crosses midnight
        if self.sleep_start > self.sleep_end:
            # Sleep period crosses midnight (e.g., 23:00 - 07:00)
            return (start.time() >= self.sleep_start or start.time() < self.sleep_end or
                    end.time() >= self.sleep_start or end.time() < self.sleep_end)
        else:
            # Sleep period within same day
            return (self.sleep_start <= start.time() < self.sleep_end or
                    self.sleep_start < end.time() <= self.sleep_end)
    
    def _is_during_work_hours(self, start: datetime, end: datetime) -> bool:
        """Check if event is during typical work hours."""
        # Event is during work hours if it starts and ends within work hours
        return (self.work_start <= start.time() < self.work_end and
                self.work_start < end.time() <= self.work_end)
    
    def _calculate_day_work_time(self, date, exclude_id: Optional[int] = None) -> float:
        """Calculate total work time (in minutes) for a specific day."""
        total_minutes = 0
        
        for event in self.existing_events:
            if exclude_id and event.get('id') == exclude_id:
                continue
            
            if event.get('category') not in ['Work', 'Meeting']:
                continue
            
            event_start = self._parse_iso(event['start'])
            if event_start.date() == date:
                event_end = self._parse_iso(event['end'])
                duration = (event_end - event_start).total_seconds() / 60
                total_minutes += duration
        
        return total_minutes
    
    @staticmethod
    def _parse_iso(iso_string: str) -> datetime:
        """Parse ISO format datetime string."""
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    
    @staticmethod
    def _parse_time(time_string: str) -> time:
        """Parse time string in HH:MM format."""
        return datetime.strptime(time_string, '%H:%M').time()
