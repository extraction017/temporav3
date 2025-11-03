"""
Preference Routes

HTTP endpoints for user preferences:
- GET /preferences - Get user scheduling preferences
- PUT /preferences - Update user preferences
"""

from flask import request, jsonify
from database import db


def register_preference_routes(app):
    """Register all preference-related routes with the Flask app."""
    
    @app.route("/preferences", methods=["GET"])
    def get_preferences():
        """Get user scheduling preferences."""
        prefs = db.get_user_preferences()
        return jsonify(prefs), 200

    @app.route("/preferences", methods=["PUT"])
    def update_preferences():
        """Update user scheduling preferences."""
        data = request.json
        
        # Validate round_to_minutes
        round_to = data.get('round_to_minutes', 5)
        if round_to not in [5, 10, 15, 30]:
            return jsonify({"error": "round_to_minutes must be 5, 10, 15, or 30"}), 400
        
        updated_prefs = db.update_user_preferences(data)
        return jsonify({
            "message": "Preferences updated successfully",
            "preferences": updated_prefs
        }), 200
