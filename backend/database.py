"""
TEMPORA Database Module - SQLite3 Implementation
Minimal MVP version with core operations only
"""

import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager

DB_FILE = "events.db"
SCHEMA_FILE = "schema.sql"


class DatabaseManager:
    """Manages SQLite database operations for Tempora event system."""
    
    def __init__(self, db_path=DB_FILE):
        """Initialize database manager with path to database file."""
        self.db_path = db_path
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database with schema from schema.sql file."""
        if not os.path.exists(SCHEMA_FILE):
            raise FileNotFoundError(f"Schema file '{SCHEMA_FILE}' not found")
        
        with open(SCHEMA_FILE, 'r') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
        
        print(f"✅ Database initialized: {self.db_path}")
    
    def get_all_events(self):
        """Retrieve all events from database as list of dictionaries."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM events ORDER BY start_time")
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def get_future_events(self, from_date=None):
        """
        Retrieve only future events (end_time >= from_date).
        Used for optimized conflict checking - past events can't conflict.
        
        Args:
            from_date: ISO format datetime string (default: now)
        
        Returns:
            List of event dictionaries with end_time >= from_date
        """
        if from_date is None:
            from_date = datetime.now().isoformat()
        
        query = """
            SELECT * FROM events 
            WHERE end_time >= ?
            ORDER BY start_time
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, (from_date,))
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def get_event_by_id(self, event_id):
        """Retrieve a single event by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    def create_event(self, event_dict):
        """
        Insert a new event into database.
        Returns the created event with its new ID.
        """
        # Extract fields from event dictionary
        fields = [
            'title', 'priority', 'type', 'category', 'start_time', 'end_time', 'locked',
            'parent_id', 'duration', 'frequency', 'earliest_start', 'deadline'
        ]
        
        # Handle preferred_time: convert dict to JSON string if present
        preferred_time = event_dict.get('preferred_time')
        if preferred_time and isinstance(preferred_time, dict):
            preferred_time = json.dumps(preferred_time)
        
        # Build SQL INSERT query
        query = """
            INSERT INTO events (
                title, priority, type, category, start_time, end_time, locked,
                parent_id, duration, frequency, earliest_start, deadline, preferred_time, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Map field names: start/end → start_time/end_time for database
        values = (
            event_dict.get('title'),
            event_dict.get('priority'),
            event_dict.get('type'),
            event_dict.get('category', 'Personal'),  # Default to Personal if not specified
            event_dict.get('start'),  # Maps to start_time in DB
            event_dict.get('end'),    # Maps to end_time in DB
            1 if event_dict.get('locked', False) else 0,
            event_dict.get('parent_id'),
            event_dict.get('duration'),
            event_dict.get('frequency'),
            event_dict.get('earliest_start'),
            event_dict.get('deadline'),
            preferred_time,
            event_dict.get('notes', '')  # Add notes field
        )
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, values)
            event_id = cursor.lastrowid
        
        # Return the created event with its new ID
        return self.get_event_by_id(event_id)
    
    def delete_event(self, event_id):
        """
        Delete an event by ID.
        Cascades to delete recurring instances due to foreign key constraint.
        Returns True if deleted, False if not found.
        """
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
            return cursor.rowcount > 0
    
    def update_event(self, event_id, updates):
        """
        Update an existing event with the provided fields.
        
        Args:
            event_id: ID of the event to update
            updates: Dictionary of fields to update (e.g., {'title': 'New Title', 'notes': 'Some notes'})
        
        Returns:
            True if updated successfully, False otherwise
        """
        if not updates:
            return True  # Nothing to update
        
        # Build SET clause dynamically
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        # Add updated_at timestamp
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        # Add event_id for WHERE clause
        values.append(event_id)
        
        query = f"UPDATE events SET {', '.join(set_clauses)} WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, values)
            return cursor.rowcount > 0
    
    def delete_recurring_instance(self, event_id):
        """
        Delete a single recurring instance by ID.
        Does NOT delete other instances.
        Returns True if deleted, False if not found.
        """
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
            return cursor.rowcount > 0
    
    def delete_future_recurring_instances(self, event_id):
        """
        Delete this recurring instance and all future instances (same parent_id, later start time).
        
        Args:
            event_id: ID of the recurring instance to delete from
        
        Returns:
            Number of instances deleted
        """
        # First, get the event to find its parent_id and start_time (separate connection)
        event = self.get_event_by_id(event_id)
        print(f"  delete_future_recurring_instances: event_id={event_id}")
        print(f"  Event retrieved: {event}")
        
        if not event or event['type'] != 'recurring_instance':
            print(f"  ERROR: Event not found or not recurring_instance (type={event.get('type') if event else 'None'})")
            return 0
        
        parent_id = event.get('parent_id')
        start_time = event.get('start')  # _row_to_dict maps start_time → 'start'
        
        print(f"  parent_id={parent_id}, start_time={start_time}")
        
        if not start_time:
            print(f"  ERROR: Missing start_time")
            return 0
        
        # Now delete this instance and all future instances
        with self.get_connection() as conn:
            if parent_id:
                # Standard case: instances have parent_id
                # First, let's see what we're about to delete
                test_cursor = conn.execute("""
                    SELECT id, title, start_time FROM events 
                    WHERE parent_id = ? 
                    AND start_time >= ?
                    AND type = 'recurring_instance'
                """, (parent_id, start_time))
                matching_events = test_cursor.fetchall()
                print(f"  SQL query will match {len(matching_events)} events:")
                for evt in matching_events:
                    print(f"    - ID {evt['id']}: {evt['title']} at {evt['start_time']}")
                
                # Now actually delete them
                cursor = conn.execute("""
                    DELETE FROM events 
                    WHERE parent_id = ? 
                    AND start_time >= ?
                    AND type = 'recurring_instance'
                """, (parent_id, start_time))
            else:
                # Fallback: no parent_id, find by matching title, duration, frequency
                print(f"  No parent_id - finding siblings by title/duration/frequency")
                title = event.get('title')
                duration = event.get('duration')
                frequency = event.get('frequency')
                
                test_cursor = conn.execute("""
                    SELECT id, title, start_time FROM events 
                    WHERE title = ?
                    AND duration = ?
                    AND frequency = ?
                    AND start_time >= ?
                    AND type = 'recurring_instance'
                """, (title, duration, frequency, start_time))
                matching_events = test_cursor.fetchall()
                print(f"  SQL query will match {len(matching_events)} events:")
                for evt in matching_events:
                    print(f"    - ID {evt['id']}: {evt['title']} at {evt['start_time']}")
                
                # Now actually delete them
                cursor = conn.execute("""
                    DELETE FROM events 
                    WHERE title = ?
                    AND duration = ?
                    AND frequency = ?
                    AND start_time >= ?
                    AND type = 'recurring_instance'
                """, (title, duration, frequency, start_time))
            
            deleted = cursor.rowcount
            print(f"  Deleted {deleted} instances")
            return deleted
    
    def get_future_recurring_instances(self, event_id):
        """
        Get IDs of this recurring instance and all future instances (same parent_id, later start time).
        Used to find breaks before deletion.
        
        Args:
            event_id: ID of the recurring instance
        
        Returns:
            List of event IDs
        """
        # First, get the event to find its parent_id and start_time
        event = self.get_event_by_id(event_id)
        if not event or event['type'] != 'recurring_instance':
            return []
        
        parent_id = event.get('parent_id')
        start_time = event.get('start')
        
        if not start_time:
            return []
        
        # Get all future instances with the same parent
        with self.get_connection() as conn:
            if parent_id:
                # Standard case: instances have parent_id
                cursor = conn.execute("""
                    SELECT id FROM events 
                    WHERE parent_id = ? 
                    AND start_time >= ?
                    AND type = 'recurring_instance'
                """, (parent_id, start_time))
            else:
                # Fallback: no parent_id, find by matching title, duration, frequency
                title = event.get('title')
                duration = event.get('duration')
                frequency = event.get('frequency')
                
                cursor = conn.execute("""
                    SELECT id FROM events 
                    WHERE title = ?
                    AND duration = ?
                    AND frequency = ?
                    AND start_time >= ?
                    AND type = 'recurring_instance'
                """, (title, duration, frequency, start_time))
            
            return [row['id'] for row in cursor.fetchall()]
    
    def find_breaks_after_event(self, event_id):
        """
        DEPRECATED: Breaks are now virtual (calculated from gaps).
        This method is kept for backward compatibility but returns empty list.
        
        Args:
            event_id: ID of the event to find breaks after
        
        Returns:
            List of break event IDs (always empty now - breaks are virtual)
        """
        return []  # Virtual breaks are not stored in database
    
    def update_event_times(self, event_id, start_time, end_time):
        """
        Update only start and end times of an event.
        Used for schedule optimization.
        
        Args:
            event_id: ID of event to update
            start_time: New start time (ISO format string)
            end_time: New end time (ISO format string)
        
        Returns:
            True if updated, False if event not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE events 
                SET start_time = ?, end_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (start_time, end_time, event_id))
            return cursor.rowcount > 0
    
    def bulk_update_event_times(self, updates):
        """
        Update multiple events' times in a single transaction.
        Ensures atomic updates - all succeed or all fail.
        
        Args:
            updates: List of dicts with keys 'id', 'start', 'end'
                    e.g., [{'id': 1, 'start': '2025-10-13T09:00:00', 'end': '2025-10-13T10:00:00'}]
        
        Returns:
            Number of events updated
        """
        if not updates:
            return 0
        
        with self.get_connection() as conn:
            count = 0
            for update in updates:
                cursor = conn.execute("""
                    UPDATE events 
                    SET start_time = ?, end_time = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (update['start'], update['end'], update['id']))
                count += cursor.rowcount
            return count
    
    def get_events_in_range(self, start_date, end_date):
        """
        Get all events that overlap with a date range.
        Includes events that start, end, or span across the range.
        
        Args:
            start_date: Range start (ISO format string)
            end_date: Range end (ISO format string)
        
        Returns:
            List of event dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM events 
                WHERE start_time < ? AND end_time > ?
                ORDER BY start_time
            """, (end_date, start_date))
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def check_conflicts(self, start_time, end_time, exclude_id=None):
        """
        Check if a time slot conflicts with existing events.
        Uses indexed query with future-only filter for optimal performance.
        Only checks events that haven't ended yet (past events can't conflict).
        
        Args:
            start_time: ISO format datetime string
            end_time: ISO format datetime string
            exclude_id: Optional event ID to exclude from conflict check (for updates)
        
        Returns:
            True if conflict exists, False if slot is free
        """
        # Future-only optimization: only check events that end after now
        query = """
            SELECT COUNT(*) as count FROM events
            WHERE start_time < ? 
            AND end_time > ?
            AND end_time >= datetime('now')
        """
        params = [end_time, start_time]
        
        # Exclude specific event if updating
        if exclude_id is not None:
            query += " AND id != ?"
            params.append(exclude_id)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            result = cursor.fetchone()
            return result['count'] > 0
    
    def toggle_lock(self, event_id):
        """
        Toggle the locked status of an event.
        Returns the updated event or None if not found.
        """
        event = self.get_event_by_id(event_id)
        if not event:
            return None
        
        new_locked_status = 0 if event['locked'] else 1
        
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE events SET locked = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_locked_status, event_id)
            )
        
        return self.get_event_by_id(event_id)
    
    def _row_to_dict(self, row):
        """
        Convert SQLite Row object to dictionary matching app.py's event format.
        Maps database field names back to app field names.
        """
        if not row:
            return None
        
        event = {
            'id': row['id'],
            'title': row['title'],
            'priority': row['priority'],
            'type': row['type'],
            'category': row['category'],  # Add category field
            'start': row['start_time'],  # Map back from start_time → start
            'end': row['end_time'],      # Map back from end_time → end
            'locked': bool(row['locked'])
        }
        
        # Add notes field safely (handle if column doesn't exist yet)
        try:
            event['notes'] = row['notes'] if row['notes'] is not None else ''
        except (KeyError, IndexError):
            event['notes'] = ''
        
        # Add optional fields only if they're not NULL
        if row['parent_id'] is not None:
            event['parent_id'] = row['parent_id']
        if row['duration'] is not None:
            event['duration'] = row['duration']
        if row['frequency'] is not None:
            event['frequency'] = row['frequency']
        if row['earliest_start'] is not None:
            event['earliest_start'] = row['earliest_start']
        if row['deadline'] is not None:
            event['deadline'] = row['deadline']
        if row['preferred_time'] is not None:
            # Parse JSON string back to dict
            try:
                event['preferred_time'] = json.loads(row['preferred_time'])
            except json.JSONDecodeError:
                event['preferred_time'] = {}
        
        return event
    
    def get_events_in_range(self, start_date, end_date):
        """
        Get events within a specific date range for health score analysis.
        
        Args:
            start_date: ISO format datetime string (inclusive)
            end_date: ISO format datetime string (inclusive)
        
        Returns:
            List of event dictionaries within the date range
        """
        query = """
            SELECT * FROM events 
            WHERE start_time >= ? AND start_time <= ?
            ORDER BY start_time
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def get_user_preferences(self, user_id=1):
        """
        Get user preferences for smart scheduling.
        
        Returns:
            Dictionary with sleep hours, work hours, and scheduling preferences
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                # Return defaults if no preferences found
                return {
                    'sleep_start': '23:00',
                    'sleep_end': '07:00',
                    'work_start': '09:00',
                    'work_end': '18:00',
                    'round_to_minutes': 5
                }
            
            return {
                'sleep_start': row['sleep_start'],
                'sleep_end': row['sleep_end'],
                'work_start': row['work_start'],
                'work_end': row['work_end'],
                'round_to_minutes': row['round_to_minutes']
            }
    
    def update_user_preferences(self, preferences, user_id=1):
        """
        Update user preferences for smart scheduling.
        
        Args:
            preferences: Dictionary with sleep_start, sleep_end, work_start, work_end, round_to_minutes
            user_id: User ID (default 1)
        
        Returns:
            Updated preferences dictionary
        """
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE user_preferences 
                SET sleep_start = ?,
                    sleep_end = ?,
                    work_start = ?,
                    work_end = ?,
                    round_to_minutes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (
                preferences.get('sleep_start', '23:00'),
                preferences.get('sleep_end', '07:00'),
                preferences.get('work_start', '09:00'),
                preferences.get('work_end', '18:00'),
                preferences.get('round_to_minutes', 5),
                user_id
            ))
        
        return self.get_user_preferences(user_id)


# Global database instance
db = DatabaseManager()
