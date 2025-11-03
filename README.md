# 🎯 TEMPORA - Intelligent Calendar System

> **Smart scheduling with evidence-based health and productivity insights.**

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)]()
[![Version](https://img.shields.io/badge/version-1.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![React](https://img.shields.io/badge/react-19%2B-61dafb)]()

---

## 📖 What is TEMPORA?

TEMPORA is an intelligent calendar optimization system that helps you improve your schedule health and productivity through evidence-based metrics and actionable recommendations. Unlike traditional calendars that just display events, TEMPORA:

- 💚 **Measures schedule health** - Sleep respect, work-life balance, recovery time
- ⚡ **Calculates productivity** - Deep work blocks, meeting efficiency, context switching
- 🎯 **Provides recommendations** - Step-by-step guidance based on 20+ research studies
- 📊 **Tracks progress** - Weekly analytics and historical trends
- 🎨 **Modern interface** - Beautiful dark theme with intuitive design

---

## 📚 Documentation

### Essential Documentation
- 📐 **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture diagrams, component breakdown, technology stack
- 🔧 **[PSEUDOCODE.md](PSEUDOCODE.md)** - Detailed pseudocode for all main functions (event handling, scoring, optimization)
- 📊 **[DATA_FLOW.md](DATA_FLOW.md)** - Complete data flow diagrams showing UI interactions and backend processing
- ✅ **[REQUIREMENTS.md](REQUIREMENTS.md)** - Comprehensive list of functional and non-functional requirements met (98% coverage)

---

## ✨ Key Features

### 📌 Three Event Types

| Type | Description | Auto-Scheduled | Example |
|------|-------------|----------------|---------|
| **Fixed** | Time-specific appointments | ❌ | "Team meeting Tuesday 2-3pm" |
| **Recurring** | Repeating habits/tasks | ✅ | "Gym every 2 days, prefer mornings" |
| **Floating** | Flexible tasks with deadlines | ✅ | "Study 3 hours before Friday exam" |

### 🎯 Smart Scheduling

- **Conflict Prevention** - Automatic overlap detection
- **Break Scheduling** - Auto-inserts breaks after long work/meetings (≥45min → 15min break)
- **Sleep & Work Hours** - Respects your schedule preferences
- **Time Rounding** - Clean intervals (5/10/15/30 minutes)
- **Preferred Windows** - Optional time ranges for tasks
- **Priority System** - High/Medium/Low importance

### 📊 Evidence-Based Scoring

- **Health Score** - Schedule sustainability (sleep respect, work-life balance, recovery time)
- **Productivity Score** - Time efficiency (deep work blocks, meeting load, fragmentation)
- **Actionable Insights** - One-click optimizations with before/after preview

### 🔄 Schedule Optimization

5-phase algorithm that intelligently reorganizes your calendar:
1. **Classification** - Sort events by flexibility
2. **Anchor Placement** - Minimize movement of important events
3. **Intelligence Scoring** - Rank by priority & urgency
4. **Optimal Slot Finding** - Respect all constraints
5. **Atomic Update** - Apply changes in single transaction

### 🎨 Modern UI

- **FullCalendar Integration** - Interactive weekly/monthly views
- **Category Icons** - 💼 Work, 👥 Meeting, 👤 Personal, 🎮 Recreational, 🍽️ Meal
- **Visual Indicators** - Color-coded by priority, outlined when locked
- **Context Menus** - Right-click for quick actions
- **Responsive Design** - Clean, professional interface

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenWeatherMap API key (free at https://openweathermap.org/api)

### Installation

**Windows (Automated):**
```powershell
# Step 1: Configure Environment
cd frontend
copy .env.example .env
# Edit .env and add your OpenWeatherMap API key

# Step 2: Start Backend
.\setup_backend.bat

# Step 3: Start Frontend
.\setup_frontend.bat

# Open http://localhost:5173
```

**Manual Setup:**

**Backend:**
```powershell
cd backend
pip install -r requirements.txt
python -c "from database import db; db.init_db()"
python app.py
# Running on http://localhost:5000
```

**Frontend:**
```powershell
cd frontend
# Copy and configure environment variables
copy .env.example .env
# Edit .env and add your OpenWeatherMap API key

npm install
npm run dev
# Running on http://localhost:5173
```

---

## 💡 Usage Examples

### Create a Fixed Event
```
1. Click "Fixed Event"
2. Title: "Team Meeting"
3. Start: 2025-10-13 14:00
4. End: 2025-10-13 15:00
5. Priority: High, Category: Meeting
6. Submit
```

### Create a Recurring Task
```
1. Click "Recurring Event"
2. Title: "Gym Workout"
3. Duration: 60 minutes
4. Frequency: Every 2 days
5. ☑️ Preferred Time: 09:00 - 11:00
6. Submit

→ Automatically schedules instances for next 30 days!
```

### Create a Floating Task
```
1. Click "Floating Event"
2. Title: "Study for Exam"
3. Duration: 180 minutes
4. Earliest Start: 2025-10-13 08:00
5. Deadline: 2025-10-15 18:00
6. ☑️ Preferred Time: 14:00 - 17:00
7. Submit

→ System finds optimal 3-hour slot before deadline!
```

### Optimize Your Schedule
```
1. Click "♻️ Optimize Schedule"
2. Start: Monday 00:00
3. End: Friday 23:59
4. Review proposed changes in preview modal
5. Confirm to apply

→ Events intelligently rearranged!
```

---

## 🏗️ Technical Stack

### Backend
- **Framework:** Flask 3.x (Python)
- **Database:** SQLite3 with optimized indexes
- **API:** RESTful with CORS support (ports 5173/5174)
- **Port:** 5000

### Frontend
- **Framework:** React 19 with hooks
- **Calendar:** FullCalendar 6.x
- **HTTP:** Axios
- **Build:** Vite 7.x
- **Port:** 5173/5174

### Features
- 7 API endpoints
- 2 database tables with foreign keys
- 3 event types, 5 categories
- Real-time validation
- Preview before optimization

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System design, data flow, component structure |
| **[DOCUMENTATION.md](DOCUMENTATION.md)** | Complete API reference, algorithms, troubleshooting |



## 🔐 Security & Limitations

### Current Status (Single-User Development)
- ✅ SQL injection protection (parameterized queries)
- ✅ Input validation (client & server)
- ✅ Foreign key constraints
- ⚠️ No authentication (single-user system)
- ⚠️ HTTP only (localhost)

### Known Limitations
1. **Single-User** - No authentication or multi-user support
2. **30-Day Recurring Window** - Instances generated 30 days ahead
3. **7-Day Optimization Limit** - Maximum range for optimizer
4. **No Undo** - Event changes are permanent

---

## 🚦 Future Roadmap

### Production Deployment
- [ ] **User authentication & authorization** (JWT/OAuth)
- [ ] **Multi-user support** with device sync
- [ ] **HTTPS deployment** with SSL certificates
- [ ] **API security** (rate limiting, CSRF protection)
- [ ] **PostgreSQL database** for production scale

### Algorithm Enhancements
- [ ] **Optimize scheduling algorithms** for better performance
- [ ] **Enhanced scoring systems** with more metrics
- [ ] **Machine learning** for personalized recommendations

### User Testing & Validation
- [ ] **Extensive user testing** with real users
- [ ] **Feedback integration** and UX improvements
- [ ] **Performance benchmarking** across different scenarios

---

## 📈 Version History

### October 2025 - JuFo Prototype
First prototype developed for "Jugend forscht" competition:
- ❌ No database or data persistence
- ❌ Poor event architecture (5 event types including separate preferred time events)
- ❌ Non-functional rescheduling
- ❌ Basic UI with no scoring or preference systems
- ✅ Core concept and initial scheduling logic

### October-November 2025 - Current Version
Complete rebuild with enhanced features:
- ✅ SQLite database with persistent storage
- ✅ Streamlined 3 event types (Fixed, Recurring, Floating)
- ✅ Functional optimization algorithm with preview
- ✅ Health & Productivity scoring systems
- ✅ Modern UI with FullCalendar integration
- ✅ User preferences and actionable recommendations
- ✅ Break scheduling and conflict prevention

---

## 📄 License & Usage

© 2025 [Your Name]. All Rights Reserved.

This project is a school assignment and is made public for portfolio purposes only.
Copying, distribution, or use of this code is not permitted without explicit permission.

---

## 👏 Acknowledgments

- **FullCalendar** - Interactive calendar component
- **Flask** - Lightweight Python web framework
- **React** - Modern UI library
- **SQLite** - Reliable embedded database

---

<div align="center">

**Made with ❤️ for smarter scheduling**

[Architecture](ARCHITECTURE.md) • [Documentation](DOCUMENTATION.md) • [Quick Start](#-quick-start)

**Status:** ✅ Production-Ready | **Version:** 2.1 | **Updated:** October 2025

</div>
