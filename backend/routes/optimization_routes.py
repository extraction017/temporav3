"""
Optimization Routes Module

Handles schedule optimization endpoints:
- POST /apply-optimization - Apply one-click optimization actions

These routes use the OptimizationEngine to improve schedules based on
health score, productivity score, and user preferences.
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from database import db
from health_score import HealthScoreCalculator
from productivity_score import ProductivityScoreCalculator
from optimizations import OptimizationEngine


def register_optimization_routes(app):
    """Register all optimization-related routes with the Flask app."""
    
    @app.route("/apply-optimization", methods=["POST"])
    def apply_optimization():
        """
        Apply one-click optimization to improve schedule.
        Available actions: consolidate_schedule, group_deep_work, add_planning_buffer,
                          reduce_meeting_load, add_recovery_time, fix_sleep_schedule
        
        Request body:
            {
                "action": "smart_optimize_week" | "consolidate_schedule" | ...,
                "week_offset": 0,  // 0 = current week, -1 = last week, etc.
                "preview": true    // Optional: true for preview mode, false to apply
            }
        
        Response:
            {
                "success": true,
                "action": "smart_optimize_week",
                "preview": false,
                "events_modified": 5,
                "score_improvement": {
                    "health": {"before": 65, "after": 78, "delta": 13},
                    "productivity": {"before": 72, "after": 81, "delta": 9}
                },
                "modifications": [...],
                "recommendations": [...],
                "message": "Applied smart_optimize_week optimization"
            }
        """
        try:
            data = request.json
            action = data.get('action')
            week_offset = int(data.get('week_offset', 0))
            
            if not action:
                return jsonify({"error": "Missing 'action' parameter"}), 400
            
            # Calculate date range (Monday-Sunday)
            today = datetime.now().date()
            monday = today - timedelta(days=today.weekday())
            start_date = monday + timedelta(weeks=week_offset)
            end_date = start_date + timedelta(days=6)
            
            # CRITICAL: Prevent optimizing past weeks (would corrupt scoring system)
            if end_date < today:
                return jsonify({
                    "error": "Cannot optimize past weeks. This would falsely boost scores by modifying historical data.",
                    "suggestion": "Please select current or future weeks only."
                }), 400
            
            # Get current events and preferences
            events = db.get_events_in_range(
                start_date.isoformat() + "T00:00:00",
                end_date.isoformat() + "T23:59:59"
            )
            preferences = db.get_user_preferences()
            
            # Calculate before scores
            health_calc = HealthScoreCalculator(events, preferences)
            prod_calc = ProductivityScoreCalculator(events, preferences)
            before_health = health_calc.calculate_score()['score']
            before_prod = prod_calc.calculate_score()['score']
            
            # Apply optimization
            engine = OptimizationEngine(events, preferences)
            
            if action == 'smart_optimize_week':
                result = engine.smart_optimize_week()
            elif action == 'consolidate_schedule':
                result = engine.consolidate_schedule()
            elif action == 'group_deep_work':
                result = engine.group_deep_work()
            elif action == 'add_planning_buffer':
                result = engine.add_planning_buffer()
            elif action == 'reduce_meeting_load':
                result = engine.reduce_meeting_load()
            elif action == 'add_recovery_time':
                result = engine.add_recovery_time()
            elif action == 'fix_sleep_schedule':
                result = engine.fix_sleep_schedule()
            else:
                return jsonify({"error": f"Unknown action: {action}"}), 400
            
            # Check if preview mode (don't apply changes to DB)
            preview_mode = data.get('preview', False)
            
            # Apply modifications to database (if any) - skip if preview mode
            applied = 0
            deleted = 0
            if not preview_mode and 'modifications' in result and result['modifications']:
                for mod in result['modifications']:
                    # Check if this is a deletion (new_start is None)
                    if mod.get('new_start') is None:
                        if db.delete_event(mod['id']):
                            deleted += 1
                    else:
                        if db.update_event(mod['id'], {
                            'start_time': mod['new_start'],
                            'end_time': mod['new_end']
                        }):
                            applied += 1
            
            # Calculate after scores
            after_health = before_health
            after_prod = before_prod
            
            if preview_mode and result.get('modifications'):
                # Preview mode: simulate score changes without DB updates
                simulated_events = [dict(e) for e in events]
                for mod in result['modifications']:
                    for evt in simulated_events:
                        if evt['id'] == mod['id']:
                            evt['start'] = mod['new_start']
                            evt['end'] = mod['new_end']
                            break
                
                health_calc_after = HealthScoreCalculator(simulated_events, preferences)
                prod_calc_after = ProductivityScoreCalculator(simulated_events, preferences)
                after_health = health_calc_after.calculate_score()['score']
                after_prod = prod_calc_after.calculate_score()['score']
            elif applied > 0:
                # Live mode: re-fetch events to get updated times from DB
                updated_events = db.get_events_in_range(
                    start_date.isoformat() + "T00:00:00",
                    end_date.isoformat() + "T23:59:59"
                )
                health_calc_after = HealthScoreCalculator(updated_events, preferences)
                prod_calc_after = ProductivityScoreCalculator(updated_events, preferences)
                after_health = health_calc_after.calculate_score()['score']
                after_prod = prod_calc_after.calculate_score()['score']
            
            return jsonify({
                "success": True,
                "action": action,
                "preview": preview_mode,
                "events_modified": applied if not preview_mode else len(result.get('modifications', [])),
                "score_improvement": {
                    "health": {
                        "before": before_health,
                        "after": after_health,
                        "delta": after_health - before_health
                    },
                    "productivity": {
                        "before": before_prod,
                        "after": after_prod,
                        "delta": after_prod - before_prod
                    }
                },
                "modifications": result.get('modifications', []),
                "recommendations": result.get('recommendations', []),
                "message": result.get('message', 
                    f'Preview: {len(result.get("modifications", []))} changes proposed' if preview_mode 
                    else f'Applied {action} optimization')
            }), 200
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Failed to apply optimization",
                "details": str(e)
            }), 500
