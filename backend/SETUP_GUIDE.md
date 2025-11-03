# Backend Setup and Run Guide

## Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Windows
setup_backend.bat

# The script will:
# 1. Create/activate Python virtual environment
# 2. Install dependencies from requirements.txt
# 3. Start the Flask server (app.py)
```

### Option 2: Manual Setup
```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py
```

## Backend Structure

The backend uses a modular architecture for better maintainability:

- **`app.py`** - Main Flask application (118 lines)
- **`routes/`** - HTTP endpoint handlers (5 modules)
  - `event_routes.py` - Event CRUD operations
  - `preference_routes.py` - User preferences
  - `score_routes.py` - Health & productivity scoring
  - `statistics_routes.py` - Calendar statistics
  - `optimization_routes.py` - Schedule optimization
- **`utils/`** - Helper functions (3 modules)
  - `datetime_utils.py` - Date/time parsing
  - `time_validators.py` - Work/sleep hour validation
  - `gap_calculator.py` - Break duration calculation
- **`scheduling/`** - Event scheduling logic (4 modules)
  - `slot_finder.py` - Smart slot finding & scoring
  - `recurring_handler.py` - Recurring event scheduling
  - `floating_handler.py` - Floating event scheduling
  - `schedule_state.py` - Schedule state management

## Running the Backend

```bash
# Terminal 1 - Run backend
cd backend
venv\Scripts\activate  # Windows
python app.py

# Terminal 2 - Run frontend
cd frontend
npm run dev

# Test all features:
# ✓ Create/edit/delete events
# ✓ View health & productivity scores  
# ✓ View statistics
# ✓ Apply optimizations
# ✓ Create recurring/floating events
```

## Dependencies

Current requirements (in `requirements.txt`):
```
flask          # Web framework
flask_cors     # Cross-origin resource sharing
```

All existing dependencies work with both versions - no changes needed!

## Troubleshooting

### Import Errors
```
ModuleNotFoundError: No module named 'routes'
```
**Solution**: Make sure you're in the `backend/` directory when running:
```bash
cd backend
python app.py
```

### Flask Not Found
```
ModuleNotFoundError: No module named 'flask'
```
**Solution**: Activate virtual environment and install dependencies:
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Solution**: Stop the other Flask server or change port in code:
```python
# In app.py, line ~90:
app.run(host="0.0.0.0", port=5001, debug=True)  # Change 5000 to 5001
```

## Benefits of the Modular Architecture

The current modular structure is ideal for your W-Seminar because:
- ✨ Professional software engineering architecture
- 📖 Easier to explain and document (one module at a time)
- 🎯 Shows understanding of separation of concerns
- 🏗️ Industry-standard organization
- 🔧 Easier to maintain and extend
- 📚 Clear file structure aids in documentation
