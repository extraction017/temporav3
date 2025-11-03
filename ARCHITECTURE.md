# 🏗️ TEMPORA - System Architecture

**Complete System Structure** | Version 3.0

Clear breakdown of all components, data flow, and interactions.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Backend Structure](#backend-structure)
3. [Frontend Structure](#frontend-structure)
4. [Database Schema](#database-schema)
5. [Data Flow Examples](#data-flow-examples)
6. [API Endpoints](#api-endpoints)

---

## 🎯 Overview

Tempora uses a **client-server architecture**:
- **Frontend**: React app with FullCalendar (port 5173)
- **Backend**: Flask REST API (port 5000)
- **Database**: SQLite with optimized indexes

```
┌──────────────────────────────────────────────────────┐
│           FRONTEND (React/Vite)                      │
│           localhost:5173                              │
│                                                       │
│  User interacts with calendar,                       │
│  creates events, views scores                        │
└──────────────────────────────────────────────────────┘
                      │
                      │ HTTP/JSON (Axios)
                      │ CORS Enabled
                      ▼
┌──────────────────────────────────────────────────────┐
│           BACKEND (Flask/Python)                     │
│           localhost:5000                              │
│                                                       │
│  • Processes requests                                │
│  • Runs scheduling algorithms                        │
│  • Calculates health/productivity scores             │
│  • Stores/retrieves data                             │
└──────────────────────────────────────────────────────┘
                      │
                      │ SQL Queries
                      ▼
┌──────────────────────────────────────────────────────┐
│           DATABASE (SQLite3)                         │
│                                                       │
│  • events table (all scheduled events)               │
│  • user_preferences table (settings)                 │
└──────────────────────────────────────────────────────┘
```

---

## 🔧 Backend Structure

The backend is organized into **modular files** for clarity and maintainability.

### 📁 File Organization

```
backend/
├── app.py                    # Main Flask app (118 lines)
├── database.py               # SQLite interface
├── event_validator.py        # Input validation
├── health_score.py           # Health scoring engine
├── productivity_score.py     # Productivity scoring
├── optimizations.py          # Schedule optimizer
│
├── routes/                   # HTTP endpoints (5 files)
│   ├── event_routes.py       # Event CRUD
│   ├── preference_routes.py  # User settings
│   ├── score_routes.py       # Health & productivity
│   ├── statistics_routes.py  # Analytics
│   └── optimization_routes.py # Optimization
│
├── utils/                    # Helper functions (3 files)
│   ├── datetime_utils.py     # Date/time parsing
│   ├── time_validators.py    # Work/sleep validation
│   └── gap_calculator.py     # Break duration calc
│
└── scheduling/               # Scheduling logic (4 files)
    ├── slot_finder.py        # Smart slot finding
    ├── recurring_handler.py  # Recurring events
    ├── floating_handler.py   # Floating events
    └── schedule_state.py     # State management
```

### 🎯 Module Purposes

#### **app.py** - Entry Point (118 lines)
```
What it does:
• Creates Flask web server
• Registers all route modules
• Configures CORS (allows frontend to connect)
• Starts server on port 5000
```

#### **routes/** - HTTP Endpoints

**event_routes.py** - Event management
- GET /events → Fetch all events
- POST /events → Create new event (fixed/recurring/floating)
- PUT /events/\<id\> → Update event
- DELETE /events/\<id\> → Delete event (with modes for recurring)
- POST /events/\<id\>/lock → Toggle lock status
- POST /validate-event → Check event validity without saving

**preference_routes.py** - User settings
- GET /preferences → Fetch work/sleep hours, rounding preference
- PUT /preferences → Update settings

**score_routes.py** - Health & productivity metrics
- GET /health-score → Calculate work-life balance score
- GET /productivity-score → Calculate efficiency score

**statistics_routes.py** - Calendar analytics
- GET /statistics → Weekly breakdown (by category, priority, type, day)

**optimization_routes.py** - Schedule improvements
- POST /apply-optimization → Apply one-click schedule reorganization

#### **utils/** - Helper Functions

**datetime_utils.py** - Date/time conversion
```python
# Converts text timestamps into Python datetime objects
parse_datetime("2025-11-03T14:30:00") → datetime(2025, 11, 3, 14, 30)

# Converts time strings for work/sleep hours
parse_time_string("09:00") → time(9, 0)

# Rounds times to clean intervals (5/10/15/30 minutes)
round_to_interval(14:07, 15) → 14:15

# Parses time ranges, detects overnight (22:00 - 02:00)
parse_preferred_time("10:00 - 12:00") → (time(10,0), time(12,0), False)
```

**time_validators.py** - Work/sleep checking
```python
# Check if datetime falls during sleep hours
is_during_sleep(datetime(2025,11,3,2,0), prefs) → True (if sleep 23:00-07:00)

# Check if datetime falls during work hours
is_during_work_hours(datetime(2025,11,3,10,0), prefs) → True (if work 09:00-18:00)

# Move datetime to next work hour if outside
adjust_to_work_hours(datetime(2025,11,3,20,0), prefs) → datetime(2025,11,4,9,0)
```

**gap_calculator.py** - Break duration measurement
```python
# Calculate minutes between event end and next event start
# Used by health/productivity scoring (gaps during sleep don't count)
calculate_gap_duration_after_event(event, all_events, prefs) → 30 (minutes)
```

#### **scheduling/** - Event Scheduling Logic

**slot_finder.py** - Smart slot selection
```
Purpose: Find BEST available slot (not just first empty)

How it works:
1. Scans time range in 15-minute intervals
2. Collects up to 50 valid candidate slots
3. Scores each slot by quality factors:
   • Work hours fit (30 pts)
   • Event spacing (20 pts)
   • Daily workload balance (15 pts)
   • Time of day preference (10 pts)
   • Proximity to deadline (2 pts)
4. Returns highest-scoring slot

Result: Events are well-spaced and balanced, not crammed together
```

**recurring_handler.py** - Recurring event scheduling
```
Purpose: Schedule repeating events (e.g., gym every 2 days)

Strategy: 4-level progressive fallback per instance
1. Try exact preferred time (10:00-11:00) → HIGHEST PRIORITY
2. Try ±1 hour expansion (09:00-12:00)
3. Try full work hours (09:00-18:00)
4. Try entire day (00:00-23:59) → LAST RESORT

Each instance tries all 4 levels independently before giving up
```

**floating_handler.py** - Floating event scheduling
```
Purpose: Schedule flexible tasks before deadline

Optimized approach (per-day):
• Day 1: Try all 4 fallback levels
• Day 2: Try all 4 fallback levels
• Day 3: Try all 4 fallback levels
... until deadline

Usually finds slot on Day 1-3 (4-12 checks)
87% faster than old level-by-level approach
```

**schedule_state.py** - Schedule state tracking
```
Purpose: Track schedule during optimization

Manages:
• Daily workload (minutes of events per day)
• Occupied time slots
• Event distribution across days

Used by OptimizationEngine for intelligent batch scheduling
```

#### Core Modules

**database.py** - SQLite interface
- Event CRUD operations (create, read, update, delete)
- Conflict detection with SQL indexes for speed
- User preferences storage
- Recurring instance management

**event_validator.py** - Input validation
- Checks: conflicts, sleep intrusion, excessive duration
- Returns: errors (blocking), warnings (advisory), suggestions (tips)

**health_score.py** - Health scoring (0-100)
- Measures: sleep respect, work duration, recovery time, stress
- Provides: score + breakdown + recommendations

**productivity_score.py** - Productivity scoring (0-100)
- Measures: deep work blocks, meeting load, context switching
- Provides: score + breakdown + recommendations

**optimizations.py** - Schedule optimizer
- 5-phase algorithm: classify → anchor → score → find → apply
- Actions: consolidate, group work, add buffers, reduce meetings

---

## 🎨 Frontend Structure

React application using modern hooks and FullCalendar library.

### 📁 File Organization

```
frontend/src/
├── main.jsx              # App entry point
├── App.jsx               # Main shell (header, logo, clock)
├── Calendar.jsx          # Main calendar component (927 lines)
│
├── components/           # Reusable UI components
│   ├── FormField.jsx     # Input fields
│   ├── DurationInput.jsx # Hours/minutes selector
│   ├── Statistics.jsx    # Analytics display
│   ├── HealthScore.jsx   # Health metrics modal
│   ├── ProductivityScore.jsx # Productivity modal
│   ├── GuideModal.jsx    # Help documentation
│   ├── PreviewModal.jsx  # Optimization preview
│
├── styles/
│   ├── index.css         # Global styles
│   ├── App.css           # App-specific styles
│   └── Calendar.css      # Calendar styles
```

### 🎯 Component Purposes

**Calendar.jsx** - Main component (927 lines)
```
Responsibilities:
• Event management (create, read, update, delete)
• FullCalendar integration (weekly/monthly views)
• Form handling (fixed/recurring/floating events)
• Settings modal (work hours, sleep hours, rounding)
• Statistics display (weekly analytics)
• Context menu for events (edit, delete, lock)
• API communication with backend
```

**Reusable Components**

**FormField.jsx** - Standardized form inputs
- Consistent styling across all forms
- Label + input + optional error message
- Used in event forms and settings

**DurationInput.jsx** - Duration picker
- Hours and minutes selectors
- Prevents invalid values
- Used for recurring/floating event duration

**Statistics.jsx** - Analytics visualization
- Weekly breakdown charts
- Category/priority/type distribution
- Daily event counts

**HealthScore.jsx / ProductivityScore.jsx** - Score modals
- Display 0-100 scores
- Show detailed metric breakdowns
- Provide actionable recommendations

**GuideModal.jsx** - User help
- Explains event types
- Shows usage examples
- Tips and best practices

**PreviewModal.jsx** - Optimization preview
- Shows proposed changes before/after
- Estimated score improvements
- Confirmation/cancel actions

---

## 💾 Database Schema

SQLite database with 2 tables and optimized indexes.

### Table: `events`

Stores all scheduled events (fixed, recurring instances, floating).

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    type TEXT NOT NULL,           -- 'event', 'recurring_instance', 'floating'
    category TEXT,                 -- 'Work', 'Meeting', 'Personal', 'Recreational', 'Meal'
    priority TEXT,                 -- 'high', 'medium', 'low'
    start_time TEXT NOT NULL,      -- ISO format: '2025-11-03T14:00:00'
    end_time TEXT NOT NULL,        -- ISO format: '2025-11-03T15:00:00'
    locked INTEGER DEFAULT 0,      -- 0 = unlocked, 1 = locked (immovable)
    notes TEXT,                    -- User notes (max 200 chars)
    parent_id INTEGER,             -- For recurring instances: links to parent
    duration INTEGER,              -- For recurring/floating: original duration
    frequency INTEGER,             -- For recurring: repeat interval in days
    earliest_start TEXT,           -- For floating: earliest possible start
    deadline TEXT,                 -- For floating: must complete before this
    preferred_time TEXT            -- JSON: {"enabled": true, "start": "10:00", "end": "12:00"}
);

-- Performance indexes
CREATE INDEX idx_events_time ON events(start_time, end_time);
CREATE INDEX idx_events_parent ON events(parent_id);
```

### Table: `user_preferences`

Stores user settings (single row).

```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY DEFAULT 1,
    sleep_start TEXT DEFAULT '23:00',     -- Sleep start time
    sleep_end TEXT DEFAULT '07:00',       -- Wake up time
    work_start TEXT DEFAULT '09:00',      -- Work day start
    work_end TEXT DEFAULT '18:00',        -- Work day end
    round_to_minutes INTEGER DEFAULT 15   -- Time rounding (5/10/15/30)
);
```

---

## 🔄 Data Flow Examples

### Example 1: Creating a Fixed Event

```
1. USER ACTION
   User clicks "Create Fixed Event" button
   Fills form: Title, Start, End, Priority, Category
   Clicks Submit

2. FRONTEND (Calendar.jsx)
   • Validates form fields (not empty, end > start)
   • Sends POST request to backend:
     POST http://localhost:5000/events
     {
       "title": "Team Meeting",
       "type": "event",
       "start": "2025-11-03T14:00:00",
       "end": "2025-11-03T15:00:00",
       "priority": "high",
       "category": "Meeting"
     }

3. BACKEND (event_routes.py)
   • Receives request, validates JSON
   • Checks for conflicts:
     database.py → check_conflicts()
   • If no conflicts:
     database.py → create_event()
     Inserts into SQLite events table
   • Returns: {"id": 123, "title": "Team Meeting", ...}

4. FRONTEND (Calendar.jsx)
   • Receives response
   • Refreshes calendar view (re-fetches all events)
   • Event appears on calendar
```

### Example 2: Calculating Health Score

```
1. USER ACTION
   User clicks "Health Score" button

2. FRONTEND (Calendar.jsx)
   • Opens HealthScore.jsx modal
   • Sends GET request:
     GET http://localhost:5000/health-score?week_offset=0

3. BACKEND (score_routes.py)
   • Gets current week date range (Monday-Sunday)
   • Fetches events in range:
     database.py → get_events_in_range()
   • Gets user preferences:
     database.py → get_user_preferences()
   • Calculates score:
     health_score.py → HealthScoreCalculator.calculate_score()
     - Checks sleep respect (events during sleep hours?)
     - Measures work duration (excessive work hours?)
     - Evaluates recovery time (sufficient breaks?)
     - Detects stress indicators (too many meetings?)
   • Returns: {
       "score": 78,
       "breakdown": {...},
       "recommendations": [...]
     }

4. FRONTEND (HealthScore.jsx)
   • Receives score data
   • Displays:
     - Overall score (78/100)
     - Metric breakdown with bars
     - Actionable recommendations
```

### Example 3: Scheduling a Recurring Event

```
1. USER ACTION
   User clicks "Create Recurring Event"
   Fills form:
   • Title: "Gym Workout"
   • Duration: 60 minutes
   • Frequency: Every 2 days
   • Start Date: 2025-11-03
   • Preferred Time: 09:00 - 11:00
   Clicks Submit

2. FRONTEND (Calendar.jsx)
   • Sends POST request:
     POST http://localhost:5000/events
     {
       "title": "Gym Workout",
       "type": "recurring",
       "duration": 60,
       "frequency": 2,
       "start_date": "2025-11-03T00:00:00",
       "preferred_time": {
         "enabled": true,
         "start": "09:00",
         "end": "11:00"
       },
       "priority": "medium",
       "category": "Personal"
     }

3. BACKEND (event_routes.py → recurring_handler.py)
   • For each occurrence (every 2 days, 30 days ahead):
     
     Day 1 (Nov 3):
     • Try exact window: 09:00-11:00
       slot_finder.py → find_available_slot()
       Checks conflicts, finds 09:15-10:15 ✓
     • Creates instance: "Gym Workout" Nov 3, 09:15-10:15
     
     Day 3 (Nov 5):
     • Try exact window: 09:00-11:00 (full)
     • Try ±1 hour: 08:00-12:00
       Finds 11:30-12:30 ✓
     • Creates instance: "Gym Workout" Nov 5, 11:30-12:30
     
     ... continues for 30 days
   
   • Returns: {
       "message": "Scheduled 15 instances",
       "fallback_stats": {
         "exact": 10,
         "expanded": 4,
         "work_hours": 1,
         "failed": 0
       }
     }

4. FRONTEND (Calendar.jsx)
   • Refreshes calendar
   • All 15 instances appear on calendar
```

---

## 🌐 API Endpoints Reference

### Event Management

**GET /events**
- Purpose: Fetch all events
- Returns: Array of event objects

**POST /events**
- Purpose: Create new event (fixed/recurring/floating)
- Body: Event data (type-specific fields)
- Returns: Created event(s)

**PUT /events/\<id\>**
- Purpose: Update existing event
- Body: Fields to update
- Returns: Updated event

**DELETE /events/\<id\>**
- Purpose: Delete event
- Query params: mode ('this_instance', 'all_future', 'default')
- Returns: Confirmation message

**POST /events/\<id\>/lock**
- Purpose: Toggle lock status (prevent moving during optimization)
- Returns: Updated event

**POST /validate-event**
- Purpose: Check event validity without saving
- Body: Event data
- Returns: {valid: bool, errors: [], warnings: [], suggestions: []}

### User Preferences

**GET /preferences**
- Purpose: Fetch user settings
- Returns: Sleep/work hours, rounding preference

**PUT /preferences**
- Purpose: Update settings
- Body: Settings to change
- Returns: Updated preferences

### Scoring

**GET /health-score**
- Purpose: Calculate schedule health
- Query params: week_offset (0=current, -1=last week)
- Returns: Score + breakdown + recommendations

**GET /productivity-score**
- Purpose: Calculate efficiency metrics
- Query params: week_offset
- Returns: Score + breakdown + recommendations

### Analytics

**GET /statistics**
- Purpose: Weekly calendar statistics
- Query params: week_offset
- Returns: Breakdown by category, priority, type, day

### Optimization

**POST /apply-optimization**
- Purpose: Apply schedule reorganization
- Body: {action: string, week_offset: number, preview: bool}
- Returns: Proposed changes + score improvements

---

## 🎓 Architecture Benefits

This modular structure provides:

1. **Clarity** - Each file has one clear purpose
2. **Maintainability** - Easy to find and fix bugs
3. **Testability** - Can test individual components
4. **Scalability** - Easy to add new features
5. **Documentation** - Code organization tells a story
6. **Education** - Perfect for W-Seminar presentation

---

*Last updated: November 3, 2025*
