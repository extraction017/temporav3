"""
Score Routes

HTTP endpoints for health and productivity scoring:
- GET /health-score - Calculate health score for a week
- GET /productivity-score - Calculate productivity score for a week
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from database import db
from health_score import HealthScoreCalculator
from productivity_score import ProductivityScoreCalculator


def register_score_routes(app):
    """Register all score-related routes with the Flask app."""
    
    @app.route("/health-score", methods=["GET"])
    def get_health_score():
        """
        Calculate health score for specified week.
        Query params:
            week_offset: 0 for current week, -1 for last week, etc. (default: 0)
        """
        try:
            week_offset = int(request.args.get('week_offset', 0))
            
            # Calculate date range (Monday-Sunday)
            today = datetime.now().date()
            monday = today - timedelta(days=today.weekday())
            start_date = monday + timedelta(weeks=week_offset)
            end_date = start_date + timedelta(days=6)  # Sunday
            
            # Get data
            events = db.get_events_in_range(
                start_date.isoformat() + "T00:00:00",
                end_date.isoformat() + "T23:59:59"
            )
            preferences = db.get_user_preferences()
            
            # Calculate health score
            calculator = HealthScoreCalculator(events, preferences)
            result = calculator.calculate_score()
            
            # Add date range and preferences to response
            result['week_start'] = start_date.isoformat()
            result['week_end'] = end_date.isoformat()
            result['preferences'] = preferences
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                "error": "Failed to calculate health score",
                "details": str(e)
            }), 500

    @app.route("/productivity-score", methods=["GET"])
    def get_productivity_score():
        """
        Calculate productivity/efficiency score for specified week.
        Query params:
            week_offset: 0 for current week, -1 for last week, etc. (default: 0)
        """
        try:
            week_offset = int(request.args.get('week_offset', 0))
            
            # Calculate date range (Monday-Sunday)
            today = datetime.now().date()
            monday = today - timedelta(days=today.weekday())
            start_date = monday + timedelta(weeks=week_offset)
            end_date = start_date + timedelta(days=6)  # Sunday
            
            # Get data
            events = db.get_events_in_range(
                start_date.isoformat() + "T00:00:00",
                end_date.isoformat() + "T23:59:59"
            )
            preferences = db.get_user_preferences()
            
            # Calculate productivity score
            calculator = ProductivityScoreCalculator(events, preferences)
            result = calculator.calculate_score()
            
            # Add date range to response
            result['week_start'] = start_date.isoformat()
            result['week_end'] = end_date.isoformat()
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                "error": "Failed to calculate productivity score",
                "details": str(e)
            }), 500
