"""
Event Routes

HTTP endpoints for event CRUD operations:
- GET /events - Fetch all events
- POST /events - Create new event
- PUT /events/<id> - Update event
- DELETE /events/<id> - Delete event
- POST /events/<id>/lock - Toggle lock status
- POST /validate-event - Validate event without saving
"""

from flask import request, jsonify
from database import db
from event_validator import EventValidator
from utils.datetime_utils import parse_datetime
from scheduling.recurring_handler import handle_recurring_event
from scheduling.floating_handler import handle_floating_event


def register_event_routes(app):
    """Register all event-related routes with the Flask app."""
    
    @app.route("/events", methods=["GET"])
    def get_events():
        """Fetch all events (breaks are not events - just empty time)."""
        # Get real events from database, filter out any legacy Break events
        events = [e for e in db.get_all_events() if e.get('title') != 'Break']
        return jsonify(events)

    @app.route("/validate-event", methods=["POST"])
    def validate_event():
        """
        Validate an event without saving it to the database.
        Returns validation warnings and errors for proactive feedback.
        
        Request body:
            {
                "event": {
                    "title": "Team Meeting",
                    "category": "Meeting",
                    "start": "2025-10-17T14:00:00",
                    "end": "2025-10-17T15:00:00",
                    "priority": "medium"
                },
                "event_id": 123  // Optional - ID of event being edited
            }
        
        Response:
            {
                "valid": true,
                "errors": [...],
                "warnings": [...],
                "suggestions": [...]
            }
        """
        data = request.json
        event = data.get('event')
        event_id = data.get('event_id')  # None for new events, ID for edits
        
        if not event:
            return jsonify({"error": "Missing 'event' in request body"}), 400
        
        # Get current schedule and preferences
        existing_events = db.get_all_events()
        preferences = db.get_user_preferences()
        
        # Run validation
        validator = EventValidator(existing_events, preferences)
        result = validator.validate_event(event, event_id)
        
        return jsonify(result), 200

    @app.route("/events/<int:event_id>", methods=["DELETE"])
    def delete_event(event_id):
        """
        Delete an event with optional modes for recurring instances.
        Query params:
          - mode: 'this_instance' (delete only this), 'all_future' (delete this and future), or default (delete all)
          
        Note: Breaks are now virtual (calculated from gaps), so no break deletion needed.
        """
        mode = request.args.get('mode', 'default')
        
        print(f"\n=== DELETE EVENT ===")
        print(f"Event ID: {event_id}, Mode: {mode}")
        
        # Get the event to check its type
        event = db.get_event_by_id(event_id)
        if not event:
            print(f"ERROR: Event {event_id} not found in database")
            return jsonify({"error": "Event not found"}), 404
        
        print(f"Event found: {event.get('title')} (type: {event.get('type')}, parent_id: {event.get('parent_id')})")
        
        deleted_count = 0
        
        if mode == 'this_instance' and event['type'] == 'recurring_instance':
            # Delete only this specific instance
            success = db.delete_recurring_instance(event_id)
            if success:
                deleted_count = 1
        
        elif mode == 'all_future' and event['type'] == 'recurring_instance':
            # Delete this and all future instances
            print(f"  Mode: all_future, deleting future instances...")
            deleted_count = db.delete_future_recurring_instances(event_id)
            print(f"  deleted_count = {deleted_count}")
        
        else:
            # Default mode: delete the event (and all its instances if it's a parent)
            success = db.delete_event(event_id)
            if success:
                deleted_count = 1
        
        if deleted_count == 0:
            return jsonify({"error": "Event not found or could not be deleted"}), 404
        
        return jsonify({
            "message": f"Deleted {deleted_count} event(s)",
            "deleted_events": deleted_count
        }), 200

    @app.route("/events/<int:event_id>", methods=["PUT"])
    def update_event(event_id):
        """
        Update an existing event.
        Supports updating: title, priority, category, start, end, locked, notes
        """
        data = request.json
        
        # Get the existing event
        event = db.get_event_by_id(event_id)
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        # Build update dictionary with allowed fields
        updates = {}
        
        # Basic fields that can always be updated
        if "title" in data:
            updates["title"] = data["title"]
        if "priority" in data:
            if data["priority"] not in ["high", "medium", "low"]:
                return jsonify({"error": "Invalid priority value"}), 400
            updates["priority"] = data["priority"]
        if "category" in data:
            if data["category"] not in ["Work", "Meeting", "Personal", "Recreational", "Meal"]:
                return jsonify({"error": "Invalid category value"}), 400
            updates["category"] = data["category"]
        if "locked" in data:
            updates["locked"] = 1 if data["locked"] else 0
        if "notes" in data:
            # Enforce 200 character limit
            notes = data["notes"]
            if len(notes) > 200:
                return jsonify({"error": "Notes must be 200 characters or less"}), 400
            updates["notes"] = notes
        
        # Time fields - check for conflicts if changing times
        time_changed = False
        if "start" in data or "end" in data:
            time_changed = True
            # Use the API payload value if provided, otherwise fall back to the stored event fields
            new_start = data.get("start", event.get("start"))
            new_end = data.get("end", event.get("end"))

            # Validate datetime format
            try:
                parse_datetime(new_start)
                parse_datetime(new_end)
            except ValueError as e:
                return jsonify({"error": f"Invalid datetime format: {str(e)}"}), 400

            # Check for conflicts with other events (excluding this event)
            conflicts = db.check_conflicts(new_start, new_end, exclude_id=event_id)
            if conflicts:
                return jsonify({"error": "Time slot is occupied by another event"}), 409

            # Map to database column names
            updates["start_time"] = new_start
            updates["end_time"] = new_end
        
        # Update the event in database
        success = db.update_event(event_id, updates)
        
        if not success:
            return jsonify({"error": "Failed to update event"}), 500
        
        # Get updated event
        updated_event = db.get_event_by_id(event_id)
        
        return jsonify({
            "message": "Event updated successfully",
            "event": updated_event
        }), 200

    @app.route("/events/<int:event_id>/lock", methods=["POST"])
    def toggle_lock_event(event_id):
        """Toggle the locked status of an event."""
        updated_event = db.toggle_lock(event_id)
        
        if not updated_event:
            return jsonify({"error": "Event not found"}), 404
        
        return jsonify({
            "message": f"Event {'locked' if updated_event['locked'] else 'unlocked'} successfully",
            "event": updated_event
        }), 200

    @app.route("/events", methods=["POST"])
    def create_event():
        """Create a new event with conflict checking."""
        data = request.json
        event_type = data.get("type", "event")  # Default to 'event'
        
        # Validate required fields based on event type
        if not _validate_event_data(data, event_type):
            return jsonify({"error": "Missing required fields"}), 400

        new_event = {
            "title": data["title"],
            "priority": data["priority"],
            "type": event_type,
            "category": data.get("category", "Personal"),
            "locked": data.get("locked", False),
            "notes": data.get("notes", "")
        }

        if event_type == "event":
            # Validate start and end times
            try:
                start_dt = parse_datetime(data["start"])
                end_dt = parse_datetime(data["end"])
            except (ValueError, KeyError) as e:
                return jsonify({"error": f"Invalid datetime format: {str(e)}"}), 400
            
            # Validation: End must be after start
            if end_dt <= start_dt:
                return jsonify({"error": "Event end time must be after start time"}), 400
            
            # Validation: Cannot create events in the past
            from datetime import datetime
            now = datetime.now()
            if end_dt < now:
                return jsonify({"error": "Cannot create events in the past"}), 400
            
            new_event.update({
                "start": data["start"],
                "end": data["end"]
            })
            if _check_conflicts(new_event):
                return jsonify({"error": "Time slot is occupied"}), 409
            created_event = db.create_event(new_event)
            return jsonify(created_event), 201
            
        elif event_type == "recurring":
            success = handle_recurring_event(data, new_event)
            if not success:
                return jsonify({"error": "Could not schedule recurring event"}), 409
            return jsonify(new_event), 201
            
        elif event_type == "floating":
            success = handle_floating_event(data, new_event)
            if not success:
                return jsonify({"error": "Could not schedule floating event"}), 409
            return jsonify(new_event), 201
            
        return jsonify(new_event), 201


def _validate_event_data(data, event_type):
    """Validate required fields based on event type."""
    base_fields = ["title", "priority"]
    
    # Simplified type fields - only 3 event types now
    type_fields = {
        "event": ["start", "end"],
        "recurring": ["duration", "frequency", "start_date"],
        "floating": ["duration", "earliest_start", "deadline"]
    }
    
    required_fields = base_fields + type_fields.get(event_type, [])
    return all(field in data and data[field] for field in required_fields)


def _check_conflicts(new_event):
    """Check if the new event conflicts with existing events."""
    new_start = parse_datetime(new_event["start"])
    new_end = parse_datetime(new_event["end"])
    
    if not new_start or not new_end:
        return True  # Signal conflict if there's no start or end

    # Use database conflict check (much faster with indexes)
    return db.check_conflicts(new_event["start"], new_event["end"])
