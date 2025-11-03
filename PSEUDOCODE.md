# Tempora - Pseudocode Documentation

## Table of Contents
1. [Event Creation & Handling](#event-creation--handling)
2. [Health Score Calculation](#health-score-calculation)
3. [Productivity Score Calculation](#productivity-score-calculation)
4. [Schedule Balancing & Optimization](#schedule-balancing--optimization)
5. [Event Validation](#event-validation)
6. [Recurring Event Handling](#recurring-event-handling)

---

## Event Creation & Handling

### 1. Create Fixed Event
```
FUNCTION create_fixed_event(title, start_datetime, end_datetime, category, priority, notes):
    // Fixed events have exact start and end times (e.g., doctor appointment)
    
    // Parse and validate input
    start = parse_datetime(start_datetime)
    end = parse_datetime(end_datetime)
    
    IF end <= start:
        RETURN error("End time must be after start time")
    
    // Check for conflicts with existing events
    conflicts = database.check_conflicts(start, end)
    IF conflicts exist:
        RETURN error("Time slot is occupied")
    
    // Check against user preferences
    preferences = database.get_user_preferences()
    
    IF is_during_sleep_hours(start, preferences):
        RETURN warning("Event scheduled during sleep hours")
    
    // Round times to user's preferred interval (5, 10, 15, or 30 min)
    start = round_to_interval(start, preferences.round_to_minutes)
    end = round_to_interval(end, preferences.round_to_minutes)
    
    // Create event object
    event = {
        type: "fixed",
        title: title,
        start_time: start,
        end_time: end,
        category: category,
        priority: priority,
        notes: notes,
        locked: false
    }
    
    // Save to database
    event_id = database.insert_event(event)
    
    RETURN event_id
END FUNCTION
```

### 2. Create Recurring Event
```
FUNCTION create_recurring_event(title, duration, frequency, start_date, preferred_time, category, priority):
    // Recurring events repeat at regular intervals (e.g., daily standup, weekly class)
    
    instances = []
    current_date = parse_date(start_date)
    end_date = current_date + 30 days  // Generate 30 days of recurrences
    
    // Parse preferred time window
    pref_start, pref_end = parse_preferred_time(preferred_time)
    
    WHILE current_date <= end_date:
        // Determine if this date matches the frequency
        IF matches_frequency(current_date, frequency):
            
            // Try to schedule in preferred time window first
            slot_start = combine_date_and_time(current_date, pref_start)
            slot_end = slot_start + duration
            
            // Check if slot is available and within preferred window
            conflicts = database.check_conflicts(slot_start, slot_end)
            
            IF no conflicts AND is_within_preferred_time(slot_end, pref_start, pref_end):
                // Create instance at preferred time
                event = {
                    type: "recurring",
                    title: title,
                    start_time: slot_start,
                    end_time: slot_end,
                    category: category,
                    priority: priority,
                    parent_series_id: generate_series_id()
                }
                database.insert_event(event)
                instances.append(event)
            ELSE:
                // Progressive fallback: try alternative times
                alternative_slot = find_alternative_slot(current_date, duration, pref_start, pref_end)
                IF alternative_slot exists:
                    event = create_event_at_slot(alternative_slot, title, duration, category, priority)
                    database.insert_event(event)
                    instances.append(event)
                ELSE:
                    RETURN warning("Could not schedule instance on " + current_date)
        
        // Move to next frequency period
        current_date = get_next_frequency_date(current_date, frequency)
    
    RETURN instances
END FUNCTION
```

### 3. Create Floating Event
```
FUNCTION create_floating_event(title, duration, earliest_start, deadline, preferred_time, category, priority):
    // Floating events are flexible tasks that need to fit somewhere in the schedule
    
    preferences = database.get_user_preferences()
    search_start = parse_datetime(earliest_start)
    search_end = parse_datetime(deadline)
    
    // Parse preferred time window (optional)
    IF preferred_time provided:
        pref_start, pref_end = parse_preferred_time(preferred_time)
    
    // Progressive fallback strategy
    best_slot = NULL
    
    // PHASE 1: Try preferred time window first
    IF preferred_time provided:
        best_slot = find_slot_in_window(search_start, search_end, duration, pref_start, pref_end)
    
    // PHASE 2: Expand to ±1 hour around preferred time
    IF best_slot is NULL AND preferred_time provided:
        expanded_start = pref_start - 1 hour
        expanded_end = pref_end + 1 hour
        best_slot = find_slot_in_window(search_start, search_end, duration, expanded_start, expanded_end)
    
    // PHASE 3: Try work hours
    IF best_slot is NULL:
        best_slot = find_slot_in_work_hours(search_start, search_end, duration, preferences)
    
    // PHASE 4: Try any available slot (full day)
    IF best_slot is NULL:
        best_slot = find_any_available_slot(search_start, search_end, duration)
    
    IF best_slot is NULL:
        RETURN error("No available time slot found before deadline")
    
    // Create and save event
    event = {
        type: "floating",
        title: title,
        start_time: best_slot.start,
        end_time: best_slot.end,
        category: category,
        priority: priority
    }
    
    event_id = database.insert_event(event)
    RETURN event_id
END FUNCTION
```

---

## Health Score Calculation

### Overall Health Score Algorithm
```
FUNCTION calculate_health_score(events, preferences):
    // Health score measures work-life balance and well-being (0-100)
    // Based on 5 research-backed metrics
    
    // Handle empty schedule edge case
    IF events is empty:
        RETURN {
            score: 0,
            issues: ["No events scheduled"],
            suggestions: ["Start by scheduling work hours", "Add recreational activities"]
        }
    
    // Categorize events
    work_events = filter_by_category(events, "Work")
    meetings = filter_by_category(events, "Meeting")
    recreational = filter_by_category(events, "Recreational")
    meals = filter_by_category(events, "Meal")
    
    // Calculate 5 metrics
    work_life_score = calculate_work_life_balance(work_events, meetings)
    sleep_score = calculate_sleep_respect(events, preferences)
    focus_score = calculate_focus_blocks(work_events, meetings)
    meeting_score = calculate_meeting_load(meetings, work_events)
    recovery_score = calculate_recovery_time(recreational, meals)
    
    // Weighted composite score
    weights = {
        work_life: 0.25,
        sleep: 0.20,
        focus: 0.20,
        meetings: 0.15,
        recovery: 0.20
    }
    
    composite_score = (
        work_life_score * weights.work_life +
        sleep_score * weights.sleep +
        focus_score * weights.focus +
        meeting_score * weights.meetings +
        recovery_score * weights.recovery
    )
    
    // Generate actionable insights
    issues = identify_health_issues(work_life_score, sleep_score, focus_score, meeting_score, recovery_score)
    suggestions = generate_health_suggestions(issues)
    
    RETURN {
        score: round(composite_score),
        breakdown: {
            work_life: work_life_score,
            sleep_respect: sleep_score,
            focus_blocks: focus_score,
            meetings: meeting_score,
            recovery: recovery_score
        },
        issues: issues,
        suggestions: suggestions
    }
END FUNCTION
```

### Work-Life Balance Metric
```
FUNCTION calculate_work_life_balance(work_events, meetings):
    // Measures if work hours are reasonable and balanced
    
    all_work = combine(work_events, meetings)
    total_work_hours = sum_duration(all_work) / 60.0
    
    // Count long days (>10 hours)
    long_days = count_days_with_duration(all_work, > 10 hours)
    
    // Count weekend/evening work
    weekend_hours = count_weekend_work_hours(all_work)
    
    // Scoring logic based on research
    // Optimal: 35-45 hours/week, no long days, minimal weekend work
    score = 100
    
    IF total_work_hours > 50:
        score -= 30  // Significant overwork
    ELSE IF total_work_hours > 45:
        score -= 15  // Moderate overwork
    
    IF total_work_hours < 20 AND has_personal_events():
        score = 100  // Good work-life balance (vacation/sabbatical)
    ELSE IF total_work_hours < 20:
        score -= 20  // Underutilization
    
    score -= (long_days * 10)  // Penalty for each long day
    score -= (weekend_hours * 2)  // Penalty for weekend work
    
    RETURN max(0, min(100, score))
END FUNCTION
```

### Sleep Respect Metric
```
FUNCTION calculate_sleep_respect(events, preferences):
    // Measures how well the schedule respects sleep hours
    
    sleep_start = parse_time(preferences.sleep_start)
    sleep_end = parse_time(preferences.sleep_end)
    
    intrusion_hours = 0
    intrusion_count = 0
    
    FOR EACH event IN events:
        event_start_time = get_time_component(event.start_time)
        event_end_time = get_time_component(event.end_time)
        
        // Check if event overlaps with sleep hours
        IF overlaps_with_sleep(event_start_time, event_end_time, sleep_start, sleep_end):
            intrusion_count += 1
            intrusion_duration = calculate_overlap_duration(event, sleep_start, sleep_end)
            intrusion_hours += intrusion_duration / 60.0
    
    // Scoring: any sleep intrusion is bad
    score = 100
    
    IF intrusion_count > 0:
        score = max(0, 100 - (intrusion_count * 20) - (intrusion_hours * 5))
    
    RETURN score
END FUNCTION
```

### Focus Blocks Metric
```
FUNCTION calculate_focus_blocks(work_events, meetings):
    // Measures availability of uninterrupted deep work time
    // Deep work requires 90+ minute blocks
    
    DEEP_WORK_THRESHOLD = 90  // minutes
    
    focus_blocks = []
    
    // Combine work events to find continuous work periods
    sorted_events = sort_by_start_time(work_events)
    
    current_block = NULL
    
    FOR EACH event IN sorted_events:
        IF current_block is NULL:
            current_block = {start: event.start_time, end: event.end_time}
        ELSE:
            gap = minutes_between(current_block.end, event.start_time)
            
            IF gap <= 15:  // Less than 15 min gap = continuous block
                current_block.end = event.end_time
            ELSE:
                // Block ended, check if it was deep work
                block_duration = minutes_between(current_block.start, current_block.end)
                IF block_duration >= DEEP_WORK_THRESHOLD:
                    focus_blocks.append(current_block)
                
                // Start new block
                current_block = {start: event.start_time, end: event.end_time}
    
    // Check final block
    IF current_block:
        block_duration = minutes_between(current_block.start, current_block.end)
        IF block_duration >= DEEP_WORK_THRESHOLD:
            focus_blocks.append(current_block)
    
    // Count interruptions by meetings
    interrupted_blocks = 0
    FOR EACH block IN focus_blocks:
        FOR EACH meeting IN meetings:
            IF meeting overlaps with block:
                interrupted_blocks += 1
                BREAK
    
    // Scoring
    total_focus_hours = sum_duration(focus_blocks) / 60.0
    focus_block_count = length(focus_blocks)
    
    score = min(100, (focus_block_count * 15) + (total_focus_hours * 5))
    score -= (interrupted_blocks * 10)  // Penalty for interrupted focus
    
    RETURN max(0, score)
END FUNCTION
```

---

## Productivity Score Calculation

### Overall Productivity Score Algorithm
```
FUNCTION calculate_productivity_score(events, preferences):
    // Productivity score measures time allocation efficiency (0-100)
    // NOT "more work = better" but "smarter allocation = better"
    
    // Handle empty schedule
    IF events is empty:
        RETURN {
            score: 0,
            inefficiencies: ["No events scheduled"],
            optimizations: ["Schedule deep work blocks", "Add recovery time"]
        }
    
    // Calculate 5 efficiency metrics
    block_score = calculate_block_structure(events)
    fragmentation_score = calculate_fragmentation(events)
    balance_score = calculate_schedule_balance(events, preferences)
    meeting_efficiency_score = calculate_meeting_efficiency(events)
    recovery_score = calculate_recovery_support(events)
    
    // Weighted composite
    weights = {
        block_structure: 0.35,      // Time chunking efficiency
        fragmentation: 0.15,        // Context switching cost
        schedule_balance: 0.20,     // Utilization + buffer
        meeting_efficiency: 0.20,   // Meeting-to-work flow
        recovery_support: 0.10      // Sustainability
    }
    
    composite_score = (
        block_score * weights.block_structure +
        fragmentation_score * weights.fragmentation +
        balance_score * weights.schedule_balance +
        meeting_efficiency_score * weights.meeting_efficiency +
        recovery_score * weights.recovery_support
    )
    
    // Generate insights
    inefficiencies = identify_inefficiencies(block_score, fragmentation_score, balance_score, meeting_efficiency_score, recovery_score)
    optimizations = generate_optimization_suggestions(inefficiencies)
    
    RETURN {
        score: round(composite_score),
        breakdown: {
            block_structure: block_score,
            fragmentation: fragmentation_score,
            schedule_balance: balance_score,
            meeting_efficiency: meeting_efficiency_score,
            recovery_support: recovery_score
        },
        inefficiencies: inefficiencies,
        optimizations: optimizations
    }
END FUNCTION
```

### Block Structure Metric
```
FUNCTION calculate_block_structure(events):
    // Measures time chunking efficiency (deep work blocks)
    // Research: 90+ minute blocks enable flow state
    
    DEEP_WORK_THRESHOLD = 90  // minutes
    
    work_events = filter_by_category(events, "Work")
    
    IF work_events is empty:
        RETURN 0
    
    deep_blocks = []
    deep_work_hours = 0
    
    FOR EACH event IN work_events:
        duration = minutes_between(event.start_time, event.end_time)
        
        IF duration >= DEEP_WORK_THRESHOLD:
            deep_blocks.append(event)
            deep_work_hours += duration / 60.0
    
    // Scoring: reward deep blocks
    score = min(100, (length(deep_blocks) * 20) + (deep_work_hours * 3))
    
    // Bonus for consistent daily deep work
    days_with_deep_work = count_unique_days(deep_blocks)
    IF days_with_deep_work >= 5:
        score += 15
    
    RETURN max(0, min(100, score))
END FUNCTION
```

### Fragmentation Metric
```
FUNCTION calculate_fragmentation(events):
    // Measures context switching cost and schedule fragmentation
    // Research: 15-20 min lost per context switch
    
    TRANSITION_COST = 15  // minutes per switch
    
    sorted_events = sort_by_start_time(events)
    
    total_transitions = 0
    weighted_transitions = 0
    short_gaps = 0  // Gaps < 30 min (not enough to do anything useful)
    
    FOR i = 0 TO length(sorted_events) - 2:
        current = sorted_events[i]
        next = sorted_events[i + 1]
        
        gap = minutes_between(current.end_time, next.start_time)
        
        // Count transition
        total_transitions += 1
        
        // Weight transition by category switch severity
        IF current.category != next.category:
            weighted_transitions += 2  // External switch (high cost)
        ELSE:
            weighted_transitions += 1  // Internal switch (lower cost)
        
        // Count short gaps (wasted time)
        IF gap > 0 AND gap < 30:
            short_gaps += 1
    
    // Calculate wasted time from transitions
    wasted_hours = (weighted_transitions * TRANSITION_COST) / 60.0
    
    // Scoring: penalize excessive fragmentation
    score = 100
    score -= (weighted_transitions * 3)
    score -= (short_gaps * 5)
    score -= (wasted_hours * 2)
    
    RETURN max(0, score)
END FUNCTION
```

---

## Schedule Balancing & Optimization

### Smart Weekly Balancing Algorithm
```
FUNCTION smart_optimize_week(events, preferences):
    // WORKLOAD BALANCING: Distribute events evenly across week by duration
    // Prevents asymmetric schedules (e.g., 8h Mon, 2h Tue)
    
    // Separate locked vs moveable events
    locked_events = filter_events(events, WHERE locked = true OR in_past = true)
    moveable_events = filter_events(events, WHERE locked = false AND in_past = false)
    
    IF moveable_events is empty:
        RETURN {modifications: [], message: "No moveable events"}
    
    // Get week range
    week_days = [Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]
    
    // Initialize simulation with locked events
    simulated_schedule = copy(locked_events)
    
    // Sort moveable events by priority
    sorted_events = sort_by_priority(moveable_events)
    // Priority order: high → medium → low
    // Type order: fixed → recurring → floating
    // Category order: Work → Meeting → Recreational → Meal → Personal
    
    modifications = []
    
    FOR EACH event IN sorted_events:
        original_start = event.start_time
        original_duration = duration_of(event)
        
        // CRITICAL: Calculate TOTAL DURATION on each day (workload balancing key)
        daily_durations = {}
        FOR EACH day IN week_days:
            daily_durations[day] = 0
        
        FOR EACH sim_event IN simulated_schedule:
            event_day = get_day_of_week(sim_event.start_time)
            event_duration = duration_minutes(sim_event)
            daily_durations[event_day] += event_duration
        
        // Choose day with LEAST total duration (workload balancing guarantee)
        best_day = min(week_days, KEY: daily_durations[day])
        
        // Find best time slot on that day using multi-criteria scoring
        best_slot = find_best_slot_on_day(
            day: best_day,
            duration: original_duration,
            event: event,
            simulated_schedule: simulated_schedule,
            preferences: preferences
        )
        
        IF best_slot found:
            // Update event in simulation
            event.start_time = best_slot.start
            event.end_time = best_slot.end
            simulated_schedule.append(event)
            
            // Track modification
            IF best_slot.start != original_start:
                modifications.append({
                    event_id: event.id,
                    old_start: original_start,
                    new_start: best_slot.start,
                    reason: "Workload balancing"
                })
        ELSE:
            RETURN error("Could not find slot for event: " + event.title)
    
    RETURN {
        modifications: modifications,
        simulated_schedule: simulated_schedule,
        message: "Schedule balanced across week"
    }
END FUNCTION
```

### Find Best Slot with Progressive Fallback
```
FUNCTION find_best_slot_on_day(day, duration, event, simulated_schedule, preferences):
    // Progressive fallback with multi-criteria scoring
    
    // Phase 1: Try preferred time window
    IF event has preferred_time:
        pref_start, pref_end = parse_preferred_time(event.preferred_time)
        slot = find_slot_in_window(day, duration, pref_start, pref_end, simulated_schedule)
        IF slot found:
            RETURN slot
    
    // Phase 2: Expand to ±1 hour around preferred time
    IF event has preferred_time:
        expanded_start = pref_start - 1 hour
        expanded_end = pref_end + 1 hour
        slot = find_slot_in_window(day, duration, expanded_start, expanded_end, simulated_schedule)
        IF slot found:
            RETURN slot
    
    // Phase 3: Try work hours
    work_start = parse_time(preferences.work_start)
    work_end = parse_time(preferences.work_end)
    slot = find_slot_in_window(day, duration, work_start, work_end, simulated_schedule)
    IF slot found:
        RETURN slot
    
    // Phase 4: Try any available slot (full day)
    slot = find_any_slot(day, duration, simulated_schedule)
    IF slot found:
        RETURN slot
    
    RETURN NULL
END FUNCTION
```

### Multi-Criteria Slot Scoring
```
FUNCTION score_slot(slot_start, slot_end, event, preferences):
    // Score potential time slots using multiple criteria
    
    score = 0
    
    // Criterion 1: Preferred time match (0-40 points)
    IF event has preferred_time:
        pref_start, pref_end = parse_preferred_time(event.preferred_time)
        IF slot within preferred window:
            score += 40
        ELSE IF slot within ±1 hour of preferred window:
            score += 20
    
    // Criterion 2: Work hours alignment (0-30 points)
    work_start = parse_time(preferences.work_start)
    work_end = parse_time(preferences.work_end)
    
    IF event.category in ["Work", "Meeting"]:
        IF slot within work hours:
            score += 30
        ELSE:
            score -= 20  // Penalty for work outside work hours
    
    // Criterion 3: Spacing from other events (0-20 points)
    gap_before = minutes_to_previous_event(slot_start)
    gap_after = minutes_to_next_event(slot_end)
    
    IF gap_before > 15 AND gap_after > 15:
        score += 20  // Good spacing
    ELSE IF gap_before < 5 OR gap_after < 5:
        score -= 10  // Too cramped
    
    // Criterion 4: Category fit (0-10 points)
    IF event.category = "Meal":
        meal_times = ["07:00-09:00", "12:00-13:00", "18:00-20:00"]
        IF slot overlaps with meal_times:
            score += 10
    
    IF event.category = "Recreational":
        IF slot on weekend OR after work hours:
            score += 10
    
    RETURN score
END FUNCTION
```

---

## Event Validation

### Comprehensive Event Validation
```
FUNCTION validate_event(event, existing_events, preferences, event_id = NULL):
    // Real-time validation with errors, warnings, and suggestions
    
    errors = []
    warnings = []
    suggestions = []
    
    // Parse times
    TRY:
        start = parse_datetime(event.start)
        end = parse_datetime(event.end)
    CATCH:
        RETURN {
            valid: false,
            errors: ["Invalid time format"],
            warnings: [],
            suggestions: []
        }
    
    // Basic validation
    IF end <= start:
        errors.append("End time must be after start time")
    
    duration_minutes = (end - start) / 60
    
    IF duration_minutes < 5:
        warnings.append("Event is very short (" + duration_minutes + " min)")
    
    IF duration_minutes > 480:  // 8 hours
        warnings.append("Event is very long (" + (duration_minutes / 60) + " hours). Consider breaking it up.")
    
    // Check overlaps
    overlaps = check_overlaps(start, end, existing_events, exclude_id = event_id)
    IF overlaps exist:
        FOR EACH overlap IN overlaps:
            errors.append("Conflicts with: " + overlap.title)
    
    // Check sleep intrusion
    IF overlaps_with_sleep(start, end, preferences):
        warnings.append("⚠️ Event scheduled during sleep hours (" + preferences.sleep_start + " - " + preferences.sleep_end + ")")
        suggestions.append("💡 Consider rescheduling to respect sleep schedule")
    
    // Check work hours
    IF event.category in ["Work", "Meeting"]:
        IF NOT within_work_hours(start, end, preferences):
            warnings.append("Work event scheduled outside work hours")
    
    // Check daily work load
    daily_work_hours = calculate_daily_work_hours(start.date, existing_events)
    event_hours = duration_minutes / 60
    
    IF (daily_work_hours + event_hours) > 10:
        warnings.append("⚠️ This will exceed 10 work hours for the day")
        suggestions.append("💡 Consider moving to a lighter day")
    
    // Check back-to-back meetings
    IF event.category = "Meeting":
        IF has_adjacent_meeting(start, end, existing_events):
            warnings.append("⚠️ Back-to-back meetings detected")
            suggestions.append("💡 Add 15-minute buffer between meetings")
    
    // Check minimum break interval
    last_event = get_last_event_before(start, existing_events)
    IF last_event exists:
        gap = minutes_between(last_event.end, start)
        IF gap < preferences.min_break_interval:
            warnings.append("Less than 2 hours since last event")
            suggestions.append("Consider scheduling a break")
    
    // Determine validity
    valid = (length(errors) = 0)
    
    RETURN {
        valid: valid,
        errors: errors,
        warnings: warnings,
        suggestions: suggestions
    }
END FUNCTION
```

---

## Recurring Event Handling

### Expand Recurring Series
```
FUNCTION expand_recurring_series(recurring_event, weeks = 4):
    // Generate individual instances from recurring event template
    
    instances = []
    
    frequency = recurring_event.frequency  // "daily", "weekly", "weekdays", etc.
    start_date = recurring_event.start_date
    duration = recurring_event.duration
    preferred_time = recurring_event.preferred_time
    
    current_date = start_date
    end_date = start_date + (weeks * 7) days
    
    WHILE current_date <= end_date:
        // Check if this date matches frequency pattern
        IF matches_frequency(current_date, frequency):
            
            // Parse preferred time for this instance
            pref_start, pref_end = parse_preferred_time(preferred_time)
            
            // Create datetime by combining date and preferred start time
            instance_start = combine(current_date, pref_start)
            instance_end = instance_start + duration
            
            // Check for conflicts
            conflicts = check_conflicts(instance_start, instance_end)
            
            IF no conflicts:
                // Create instance
                instance = {
                    type: "recurring",
                    title: recurring_event.title,
                    start_time: instance_start,
                    end_time: instance_end,
                    category: recurring_event.category,
                    priority: recurring_event.priority,
                    parent_series_id: recurring_event.series_id,
                    recurrence_date: current_date
                }
                instances.append(instance)
            ELSE:
                // Try to reschedule within same day
                alternative = find_alternative_slot_on_day(current_date, duration, pref_start, pref_end)
                IF alternative found:
                    instance = create_instance_at_slot(alternative, recurring_event)
                    instances.append(instance)
                ELSE:
                    LOG("Could not schedule recurring instance on " + current_date)
        
        // Move to next date based on frequency
        current_date = next_frequency_date(current_date, frequency)
    
    RETURN instances
END FUNCTION
```

### Frequency Matching Logic
```
FUNCTION matches_frequency(date, frequency):
    // Determine if a date matches the recurring frequency pattern
    
    day_of_week = get_day_of_week(date)  // Monday = 0, Sunday = 6
    
    SWITCH frequency:
        CASE "daily":
            RETURN true
        
        CASE "weekdays":
            RETURN day_of_week IN [0, 1, 2, 3, 4]  // Monday-Friday
        
        CASE "weekly":
            // Recurs on same day each week
            RETURN true  // (called once per week on specific day)
        
        CASE "biweekly":
            week_number = get_week_number(date)
            RETURN (week_number % 2 = 0)
        
        CASE "monthly":
            day_of_month = get_day_of_month(date)
            RETURN (day_of_month = 1)  // First of month
        
        DEFAULT:
            RETURN false
    
END FUNCTION
```

---

## Helper Functions

### Time Parsing & Validation
```
FUNCTION parse_datetime(datetime_string):
    // Parse ISO 8601 datetime string
    // Formats: "2024-10-25T14:30:00", "2024-10-25T14:30:00Z"
    
    // Remove UTC 'Z' suffix
    IF datetime_string ends with 'Z':
        datetime_string = datetime_string[0:-1]
    
    // Remove fractional seconds
    IF '.' in datetime_string:
        datetime_string = split(datetime_string, '.')[0]
    
    // Parse with full format (seconds)
    TRY:
        RETURN parse(datetime_string, format: "YYYY-MM-DDTHH:MM:SS")
    CATCH:
        // Try without seconds
        TRY:
            RETURN parse(datetime_string, format: "YYYY-MM-DDTHH:MM")
        CATCH:
            THROW error("Invalid datetime format: " + datetime_string)
END FUNCTION
```

### Round to Time Interval
```
FUNCTION round_to_interval(datetime, interval_minutes):
    // Round datetime to nearest interval (5, 10, 15, or 30 minutes)
    
    minute = datetime.minute
    remainder = minute % interval_minutes
    
    IF remainder = 0:
        RETURN datetime  // Already aligned
    
    // Round up to next interval
    rounded_minute = ((minute / interval_minutes) + 1) * interval_minutes
    
    IF rounded_minute >= 60:
        // Overflow to next hour
        RETURN datetime + 1 hour - datetime.minute minutes + (rounded_minute - 60) minutes
    ELSE:
        RETURN datetime - datetime.minute minutes + rounded_minute minutes
END FUNCTION
```

### Sleep Hours Check
```
FUNCTION is_during_sleep(datetime, preferences):
    // Check if datetime falls during user's sleep hours
    
    sleep_start = parse_time(preferences.sleep_start)  // e.g., "23:00"
    sleep_end = parse_time(preferences.sleep_end)      // e.g., "07:00"
    
    time_component = get_time(datetime)
    
    // Handle overnight sleep (e.g., 23:00 - 07:00)
    IF sleep_start > sleep_end:
        RETURN (time_component >= sleep_start) OR (time_component < sleep_end)
    ELSE:
        // Same-day sleep (e.g., 01:00 - 08:00)
        RETURN (sleep_start <= time_component) AND (time_component < sleep_end)
END FUNCTION
```

---

## Summary

This pseudocode documentation covers the main algorithmic functions in Tempora:

1. **Event Creation**: Three types (fixed, recurring, floating) with different scheduling strategies
2. **Health Score**: 5-metric system measuring work-life balance and well-being
3. **Productivity Score**: 5-metric system measuring time allocation efficiency
4. **Schedule Balancing**: Workload distribution using progressive fallback and multi-criteria scoring
5. **Event Validation**: Comprehensive real-time validation with errors, warnings, and suggestions
6. **Recurring Events**: Series expansion with frequency pattern matching

All algorithms are designed to be:
- **User-centric**: Respect user preferences and constraints
- **Research-backed**: Based on peer-reviewed studies
- **Fault-tolerant**: Handle edge cases and empty schedules
- **Actionable**: Provide specific suggestions for improvement
