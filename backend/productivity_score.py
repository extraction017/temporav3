"""
TEMPORA Productivity Score Calculator
Measures time allocation efficiency - how intelligently users schedule their available time.
Based on 7+ peer-reviewed studies on time management, fragmentation costs, and efficiency.

Key principle: This is NOT "more work = better" but "smarter allocation + waste minimization = better"
"""

from datetime import datetime, timedelta, time
from collections import defaultdict


class ProductivityScoreCalculator:
    """Calculate productivity/efficiency score from calendar events."""
    
    # Metric weights (must sum to 1.0)
    WEIGHTS = {
        'block_structure': 0.35,      # Time chunking efficiency (deep work blocks) - INCREASED
        'fragmentation': 0.15,        # Transition cost / context switching (internal vs external)
        'schedule_balance': 0.20,     # MERGED: Utilization + Planning Buffer (was 0.30 total)
        'meeting_efficiency': 0.20,   # Meeting-to-work flow optimization
        'recovery_support': 0.10      # Adequate non-work recovery (productivity lens: sustainability)
    }
    
    # Research-based thresholds
    DEEP_WORK_THRESHOLD = 90        # Minutes for "deep block" (time blocking research)
    TRANSITION_COST = 15            # Minutes lost per context switch (9.5-23 min research)
    OPTIMAL_MEETING_SHARE = 0.30    # <30% meeting time is optimal
    SAFE_WORK_HOURS = 45            # Hours/week before diminishing returns
    MIN_RECOVERY_HOURS = 10         # Minimum recreation + personal time/week
    OPTIMAL_SLACK = 0.08            # 8% unallocated time as buffer (5-10% range)
    MAX_CONTINUOUS_WORK = 240       # 4 hours max without break (cognitive fatigue)
    
    def __init__(self, events, preferences):
        """
        Initialize calculator with events and user preferences.
        
        Args:
            events: List of event dictionaries
            preferences: User preferences dictionary
        """
        self.events = events
        self.preferences = preferences
        self.work_events = []
        self.meetings = []
        self.personal_events = []
        self.recreational_events = []
        
        # Categorize events
        for event in events:
            category = event.get('category', 'Personal')
            if category == 'Work':
                self.work_events.append(event)
            elif category == 'Meeting':
                self.meetings.append(event)
            elif category == 'Personal':
                self.personal_events.append(event)
            elif category == 'Recreational':
                self.recreational_events.append(event)
    
    def calculate_score(self):
        """
        Calculate comprehensive productivity score.
        
        Returns:
            Dictionary with score, breakdown, insights, and recommendations
        """
        # CRITICAL FIX: Check for empty schedule first
        total_events = len(self.work_events + self.meetings + self.personal_events + self.recreational_events)
        if total_events == 0:
            return {
                'score': 0,
                'breakdown': {
                    'block_structure': 0,
                    'fragmentation': 0,
                    'schedule_balance': 0,
                    'meeting_efficiency': 0,
                    'recovery_support': 0
                },
                'details': {
                    'block_structure': {'score': 0, 'deep_blocks': 0, 'deep_hours': 0, 'avg_block_length': 0},
                    'fragmentation': {'score': 0, 'transitions': 0, 'weighted_transitions': 0, 'fragmented_hours': 0, 'avg_gap': 0, 'short_gaps': 0},
                    'schedule_balance': {'score': 0, 'utilization': 0, 'slack': 100, 'scheduled_hours': 0, 'buffer_hours': 0, 'work_hours': 0},
                    'meeting_efficiency': {'score': 0, 'flow_blocks': 0, 'orphaned_meetings': 0, 'avg_followup_gap': 0},
                    'recovery_support': {'score': 0, 'recovery_hours': 0, 'personal_hours': 0, 'recreational_hours': 0}
                },
                'inefficiencies': ['⚠️ No events scheduled - cannot assess productivity'],
                'optimizations': [
                    '💡 Start by scheduling work blocks (90+ min for deep work)',
                    '💡 Add meetings with clear action items',
                    '💡 Schedule personal/recreational time for recovery'
                ],
                'efficiency_stats': {
                    'deep_work_hours': 0,
                    'context_switches': 0,
                    'wasted_hours': 0,
                    'buffer_hours': 0,
                    'work_utilization': 0
                }
            }
        
        # Calculate individual metrics
        block_data = self._calculate_block_structure()
        frag_data = self._calculate_fragmentation()
        balance_data = self._calculate_schedule_balance()  # MERGED metric
        meeting_data = self._calculate_meeting_efficiency()
        recovery_data = self._calculate_recovery_support()
        
        # Composite score
        composite = (
            self.WEIGHTS['block_structure'] * block_data['score'] +
            self.WEIGHTS['fragmentation'] * frag_data['score'] +
            self.WEIGHTS['schedule_balance'] * balance_data['score'] +
            self.WEIGHTS['meeting_efficiency'] * meeting_data['score'] +
            self.WEIGHTS['recovery_support'] * recovery_data['score']
        )
        
        # Generate insights
        breakdown = {
            'block_structure': block_data,
            'fragmentation': frag_data,
            'schedule_balance': balance_data,  # MERGED
            'meeting_efficiency': meeting_data,
            'recovery_support': recovery_data
        }
        
        inefficiencies = self._generate_inefficiencies(breakdown)
        optimizations = self._generate_optimizations(breakdown)
        
        return {
            'score': int(round(composite)),
            'breakdown': {
                'block_structure': block_data['score'],
                'fragmentation': frag_data['score'],
                'schedule_balance': balance_data['score'],  # MERGED
                'meeting_efficiency': meeting_data['score'],
                'recovery_support': recovery_data['score']
            },
            'details': breakdown,
            'inefficiencies': inefficiencies,
            'optimizations': optimizations,
            'efficiency_stats': self._calculate_efficiency_stats(breakdown)
        }
    
    def _calculate_block_structure(self):
        """
        Calculate time chunking efficiency (25% weight).
        Research: Time blocking / deep work blocks improve productivity.
        """
        # CRITICAL FIX: No work events = not productive, score should be 0
        if not self.work_events:
            return {
                'score': 0,  # No work = not productive (was giving points)
                'deep_blocks': 0,
                'deep_hours': 0,
                'avg_block_length': 0
            }
        
        deep_blocks = []
        total_deep_minutes = 0
        
        # Find deep work blocks (≥90 min uninterrupted work)
        for event in self.work_events:
            duration = self._calculate_duration(event)
            if duration >= self.DEEP_WORK_THRESHOLD:
                # Check if interrupted by meetings
                has_interruption = self._check_overlapping_meetings(event)
                if not has_interruption:
                    deep_blocks.append(event)
                    total_deep_minutes += duration
        
        deep_hours = total_deep_minutes / 60
        
        # Scoring (based on time blocking research)
        # Optimal: ≥10h/week of deep blocks
        if deep_hours >= 10:
            score = 100
        elif deep_hours >= 6:
            score = 80 + (deep_hours - 6) / 4 * 20  # 80-100
        elif deep_hours >= 3:
            score = 60 + (deep_hours - 3) / 3 * 20  # 60-80
        else:
            score = max(0, (deep_hours / 3) * 60)   # 0-60
        
        return {
            'score': int(score),
            'deep_blocks': len(deep_blocks),
            'deep_hours': round(deep_hours, 1),
            'avg_block_length': round(total_deep_minutes / len(deep_blocks), 0) if deep_blocks else 0
        }
    
    def _calculate_fragmentation(self):
        """
        Calculate context switching cost (20% weight).
        Research: 9.5-23 min recovery time per interruption.
        UPDATED: Separates internal (within work) vs external (work↔meeting/personal) transitions.
        """
        # Get all events sorted by time
        all_events = sorted(
            self.work_events + self.meetings + self.personal_events + self.recreational_events,
            key=lambda x: x['start']
        )
        
        if len(all_events) == 0:
            # CRITICAL FIX: No events = not productive (score 0)
            return {
                'score': 0,
                'transitions': 0,
                'internal_transitions': 0,
                'external_transitions': 0,
                'weighted_transitions': 0,
                'fragmented_hours': 0,
                'avg_gap': 0,
                'short_gaps': 0,
                'message': 'No events to analyze'
            }
        
        if len(all_events) == 1:
            # CRITICAL FIX: Single event = perfect focus (score 100)
            return {
                'score': 100,
                'transitions': 0,
                'internal_transitions': 0,
                'external_transitions': 0,
                'weighted_transitions': 0,
                'fragmented_hours': 0,
                'avg_gap': 0,
                'short_gaps': 0,
                'message': 'Single uninterrupted event'
            }
        
        # Count category transitions WITH DURATION WEIGHTING
        transitions = 0
        internal_transitions = 0  # Work→Work transitions (low cost)
        external_transitions = 0  # Work↔Meeting/Personal transitions (high cost)
        weighted_transitions = 0.0  # Account for event duration impact
        short_gaps = 0  # <15 min gaps (wasted/unproductive)
        total_gap_minutes = 0
        
        for i in range(len(all_events) - 1):
            curr_event = all_events[i]
            next_event = all_events[i + 1]
            curr_category = curr_event.get('category')
            next_category = next_event.get('category')
            
            # Calculate gap between events
            gap = self._calculate_gap_minutes(curr_event, next_event)
            
            if gap >= 0 and gap < 15:
                short_gaps += 1
            
            total_gap_minutes += max(0, gap)
            
            # Count transitions (different category)
            if curr_category != next_category:
                transitions += 1
                
                # Classify transition type:
                # Internal = within "productive" categories (Work <-> Meeting)
                # External = crossing into/out of personal time (Work/Meeting <-> Personal/Recreational)
                productive_categories = {'Work', 'Meeting'}
                personal_categories = {'Personal', 'Recreational'}
                
                curr_is_productive = curr_category in productive_categories
                next_is_productive = next_category in productive_categories
                
                if curr_is_productive and next_is_productive:
                    # Internal: Work <-> Meeting transitions (lower cost - still work-related)
                    internal_transitions += 1
                    is_internal = True
                else:
                    # External: Crossing work/personal boundary (higher cost - major context shift)
                    external_transitions += 1
                    is_internal = False
                
                # CRITICAL FIX: Weight transitions by event duration AND transition type
                # Shorter events = higher cognitive switching cost
                curr_duration = self._calculate_duration(curr_event)
                next_duration = self._calculate_duration(next_event)
                avg_duration = (curr_duration + next_duration) / 2
                
                # Base weight from duration
                if avg_duration < 30:  # Very short events (<30 min avg)
                    duration_weight = 2.0  # Double penalty - rapid switching is exhausting
                elif avg_duration < 60:  # Short events (30-60 min avg)
                    duration_weight = 1.5  # 50% penalty - still significant cost
                else:  # Normal/long events (60+ min avg)
                    duration_weight = 1.0  # Standard cost
                
                # Modifier for transition type
                if is_internal:
                    # Internal transitions (Work→Work) are less costly
                    type_weight = 0.5  # Half the cost of external transitions
                else:
                    # External transitions (Work↔Meeting/Personal) are full cost
                    type_weight = 1.0
                
                weight = duration_weight * type_weight
                weighted_transitions += weight
        
        # Calculate fragmented time cost using WEIGHTED transitions
        # Each transition costs ~15 min base, but weighted by event duration and type
        fragmented_hours = (weighted_transitions * self.TRANSITION_COST + short_gaps * 5) / 60
        
        # Scoring (fewer weighted transitions = better)
        # Optimal: ≤15 weighted transitions/week (accounts for duration + type impact)
        if weighted_transitions <= 15:
            score = 100
        elif weighted_transitions <= 30:
            score = 100 - (weighted_transitions - 15) / 15 * 20  # 100-80
        elif weighted_transitions <= 50:
            score = 80 - (weighted_transitions - 30) / 20 * 20  # 80-60
        else:
            score = max(0, 60 - (weighted_transitions - 50) / 30 * 30)  # 60-30
        
        # Additional penalty for short gaps (wasted waiting time)
        short_gap_penalty = min(short_gaps * 2, 20)
        
        final_score = max(0, score - short_gap_penalty)
        
        return {
            'score': int(final_score),
            'transitions': transitions,
            'internal_transitions': internal_transitions,  # NEW: Work→Work
            'external_transitions': external_transitions,  # NEW: Work↔Other
            'weighted_transitions': round(weighted_transitions, 1),  # Duration + type weighted
            'fragmented_hours': round(fragmented_hours, 1),
            'avg_gap': round(total_gap_minutes / max(len(all_events) - 1, 1), 0),
            'short_gaps': short_gaps
        }
    
    def _calculate_schedule_balance(self):
        """
        Calculate schedule balance: utilization + buffer (20% weight).
        MERGED: Combines old utilization (15%) + planning_buffer (15%) metrics.
        
        Research: Optimal is 75-85% scheduled, 15-25% buffer.
        - Too scheduled (>90%) = no flexibility, stress, overruns cascade
        - Too empty (<50%) = underutilization, lack of structure
        - Sweet spot (75-85%) = productive but adaptable
        """
        # Calculate total scheduled time
        total_scheduled_minutes = sum(
            self._calculate_duration(e) 
            for e in self.work_events + self.meetings + self.personal_events + self.recreational_events
        )
        
        # Calculate available time (work hours per day × 7 days)
        work_start = self._parse_time_string(self.preferences.get('work_start', '09:00'))
        work_end = self._parse_time_string(self.preferences.get('work_end', '18:00'))
        
        work_hours_per_day = (datetime.combine(datetime.min, work_end) - datetime.combine(datetime.min, work_start)).total_seconds() / 3600
        available_minutes = work_hours_per_day * 60 * 7  # 7 days
        
        # Calculate utilization ratio
        if available_minutes == 0:
            util_ratio = 0
        else:
            util_ratio = total_scheduled_minutes / available_minutes
        
        slack_ratio = 1 - util_ratio
        
        # Scoring (optimal: 75-85% utilization = 15-25% slack)
        if 0.75 <= util_ratio <= 0.85:
            score = 100  # Perfect balance
        elif 0.70 <= util_ratio < 0.75:
            # Slightly under-scheduled
            score = 90 + (util_ratio - 0.70) / 0.05 * 10  # 90-100
        elif 0.85 < util_ratio <= 0.90:
            # Slightly over-scheduled
            score = 90 - (util_ratio - 0.85) / 0.05 * 10  # 100-90
        elif 0.65 <= util_ratio < 0.70:
            # Under-scheduled (too much slack)
            score = 75 + (util_ratio - 0.65) / 0.05 * 15  # 75-90
        elif 0.90 < util_ratio <= 0.95:
            # Over-scheduled (risky)
            score = 70 - (util_ratio - 0.90) / 0.05 * 20  # 90-70
        elif util_ratio > 0.95:
            # Dangerously over-scheduled
            score = max(30, 70 - (util_ratio - 0.95) * 200)  # 70-30
        else:
            # Severely under-scheduled (<65%)
            score = max(40, util_ratio / 0.65 * 75)  # 0-75
        
        # Check work hours for overwork penalty
        work_meeting_minutes = sum(
            self._calculate_duration(e) 
            for e in self.work_events + self.meetings
        )
        work_hours = work_meeting_minutes / 60
        
        # CRITICAL FIX: Stronger progressive overwork penalty (research: 30%+ productivity drop after 50h)
        if work_hours > 50:
            if work_hours <= 60:
                # Moderate penalty zone (50-60h)
                overwork_penalty = (work_hours - 50) * 3  # -30 max at 60h
            else:
                # Severe penalty zone (>60h) - accelerating decline
                overwork_penalty = 30 + (work_hours - 60) * 5  # -30 baseline + -5 per hour
            score = max(20, score - overwork_penalty)  # Floor at 20 (was 30)
        
        return {
            'score': int(score),
            'utilization': round(util_ratio * 100, 1),
            'slack': round(slack_ratio * 100, 1),
            'scheduled_hours': round(total_scheduled_minutes / 60, 1),
            'buffer_hours': round((available_minutes - total_scheduled_minutes) / 60, 1),
            'work_hours': round(work_hours, 1)
        }
    
    def _calculate_meeting_efficiency(self):
        """
        Calculate meeting-to-work flow optimization (15% weight).
        Research: Meetings should lead to implementation blocks.
        """
        if not self.meetings:
            # CRITICAL FIX: No meetings = check if user has work (focus mode vs empty schedule)
            if self.work_events:
                # Focus mode: All work, no meetings = perfect efficiency
                return {
                    'score': 100,
                    'flow_blocks': 0,
                    'orphaned_meetings': 0,
                    'avg_followup_gap': 0,
                    'message': 'Deep work week - no meetings scheduled'
                }
            else:
                # Empty schedule: No work or meetings
                return {
                    'score': 0,
                    'flow_blocks': 0,
                    'orphaned_meetings': 0,
                    'avg_followup_gap': 0,
                    'message': 'No work or meetings scheduled'
                }
        
        
        flow_blocks = 0  # Meetings followed by related work
        orphaned_meetings = 0  # Meetings not followed by work
        followup_gaps = []
        
        for meeting in self.meetings:
            meeting_end = self._parse_iso(meeting['end'])
            
            # Look for work block within 2 hours after meeting
            found_followup = False
            for work in self.work_events:
                work_start = self._parse_iso(work['start'])
                gap = (work_start - meeting_end).total_seconds() / 60
                
                if 0 <= gap <= 120:  # Within 2 hours
                    flow_blocks += 1
                    followup_gaps.append(gap)
                    found_followup = True
                    break
            
            if not found_followup:
                orphaned_meetings += 1
        
        # Scoring (more flow blocks = better)
        flow_ratio = flow_blocks / len(self.meetings) if self.meetings else 0
        
        if flow_ratio >= 0.70:
            score = 100
        elif flow_ratio >= 0.50:
            score = 80 + (flow_ratio - 0.50) / 0.20 * 20
        elif flow_ratio >= 0.30:
            score = 60 + (flow_ratio - 0.30) / 0.20 * 20
        else:
            score = flow_ratio / 0.30 * 60
        
        return {
            'score': int(score),
            'flow_blocks': flow_blocks,
            'orphaned_meetings': orphaned_meetings,
            'avg_followup_gap': round(sum(followup_gaps) / len(followup_gaps), 0) if followup_gaps else 0
        }
    
    # DEPRECATED: Old _calculate_utilization method removed - merged into _calculate_schedule_balance
    
    def _calculate_recovery_support(self):
        """
        Calculate recovery/non-work adequacy (10% weight).
        Research: Efficiency unsustainable without recovery.
        """
        # Total recovery time (personal + recreational)
        recovery_minutes = sum(
            self._calculate_duration(e)
            for e in self.personal_events + self.recreational_events
        )
        recovery_hours = recovery_minutes / 60
        
        # Scoring (minimum 10h/week recovery)
        if recovery_hours >= self.MIN_RECOVERY_HOURS:
            score = 100
        elif recovery_hours >= 7:
            score = 80 + (recovery_hours - 7) / 3 * 20
        elif recovery_hours >= 4:
            score = 50 + (recovery_hours - 4) / 3 * 30
        else:
            score = max(0, (recovery_hours / 4) * 50)
        
        return {
            'score': int(score),
            'recovery_hours': round(recovery_hours, 1),
            'personal_hours': round(sum(self._calculate_duration(e) for e in self.personal_events) / 60, 1),
            'recreational_hours': round(sum(self._calculate_duration(e) for e in self.recreational_events) / 60, 1)
        }
    
    def _generate_inefficiencies(self, breakdown):
        """Generate list of inefficiencies detected."""
        inefficiencies = []
        
        # Block structure issues
        block_data = breakdown['block_structure']
        if block_data['deep_hours'] < 6:
            inefficiencies.append(
                f"⚠️ Only {block_data['deep_hours']}h of deep work blocks - "
                f"Research: Time blocking improves productivity (need ≥10h/week)"
            )
        
        # Fragmentation issues
        frag_data = breakdown['fragmentation']
        if frag_data['transitions'] > 20:
            ext_trans = frag_data.get('external_transitions', frag_data['transitions'])
            int_trans = frag_data.get('internal_transitions', 0)
            inefficiencies.append(
                f"⚠️ {frag_data['transitions']} context switches ({ext_trans} external, {int_trans} internal) - "
                f"~{frag_data['fragmented_hours']}h recovery time lost (15 min per switch)"
            )
        
        if frag_data['short_gaps'] > 5:
            inefficiencies.append(
                f"⚠️ {frag_data['short_gaps']} short gaps (<15 min) - "
                f"Wasted waiting time that's hard to utilize productively"
            )
        
        # Buffer/Balance issues (MERGED into schedule_balance)
        balance_data = breakdown['schedule_balance']
        if balance_data['slack'] < 2:
            inefficiencies.append(
                f"⚠️ Over-scheduled: only {balance_data['slack']}% slack - "
                f"No buffer for overruns or unexpected tasks (need 5-10%)"
            )
        elif balance_data['slack'] > 20:
            inefficiencies.append(
                f"⚠️ Under-scheduled: {balance_data['slack']}% idle time - "
                f"Opportunity to add more productive tasks"
            )
        
        # Meeting efficiency issues
        meeting_data = breakdown['meeting_efficiency']
        if meeting_data['orphaned_meetings'] > 2:
            inefficiencies.append(
                f"⚠️ {meeting_data['orphaned_meetings']} meetings with no follow-up work - "
                f"Potential waste if no action items implemented"
            )
        
        # Work hours and overwork issues (MERGED into schedule_balance)
        balance_data = breakdown['schedule_balance']
        if balance_data['work_hours'] > 50:
            inefficiencies.append(
                f"⚠️ {balance_data['work_hours']}h work time - "
                f"Diminishing returns past 45h/week (productivity plateau)"
            )
        
        # Recovery issues
        recovery_data = breakdown['recovery_support']
        if recovery_data['recovery_hours'] < 7:
            inefficiencies.append(
                f"⚠️ Only {recovery_data['recovery_hours']}h recovery time - "
                f"Insufficient for sustained productivity (need ≥10h/week)"
            )
        
        return inefficiencies[:5]  # Top 5
    
    def _generate_optimizations(self, breakdown):
        """Generate actionable optimization recommendations."""
        optimizations = []
        
        # Block structure optimizations
        block_data = breakdown['block_structure']
        if block_data['deep_hours'] < 10:
            needed = 10 - block_data['deep_hours']
            optimizations.append(
                f"💡 Add {needed:.1f}h of 90+ min uninterrupted work blocks → Score improves to 100 "
                f"(Time blocking research: reduces decision overhead)"
            )
        
        # Fragmentation optimizations
        frag_data = breakdown['fragmentation']
        if frag_data['transitions'] > 15:
            ext_trans = frag_data.get('external_transitions', 0)
            int_trans = frag_data.get('internal_transitions', 0)
            
            # Focus on external transitions (higher cost)
            if ext_trans > 10:
                optimizations.append(
                    f"💡 Reduce external transitions: {ext_trans} work↔meeting/personal switches → "
                    f"Batch similar categories to save ~{frag_data['fragmented_hours']}h/week"
                )
            elif int_trans > 10:
                optimizations.append(
                    f"💡 Consolidate work blocks: {int_trans} work→work switches → "
                    f"Merge related tasks into longer focus sessions"
                )
        
        # Buffer optimizations (MERGED into schedule_balance)
        balance_data = breakdown['schedule_balance']
        if balance_data['slack'] < 5:
            needed_buffer = round((0.08 - balance_data['slack'] / 100) * balance_data['scheduled_hours'], 1)
            optimizations.append(
                f"💡 Add {needed_buffer}h buffer time (8% slack) → Absorbs overruns & unexpected tasks "
                f"(Planning research: contingency time improves control)"
            )
        
        # Meeting efficiency optimizations
        meeting_data = breakdown['meeting_efficiency']
        if meeting_data['orphaned_meetings'] > 0:
            optimizations.append(
                f"💡 Schedule work blocks after {meeting_data['orphaned_meetings']} meetings → "
                f"Implement action items while context is fresh (flow efficiency)"
            )
        
        # Recovery optimizations
        recovery_data = breakdown['recovery_support']
        if recovery_data['recovery_hours'] < 10:
            needed = 10 - recovery_data['recovery_hours']
            optimizations.append(
                f"💡 Add {needed:.1f}h recovery time (personal/recreational) → "
                f"Sustains long-term productivity (recovery research)"
            )
        
        return optimizations[:5]  # Top 5
    
    def _calculate_efficiency_stats(self, breakdown):
        """Calculate summary efficiency statistics."""
        return {
            'deep_work_hours': breakdown['block_structure']['deep_hours'],
            'context_switches': breakdown['fragmentation']['transitions'],
            'wasted_hours': breakdown['fragmentation']['fragmented_hours'],
            'buffer_hours': breakdown['schedule_balance']['buffer_hours'],
            'work_utilization': breakdown['schedule_balance']['utilization']
        }
    
    # Helper methods (same as HealthScoreCalculator)
    
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
    
    def _check_overlapping_meetings(self, work_event):
        """Check if work event has overlapping meetings."""
        work_start = self._parse_iso(work_event['start'])
        work_end = self._parse_iso(work_event['end'])
        
        for meeting in self.meetings:
            meeting_start = self._parse_iso(meeting['start'])
            meeting_end = self._parse_iso(meeting['end'])
            
            if meeting_start < work_end and meeting_end > work_start:
                return True
        return False
    
    def _calculate_gap_minutes(self, event1, event2):
        """Calculate gap in minutes between two events."""
        end1 = self._parse_iso(event1['end'])
        start2 = self._parse_iso(event2['start'])
        return (start2 - end1).total_seconds() / 60
