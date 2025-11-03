"""
Statistics Routes

HTTP endpoints for event statistics:
- GET /statistics - Get event statistics for a week with detailed breakdowns
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from database import db
from utils.datetime_utils import parse_datetime


def register_statistics_routes(app):
    """Register all statistics-related routes with the Flask app."""
    
    @app.route("/statistics", methods=["GET"])
    def get_statistics():
        """
        Get event statistics for the current or offset week.
        
        Returns breakdown by:
        - Category (Work, Meeting, Personal, etc.)
        - Priority (high, medium, low)
        - Type (Fixed, Recurring, Floating)
        - Daily activity
        - Summary metrics (total hours, busiest day, work/break ratio)
        """
        # Get week offset from query parameter (default 0 = current week)
        week_offset = request.args.get('week_offset', 0, type=int)
        
        today = datetime.now()
        # Calculate the base date by adding/subtracting weeks
        base_date = today + timedelta(weeks=week_offset)
        week_start = base_date - timedelta(days=base_date.weekday())
        week_end = week_start + timedelta(days=7)
        all_events = db.get_all_events()
        
        # Filter events for the selected week
        week_events = []
        for event in all_events:
            if "start" not in event:
                continue
            event_start = parse_datetime(event["start"])
            if event_start and week_start <= event_start <= week_end:
                week_events.append(event)
        
        # Calculate all breakdowns
        category_durations = {}
        priority_durations = {}
        type_durations = {}
        event_durations = {}
        daily_breakdown = {}
        
        for event in week_events:
            event_start = parse_datetime(event["start"])
            event_end = parse_datetime(event["end"])
            if event_start and event_end:
                duration = (event_end - event_start).total_seconds() / 60
                
                # By event title
                title = event["title"]
                if title in event_durations:
                    event_durations[title] += duration
                else:
                    event_durations[title] = duration
                
                # By category
                category = event.get("category", "Personal")
                if category in category_durations:
                    category_durations[category] += duration
                else:
                    category_durations[category] = duration
                
                # By priority
                priority = event.get("priority", "medium")
                if priority in priority_durations:
                    priority_durations[priority] += duration
                else:
                    priority_durations[priority] = duration
                
                # By type
                event_type = event.get("type", "event")
                # Map internal types to user-friendly names
                type_label = {
                    "event": "Fixed",
                    "recurring_instance": "Recurring",
                    "floating": "Floating",
                    "break": "Break"
                }.get(event_type, "Other")
                
                if type_label in type_durations:
                    type_durations[type_label] += duration
                else:
                    type_durations[type_label] = duration
                
                # By day
                day_name = event_start.strftime("%A")  # "Monday", "Tuesday", etc.
                if day_name not in daily_breakdown:
                    daily_breakdown[day_name] = {
                        "count": 0,
                        "duration": 0,
                        "categories": {}
                    }
                daily_breakdown[day_name]["count"] += 1
                daily_breakdown[day_name]["duration"] += duration
                
                # Track category breakdown per day for stacked charts
                if category not in daily_breakdown[day_name]["categories"]:
                    daily_breakdown[day_name]["categories"][category] = 0
                daily_breakdown[day_name]["categories"][category] += duration
        
        sorted_events = sorted(
            event_durations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Calculate summary metrics
        total_events = len(week_events)
        total_minutes = sum(event_durations.values())
        total_hours = round(total_minutes / 60, 2)
        
        # Average event duration
        avg_event_duration = round(total_minutes / total_events, 1) if total_events > 0 else 0
        
        # Events per day average
        days_with_events = len(daily_breakdown)
        avg_events_per_day = round(total_events / max(days_with_events, 1), 1)
        
        # Work vs breaks (assuming Work and Meeting are "productive", Break and Meal are "rest")
        productive_categories = ["Work", "Meeting"]
        rest_categories = ["Break", "Meal"]
        
        productive_minutes = sum(
            duration for cat, duration in category_durations.items() 
            if cat in productive_categories
        )
        rest_minutes = sum(
            duration for cat, duration in category_durations.items() 
            if cat in rest_categories
        )
        
        productive_hours = round(productive_minutes / 60, 2)
        rest_hours = round(rest_minutes / 60, 2)
        
        # Find busiest and slowest days
        busiest_day_data = None
        slowest_day_data = None
        
        if daily_breakdown:
            # Find day with most events
            busiest_day = max(daily_breakdown.items(), key=lambda x: x[1]["count"])
            busiest_day_data = {
                "day": busiest_day[0],
                "event_count": busiest_day[1]["count"],
                "total_hours": round(busiest_day[1]["duration"] / 60, 2)
            }
            
            # Find day with least events
            slowest_day = min(daily_breakdown.items(), key=lambda x: x[1]["count"])
            slowest_day_data = {
                "day": slowest_day[0],
                "event_count": slowest_day[1]["count"],
                "total_hours": round(slowest_day[1]["duration"] / 60, 2)
            }
        
        # Calculate work/break ratio and balance score
        work_break_ratio = None
        if rest_minutes > 0:
            work_break_ratio = round(productive_minutes / rest_minutes, 2)
        
        # Balance score: Ideal is roughly 8:1 ratio (8 hours work, 1 hour breaks)
        # Score from 0-100, where 100 is perfect balance
        balance_score = 0
        if productive_minutes > 0:
            ideal_ratio = 8.0
            actual_ratio = work_break_ratio if work_break_ratio else 0
            
            # Calculate how far from ideal (lower is better)
            ratio_diff = abs(actual_ratio - ideal_ratio)
            
            # Convert to 0-100 score (closer to ideal = higher score)
            # Use exponential decay: score decreases as difference increases
            balance_score = round(100 * (0.9 ** ratio_diff))
            
            # Adjust for having no breaks at all (penalty)
            if rest_minutes == 0 and productive_minutes > 240:  # More than 4 hours work, no breaks
                balance_score = max(0, balance_score - 30)
        
        summary = {
            "total_events": total_events,
            "total_hours": total_hours,
            "avg_event_duration": avg_event_duration,
            "avg_events_per_day": avg_events_per_day,
            "productive_hours": productive_hours,
            "rest_hours": rest_hours,
            "busiest_day": busiest_day_data,
            "slowest_day": slowest_day_data,
            "work_break_ratio": work_break_ratio,
            "balance_score": balance_score
        }
        
        return jsonify({
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "summary": summary,
            "event_durations": dict(sorted_events),
            "category_durations": category_durations,
            "priority_durations": priority_durations,
            "type_durations": type_durations,
            "daily_breakdown": daily_breakdown
        })
