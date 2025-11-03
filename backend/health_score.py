"""
TEMPORA Health Score Calculator
Calculates scheduling health metrics based on peer-reviewed research.
5 core metrics: Work/Life Balance, Sleep Respect, Focus Blocks, Meeting Load, Recovery Time

Note: "Breaks" are just gaps in the schedule - not events. We analyze gap presence
but give much higher weight to active recovery (Recreational/Meal events).
"""

from datetime import datetime, timedelta, time
from collections import defaultdict


class HealthScoreCalculator:
    """Calculate scheduling health score from calendar events."""
    
    # Metric weights (must sum to 1.0)
    WEIGHTS = {
        'work_life': 0.25,            # Work-life balance (work hours vs personal time)
        'sleep': 0.20,                # Sleep schedule respect (reduced - base requirement)
        'focus': 0.20,                # Deep focus blocks (uninterrupted work time)
        'meetings': 0.15,             # Meeting load and back-to-back meetings
        'recovery': 0.20              # Active recovery time (Recreational/Meal events) - increased for burnout prevention
    }
    
    def __init__(self, events, preferences):
        """
        Initialize calculator with events and user preferences.
        
        Args:
            events: List of event dictionaries with keys: id, title, category, start_time, end_time, notes
            preferences: User preferences dictionary with keys: work_start, work_end, sleep_start, sleep_end
        """
        self.events = events
        self.preferences = preferences
        self.work_events = []
        self.meetings = []
        self.recreational_events = []
        self.meal_events = []
        
        # Categorize events
        for event in events:
            category = event.get('category', 'Personal')
            if category == 'Work':
                self.work_events.append(event)
            elif category == 'Meeting':
                self.meetings.append(event)
            elif category == 'Recreational':
                self.recreational_events.append(event)
            elif category == 'Meal':
                self.meal_events.append(event)
    
    def calculate_score(self):
        """
        Calculate comprehensive health score.
        
        Returns:
            Dictionary with score, breakdown, issues, suggestions, and stats
        """
        # CRITICAL FIX: Check for empty schedule first
        total_events = len(self.work_events + self.meetings + self.recreational_events + self.meal_events)
        if total_events == 0:
            return {
                'score': 0,
                'breakdown': {
                    'work_life': 0,
                    'sleep_respect': 0,
                    'focus_blocks': 0,
                    'meetings': 0,
                    'recovery': 0
                },
                'details': {
                    'work_life': {'score': 0, 'hours': 0, 'long_days': 0, 'weekend_night_hours': 0},
                    'sleep_respect': {'score': 0, 'intrusion_hours': 0, 'intrusion_count': 0},
                    'focus_blocks': {'score': 0, 'focus_hours': 0, 'focus_blocks': 0, 'interrupted_blocks': 0},
                    'meetings': {'score': 0, 'total_hours': 0, 'back_to_back': 0, 'meeting_days': 0},
                    'recovery': {'score': 0, 'active_recovery_hours': 0, 'recreational_hours': 0, 'meal_hours': 0}
                },
                'issues': ['⚠️ No events scheduled - cannot assess health metrics'],
                'suggestions': [
                    '💡 Start by scheduling work hours within your preferred work window',
                    '💡 Add recreational activities for active recovery',
                    '💡 Schedule meal times to establish routine',
                    '💡 Ensure events respect your sleep schedule'
                ],
                'weekly_stats': {
                    'work_hours': 0,
                    'meeting_hours': 0,
                    'recovery_hours': 0,
                    'sleep_intrusions': 0,
                    'focus_time': 0
                }
            }
        
        # Calculate individual metrics
        work_life_data = self._calculate_work_life_balance()
        sleep_data = self._calculate_sleep_respect()
        focus_data = self._calculate_focus_blocks()
        meeting_data = self._calculate_meeting_load()
        recovery_data = self._calculate_recovery_time()
        
        # Composite score
        composite = (
            self.WEIGHTS['work_life'] * work_life_data['score'] +
            self.WEIGHTS['sleep'] * sleep_data['score'] +
            self.WEIGHTS['focus'] * focus_data['score'] +
            self.WEIGHTS['meetings'] * meeting_data['score'] +
            self.WEIGHTS['recovery'] * recovery_data['score']
        )
        
        # Generate insights
        breakdown = {
            'work_life': work_life_data,
            'sleep_respect': sleep_data,
            'focus_blocks': focus_data,
            'meetings': meeting_data,
            'recovery': recovery_data
        }
        
        issues = self._generate_issues(breakdown)
        suggestions = self._generate_suggestions(breakdown)
        
        return {
            'score': int(round(composite)),
            'breakdown': {
                'work_life': work_life_data['score'],
                'sleep_respect': sleep_data['score'],
                'focus_blocks': focus_data['score'],
                'meetings': meeting_data['score'],
                'recovery': recovery_data['score']
            },
            'details': breakdown,
            'issues': issues,
            'suggestions': suggestions,
            'weekly_stats': self._calculate_weekly_stats(breakdown)
        }
    
    def _calculate_work_life_balance(self):
        """Calculate work/life balance score (25% weight)."""
        # Combine work events and meetings
        work_events = self.work_events + self.meetings
        
        if not work_events:
            # CRITICAL FIX: No work scheduled
            # Check if there are personal/recreational events (retired/vacation) or truly empty
            has_personal = len(self.recreational_events) > 0 or len(self.meal_events) > 0
            
            if has_personal:
                # Has personal life but no work = good balance (vacation/sabbatical)
                return {
                    'score': 85,
                    'hours': 0,
                    'long_days': 0,
                    'weekend_night_hours': 0,
                    'message': 'No work scheduled - vacation/personal time'
                }
            else:
                # Completely empty schedule
                return {
                    'score': 0,
                    'hours': 0,
                    'long_days': 0,
                    'weekend_night_hours': 0,
                    'message': 'No events scheduled'
                }
        
        # Total work hours
        total_minutes = sum(self._calculate_duration(e) for e in work_events)
        work_hours = total_minutes / 60
        
        # Base score from weekly hours (WHO research)
        if 35 <= work_hours <= 45:
            base_score = 100
        elif 45 < work_hours <= 55:
            base_score = 100 - ((work_hours - 45) / 10) * 30  # Linear 100→70
        elif work_hours < 35:
            base_score = 100 - ((35 - work_hours) / 5) * 5  # Small penalty for under-work
        elif 55 < work_hours <= 65:
            # Balanced: Moderate penalty for overwork (55-65h range)
            base_score = 40 - ((work_hours - 55) / 10) * 10  # 40→30 (clean 1 point per hour)
        else:  # >65h - BURNOUT TERRITORY
            # Balanced: Gradual decline for extreme overwork
            base_score = max(0, 30 - ((work_hours - 65) / 5) * 5)  # 30→25→20... (1 point per hour)
        
        # Count long days (>10h work/meetings per day)
        daily_hours = self._group_by_day(work_events)
        long_days = sum(1 for hours in daily_hours.values() if hours > 10)
        long_day_penalty = max(0, (long_days - 1) * 3)
        
        # Weekend/night work penalty
        work_start = self._parse_time_string(self.preferences.get('work_start', '09:00'))
        work_end = self._parse_time_string(self.preferences.get('work_end', '18:00'))
        
        weekend_night_minutes = 0
        for event in work_events:
            dt = self._parse_iso(event['start'])
            if dt.weekday() >= 5 or not (work_start <= dt.time() < work_end):
                weekend_night_minutes += self._calculate_duration(event)
        
        weekend_penalty = weekend_night_minutes / 60
        
        final_score = max(0, base_score - long_day_penalty - weekend_penalty)
        
        return {
            'score': int(final_score),
            'hours': round(work_hours, 1),
            'long_days': long_days,
            'weekend_night_hours': round(weekend_night_minutes / 60, 1)
        }
    
    def _calculate_sleep_respect(self):
        """Calculate sleep respect score (25% weight)."""
        sleep_start = self._parse_time_string(self.preferences.get('sleep_start', '23:00'))
        sleep_end = self._parse_time_string(self.preferences.get('sleep_end', '07:00'))
        
        # Check for events overlapping sleep window
        sleep_intrusion_hours = 0
        intrusion_count = 0
        
        for event in self.events:
            overlap = self._calculate_sleep_overlap(event, sleep_start, sleep_end)
            if overlap > 0:
                sleep_intrusion_hours += overlap
                intrusion_count += 1
        
        # CRITICAL FIX: Sleep is NON-NEGOTIABLE - no cap on penalty
        # AASM research: 7-9h sleep needed, chronic deprivation has severe health consequences
        # Each hour of intrusion = -10 points (was -5 with cap at -40)
        intrusion_penalty = sleep_intrusion_hours * 10
        
        # Base score: Perfect if no intrusions
        base_score = 100
        final_score = max(0, base_score - intrusion_penalty)
        
        return {
            'score': int(final_score),
            'intrusion_hours': round(sleep_intrusion_hours, 1),
            'intrusion_count': intrusion_count,
            'message': 'No sleep intrusions' if intrusion_count == 0 else f'{intrusion_count} events during sleep hours'
        }
    
    def _calculate_focus_blocks(self):
        """Calculate focus blocks score (20% weight) - UCI research."""
        if not self.work_events:
            # No work events = no focus blocks possible
            return {
                'score': 0,
                'focus_hours': 0,
                'focus_blocks': 0,
                'interrupted_blocks': 0,
                'message': 'No work events scheduled'
            }
        
        focus_hours = 0
        focus_blocks_count = 0
        interrupted_blocks = 0
        
        for event in self.work_events:
            duration = self._calculate_duration(event)
            if duration >= 90:  # 90+ minute work blocks
                # Check for interruptions during this block
                has_meeting = self._check_overlapping_meetings(event)
                if not has_meeting:
                    focus_hours += duration / 60
                    focus_blocks_count += 1
                else:
                    interrupted_blocks += 1
        
        # Scoring (optimal: ≥8h/week of 90+ min blocks)
        if focus_hours >= 8:
            score = 100
        elif focus_hours >= 4:
            score = 80 + (focus_hours - 4) / 4 * 20  # 80-100
        elif focus_hours >= 2:
            score = 60 + (focus_hours - 2) / 2 * 20  # 60-80
        else:
            score = 40 if focus_hours > 0 else 0
        
        return {
            'score': int(score),
            'focus_hours': round(focus_hours, 1),
            'focus_blocks': focus_blocks_count,
            'interrupted_blocks': interrupted_blocks
        }
    
    def _calculate_meeting_load(self):
        """Calculate meeting load score (15% weight) - Microsoft research."""
        work_events = self.work_events + self.meetings
        
        if not work_events:
            # No work or meetings scheduled
            return {
                'score': 0,
                'total_hours': 0,
                'back_to_back': 0,
                'meeting_days': 0,
                'message': 'No work or meetings scheduled'
            }
        
        if not self.meetings:
            # Has work but no meetings = good (focus mode)
            return {
                'score': 100,
                'total_hours': 0,
                'back_to_back': 0,
                'meeting_days': 0,
                'message': 'Deep work mode - no meetings'
            }
        
        # Calculate meeting share
        total_work_minutes = sum(self._calculate_duration(e) for e in work_events)
        meeting_minutes = sum(self._calculate_duration(e) for e in self.meetings)
        meeting_share = meeting_minutes / total_work_minutes if total_work_minutes > 0 else 0
        
        # Base score from share (Gartner: >50% = 40% productivity drop)
        if meeting_share <= 0.30:
            base_score = 100 - (meeting_share * 50)  # 100 at 0%, 85 at 30%
        elif meeting_share <= 0.50:
            base_score = 85 - ((meeting_share - 0.30) / 0.20) * 25  # 85→60
        else:
            base_score = 60 - ((meeting_share - 0.50) / 0.50) * 30  # 60→30
        
        # Back-to-back penalty (Microsoft: <10min gap → stress)
        meetings_sorted = sorted(self.meetings, key=lambda x: x['start'])
        b2b_count = 0
        for i in range(len(meetings_sorted) - 1):
            gap = self._calculate_gap_minutes(meetings_sorted[i], meetings_sorted[i+1])
            if 0 <= gap < 10:
                b2b_count += 1
        b2b_penalty = min(b2b_count * 2, 20)
        
        # Long meeting penalty (Atlassian: fatigue after 4-5h/day)
        long_meetings = sum(1 for m in self.meetings if self._calculate_duration(m) > 60)
        long_penalty = min(long_meetings, 10)
        
        final_score = max(0, base_score - b2b_penalty - long_penalty)
        
        return {
            'score': int(final_score),
            'share': round(meeting_share * 100, 1),
            'b2b_count': b2b_count,
            'long_meetings': long_meetings
        }
    
    def _calculate_recovery_time(self):
        """
        Calculate recovery time score (15% weight).
        
        Prioritization (highest to lowest impact):
        1. Active recovery events (Recreational/Meal) - 80% of score
        2. Gaps after meetings (for mental recovery) - 15% of score  
        3. Gaps after long work blocks - 5% of score
        
        Rationale: Active recovery >> passive gaps
        """
        # Part 1: Active recovery events (80% weight)
        active_recovery_events = self.recreational_events + self.meal_events
        total_recovery_minutes = sum(self._calculate_duration(e) for e in active_recovery_events)
        recovery_hours = total_recovery_minutes / 60
        
        # CRITICAL FIX: Handle no recovery events
        if not active_recovery_events:
            active_score = 0  # No active recovery = not healthy
        # Ideal: 1-2 hours of active recovery per day (7-14 hours per week)
        elif 7 <= recovery_hours <= 14:
            active_score = 100
        elif recovery_hours > 14:
            # Balanced: Penalize excessive recreation without extreme drops
            # Clean numbers: 2 points per excess hour (14h→50% at 39h, 0% at 64h)
            excess = recovery_hours - 14
            penalty = excess * 2  # Clean multiplier, NO CAP
            active_score = max(0, 100 - penalty)  # Can reach 0 at 64h
        elif recovery_hours >= 3.5:  # Half of ideal minimum
            active_score = 50 + (recovery_hours / 7) * 50  # Scale 50-100
        else:
            active_score = (recovery_hours / 3.5) * 50  # Scale 0-50
        
        # Part 2: Gaps after meetings (15% weight) - important for mental reset
        meetings_with_gaps = 0
        for meeting in self.meetings:
            meeting_end = self._parse_iso(meeting['end'])
            # Find next event
            next_event_start = None
            for event in self.events:
                event_start = self._parse_iso(event['start'])
                if event_start > meeting_end:
                    if next_event_start is None or event_start < next_event_start:
                        next_event_start = event_start
            
            if next_event_start:
                gap_minutes = (next_event_start - meeting_end).total_seconds() / 60
                if gap_minutes >= 5:  # At least 5min gap
                    meetings_with_gaps += 1
        
        meeting_gap_score = 100 if len(self.meetings) == 0 else (meetings_with_gaps / len(self.meetings)) * 100
        
        # Part 3: Gaps after long work blocks (5% weight) - minor factor
        long_work_blocks = [e for e in self.work_events if self._calculate_duration(e) >= 90]
        work_blocks_with_gaps = 0
        for block in long_work_blocks:
            block_end = self._parse_iso(block['end'])
            next_event_start = None
            for event in self.events:
                event_start = self._parse_iso(event['start'])
                if event_start > block_end:
                    if next_event_start is None or event_start < next_event_start:
                        next_event_start = event_start
            
            if next_event_start:
                gap_minutes = (next_event_start - block_end).total_seconds() / 60
                if gap_minutes >= 5:
                    work_blocks_with_gaps += 1
        
        work_gap_score = 100 if len(long_work_blocks) == 0 else (work_blocks_with_gaps / len(long_work_blocks)) * 100
        
        # Weighted composite
        final_score = (active_score * 0.80) + (meeting_gap_score * 0.15) + (work_gap_score * 0.05)
        
        return {
            'score': int(final_score),
            'active_recovery_hours': round(recovery_hours, 1),
            'meetings_with_gaps': meetings_with_gaps,
            'total_meetings': len(self.meetings),
            'work_blocks_with_gaps': work_blocks_with_gaps,
            'total_long_blocks': len(long_work_blocks)
        }
    
    def _generate_issues(self, breakdown):
        """Generate list of issues from breakdown."""
        issues = []
        
        # Work/Life Balance issues
        wl_data = breakdown['work_life']
        if wl_data['hours'] >= 55:
            issues.append(f"⚠️ Excessive work hours ({wl_data['hours']}h/week) - WHO: ≥55h → +35% stroke risk")
        elif wl_data['hours'] >= 50:
            issues.append(f"⚠️ High work hours ({wl_data['hours']}h/week) - Productivity drops after 50h")
        
        if wl_data['long_days'] > 1:
            issues.append(f"⚠️ {wl_data['long_days']} days with >10h work - Linked to higher depression scores")
        
        if wl_data['weekend_night_hours'] > 2:
            issues.append(f"⚠️ {wl_data['weekend_night_hours']}h weekend/night work - Reduces recovery time")
        
        # Sleep issues
        sleep_data = breakdown['sleep_respect']
        if sleep_data['intrusion_count'] > 0:
            issues.append(f"⚠️ {sleep_data['intrusion_count']} events during sleep window ({sleep_data['intrusion_hours']}h)")
        
        # Focus issues
        focus_data = breakdown['focus_blocks']
        if focus_data.get('focus_hours', 0) < 4:
            issues.append(f"⚠️ Only {focus_data.get('focus_hours', 0)}h of deep focus time - UCI: Need 8h/week for productivity")
        
        # Meeting issues
        meeting_data = breakdown['meetings']
        if meeting_data.get('total_hours', 0) > 0:
            # Only check share if we have work time
            meeting_hours = meeting_data.get('total_hours', 0)
            work_hours = wl_data.get('hours', 0)
            if work_hours > 0:
                share_pct = (meeting_hours / work_hours) * 100
                if share_pct > 50:
                    issues.append(f"⚠️ Meetings = {share_pct:.0f}% of work time - Gartner: >50% → 40% productivity drop")
        
        if meeting_data.get('back_to_back', 0) > 3:
            issues.append(f"⚠️ {meeting_data.get('back_to_back', 0)} back-to-back meetings - Microsoft: Sustained stress response")
        
        # Recovery issues
        recovery_data = breakdown['recovery']
        if recovery_data['active_recovery_hours'] < 3.5:
            issues.append(f"⚠️ Only {recovery_data['active_recovery_hours']}h active recovery - Schedule Recreational/Meal events")
        
        if recovery_data['total_meetings'] > 0 and recovery_data['meetings_with_gaps'] < recovery_data['total_meetings'] * 0.5:
            issues.append(f"⚠️ Only {recovery_data['meetings_with_gaps']}/{recovery_data['total_meetings']} meetings have gaps after - Leave 5-10min between meetings")
        
        return issues[:5]  # Return top 5 issues
    
    def _generate_suggestions(self, breakdown):
        """Generate actionable suggestions with predicted improvements."""
        suggestions = []
        
        # Work/Life Balance suggestions
        wl_data = breakdown['work_life']
        if wl_data['hours'] > 50:
            target = 45
            reduction = wl_data['hours'] - target
            new_score = self._predict_work_life_score(target)
            suggestions.append(
                f"💡 Reduce work hours to {target}h/week (-{reduction:.1f}h) → Score improves to {new_score} "
                f"(Stanford: Productivity plateaus at 45h)"
            )
        
        if wl_data['long_days'] > 1:
            suggestions.append(
                f"💡 Limit workdays to ≤10h → Reduces depression risk (Virtanen et al., PLoS One)"
            )
        
        # Sleep suggestions
        sleep_data = breakdown['sleep_respect']
        if sleep_data['intrusion_count'] > 0:
            suggestions.append(
                f"💡 Move {sleep_data['intrusion_count']} events outside sleep window "
                f"({self.preferences.get('sleep_start', '23:00')}-{self.preferences.get('sleep_end', '07:00')}) "
                f"→ Score improves to 100 (AASM: 7-9h uninterrupted sleep)"
            )
        
        # Focus suggestions
        focus_data = breakdown['focus_blocks']
        if focus_data.get('focus_hours', 0) < 8:
            needed = 8 - focus_data.get('focus_hours', 0)
            suggestions.append(
                f"💡 Add {needed:.1f}h of 90+ min focus blocks → Score improves to 100 "
                f"(UCI: 23min recovery from each interruption)"
            )
        
        # Meeting suggestions
        meeting_data = breakdown['meetings']
        if meeting_data.get('back_to_back', 0) > 0:
            suggestions.append(
                f"💡 Add 10-min breaks between meetings → Reduces {meeting_data.get('back_to_back', 0)} back-to-backs "
                f"(Microsoft: Breaks restore baseline brain activity)"
            )
        
        if meeting_data.get('total_hours', 0) > 4:
            suggestions.append(
                f"💡 Limit meetings to <4h/day → Reduces cognitive fatigue (Atlassian)"
            )
        
        # Recovery suggestions
        recovery_data = breakdown['recovery']
        if recovery_data['active_recovery_hours'] < 7:
            needed = 7 - recovery_data['active_recovery_hours']
            suggestions.append(
                f"💡 Add {needed:.1f}h of Recreational/Meal events → Score improves to 100 "
                f"(Active recovery >> passive gaps)"
            )
        
        if recovery_data['total_meetings'] > 0 and recovery_data['meetings_with_gaps'] < recovery_data['total_meetings']:
            missing = recovery_data['total_meetings'] - recovery_data['meetings_with_gaps']
            suggestions.append(
                f"💡 Leave 5-10min gaps after {missing} meetings → Improves mental recovery "
                f"(Microsoft: Gaps reset brain activity)"
            )
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _calculate_weekly_stats(self, breakdown):
        """Calculate summary statistics."""
        return {
            'work_hours': breakdown['work_life']['hours'],
            'meeting_hours': breakdown['meetings'].get('total_hours', 0),
            'recovery_hours': breakdown['recovery']['active_recovery_hours'],
            'sleep_intrusions': breakdown['sleep_respect']['intrusion_count'],
            'focus_time': breakdown['focus_blocks'].get('focus_hours', 0)
        }
    
    # Helper methods
    
    def _calculate_duration(self, event):
        """Calculate event duration in minutes."""
        start = self._parse_iso(event['start'])
        end = self._parse_iso(event['end'])
        return (end - start).total_seconds() / 60
    
    def _parse_iso(self, date_string):
        """Parse ISO datetime string."""
        if date_string.endswith('Z'):
            date_string = date_string[:-1]
        if '.' in date_string:
            date_string = date_string.split('.')[0]
        try:
            return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return datetime.strptime(date_string, "%Y-%m-%dT%H:%M")
    
    def _parse_time_string(self, time_string):
        """Parse time string in HH:MM format to time object."""
        return datetime.strptime(time_string, "%H:%M").time()
    
    def _group_by_day(self, events):
        """Group events by day and sum hours."""
        daily_hours = defaultdict(float)
        for event in events:
            dt = self._parse_iso(event['start'])
            day_key = dt.date()
            duration_hours = self._calculate_duration(event) / 60
            daily_hours[day_key] += duration_hours
        return daily_hours
    
    def _calculate_sleep_overlap(self, event, sleep_start, sleep_end):
        """Calculate hours of event overlapping with sleep window."""
        event_start = self._parse_iso(event['start'])
        event_end = self._parse_iso(event['end'])
        
        # Create sleep window for the event's day
        event_date = event_start.date()
        
        # Handle sleep window that crosses midnight
        if sleep_start > sleep_end:
            # Sleep starts today, ends tomorrow
            sleep_window_start = datetime.combine(event_date, sleep_start)
            sleep_window_end = datetime.combine(event_date + timedelta(days=1), sleep_end)
        else:
            # Sleep is within same day
            sleep_window_start = datetime.combine(event_date, sleep_start)
            sleep_window_end = datetime.combine(event_date, sleep_end)
        
        # Calculate overlap
        overlap_start = max(event_start, sleep_window_start)
        overlap_end = min(event_end, sleep_window_end)
        
        if overlap_start < overlap_end:
            return (overlap_end - overlap_start).total_seconds() / 3600
        return 0
    
    def _check_overlapping_meetings(self, work_event):
        """Check if work event has overlapping meetings."""
        work_start = self._parse_iso(work_event['start'])
        work_end = self._parse_iso(work_event['end'])
        
        for meeting in self.meetings:
            meeting_start = self._parse_iso(meeting['start'])
            meeting_end = self._parse_iso(meeting['end'])
            
            # Check for any overlap
            if meeting_start < work_end and meeting_end > work_start:
                return True
        return False
    
    def _calculate_gap_minutes(self, event1, event2):
        """Calculate gap in minutes between two events."""
        end1 = self._parse_iso(event1['end'])
        start2 = self._parse_iso(event2['start'])
        return (start2 - end1).total_seconds() / 60
    
    def _predict_work_life_score(self, target_hours):
        """Predict work/life score for target hours."""
        if 35 <= target_hours <= 45:
            return 100
        elif 45 < target_hours <= 55:
            return int(100 - ((target_hours - 45) / 10) * 30)
        else:
            return 40
