"""
Tempora v3 - Backend Application

This is the main backend server, organized into clean modules:
- routes/ - HTTP endpoints (handle requests from frontend: events, scores, optimization)
- utils/ - Helper functions (datetime parsing, time validation, gap calculations)
- scheduling/ - Event scheduling logic (slot finding, recurring/floating event handlers)

This modular structure is much easier to understand, test, and document.

Benefits:
- Each file has single, clear purpose (single responsibility principle)
- Easier to test individual components in isolation
- Better documentation (explain one module at a time)
- Better maintainability vs monolithic file
"""

from flask import Flask, request
from flask_cors import CORS

# Import route registration functions (each registers related endpoints)
from routes.event_routes import register_event_routes
from routes.preference_routes import register_preference_routes
from routes.score_routes import register_score_routes
from routes.statistics_routes import register_statistics_routes
from routes.optimization_routes import register_optimization_routes

# Create Flask app
app = Flask(__name__)

# Configure CORS (Cross-Origin Resource Sharing)
# Allows frontend (running on port 5173/5174) to communicate with backend (port 5000)
# Without this, browsers block the connection for security reasons
CORS(app, 
     origins=["http://localhost:5173", "http://localhost:5174"], 
     supports_credentials=True, 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization"])


@app.after_request
def apply_cors_headers(response):
    """
    Ensures CORS headers are present on ALL responses (even errors).
    Flask sometimes removes CORS headers on error responses, causing frontend to fail.
    This guarantees headers are always present so frontend can read error messages.
    """
    origin = request.headers.get('Origin')
    if origin in ['http://localhost:5173', 'http://localhost:5174']:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers.setdefault('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return response


# Register routes (same pattern as original app.py)
# Each function registers related endpoints with the Flask app
register_event_routes(app)
register_preference_routes(app)
register_score_routes(app)
register_statistics_routes(app)
register_optimization_routes(app)


# Health check endpoint
@app.route("/")
def index():
    """Simple health check endpoint to verify server is running."""
    return {
        "status": "running",
        "version": "3.0.0",
        "message": "Tempora v3 Backend API",
        "endpoints": {
            "events": "/events",
            "preferences": "/preferences",
            "health_score": "/health-score",
            "productivity_score": "/productivity-score",
            "statistics": "/statistics",
            "optimization": "/apply-optimization"
        }
    }


if __name__ == "__main__":
    # Run Flask development server
    # host="0.0.0.0" allows connections from other devices on network
    # port=5000 is default Flask port
    # debug=True enables auto-reload on code changes and detailed error pages
    print("=" * 60)
    print("Tempora v3 Backend API")
    print("=" * 60)
    print("Server starting on http://localhost:5000")
    print("CORS enabled for: http://localhost:5173, http://localhost:5174")
    print()
    print("Modular Structure:")
    print("  - routes/event_routes.py - Event CRUD endpoints")
    print("  - routes/preference_routes.py - User preferences")
    print("  - routes/score_routes.py - Health & productivity scoring")
    print("  - routes/statistics_routes.py - Weekly analytics")
    print("  - routes/optimization_routes.py - Schedule optimization")
    print("  - utils/datetime_utils.py - Date/time parsing")
    print("  - utils/time_validators.py - Work/sleep hour validation")
    print("  - utils/gap_calculator.py - Break calculation")
    print("  - scheduling/slot_finder.py - Smart slot finding & scoring")
    print("  - scheduling/recurring_handler.py - Recurring event scheduling")
    print("  - scheduling/floating_handler.py - Floating event scheduling")
    print("  - scheduling/schedule_state.py - Schedule state management")
    print("=" * 60)
    print()
    
    app.run(host="0.0.0.0", port=5000, debug=True)
