import React, { useState, useEffect, useRef } from "react";  // useState as Hook thingy and useEffect for sideEffects beside rendering (e.g. API request) //
import FullCalendar from "@fullcalendar/react";  // l. 2 to l. 6 just the fullcalendar stuff //
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import axios from "axios";  // to send HTTP API requests//
import { Chart as ChartJS, ArcElement, BarElement, Tooltip, Legend } from 'chart.js';
import './Calendar.css';  // Import calendar styles //
import FormField from './components/FormField';
import DurationInput from './components/DurationInput';
import Statistics from './components/Statistics';
import HealthScore from './components/HealthScore';  // Health Score component
import ProductivityScore from './components/ProductivityScore';  // Productivity Score component
import GuideModal from './components/GuideModal';  // User Guide component
ChartJS.register(ArcElement, BarElement, Tooltip, Legend);

// API Configuration - uses environment variable with fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

// Event type constants to avoid magic strings
const EVENT_TYPES = {
  FIXED: 'event',        // Backend uses 'event' not 'fixed'
  RECURRING: 'recurring',
  FLOATING: 'floating'
};

// Priority options for event forms
const PRIORITY_OPTIONS = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' }
];

const CATEGORY_OPTIONS = [
  { value: 'Work', label: '💼 Work' },
  { value: 'Meeting', label: '🤝 Meeting' },
  { value: 'Personal', label: '👤 Personal' },
  { value: 'Recreational', label: '🎯 Recreational' },
  { value: 'Meal', label: '🍽️ Meal' }
];

// Time format configuration for FullCalendar
const TIME_FORMAT = {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
};

// Helper function to generate user-friendly error messages based on HTTP status
const handleAPIError = (error, operation = 'operation') => {
  if (error.response?.status === 409) {
    return 'The time slot for this event is already occupied.';
  }
  return `Failed to ${operation}. Please check the console for details.`;
};

const Calendar = () => {
  const [events, setEvents] = useState([]);  // array for events//
  const [activeForm, setActiveForm] = useState(null);  // to know which event creation form is used//
  const [statistics, setStatistics] = useState(null);
  const [healthScoreOpen, setHealthScoreOpen] = useState(false);  // Health Score modal state
  const [productivityScoreOpen, setProductivityScoreOpen] = useState(false);  // Productivity Score modal state
  const [weekOffset, setWeekOffset] = useState(0);  // Track which week to display (0 = current, -1 = previous, 1 = next)
  const [showSettings, setShowSettings] = useState(false);  // NEW: Settings modal state
  const [guideOpen, setGuideOpen] = useState(false);  // User Guide modal state
  const [editingEvent, setEditingEvent] = useState(null);  // Event being edited
  const [preferences, setPreferences] = useState({  // NEW: User preferences state
    sleep_start: '23:00',
    sleep_end: '07:00',
    work_start: '09:00',
    work_end: '18:00',
    round_to_minutes: 5
  });
  const [formData, setFormData] = useState({  // all input options for the different events//
    title: "",
    priority: "medium",
    category: "Personal",  // Default category
    start: "",
    end: "",
    duration: "",
    frequency: "",
    start_date: "",
    preferred_time: "",
    earliest_start: "",
    deadline: "",
    notes: "",  // Add notes field
  });
  const [validationResult, setValidationResult] = useState(null);  // Validation warnings/errors
  const [validating, setValidating] = useState(false);  // Validation in progress

  const [durationUnit, setDurationUnit] = useState("minutes");
  const [contextMenu, setContextMenu] = useState({
    visible: false,
    x: 0,
    y: 0,
    event: null
  });
  const [preferredTimeEnabled, setPreferredTimeEnabled] = useState(false);
  const [preferredTimeStart, setPreferredTimeStart] = useState("09:00");
  const [preferredTimeEnd, setPreferredTimeEnd] = useState("17:00");

  // Get current date/time for min validation
  const getCurrentDateTime = () => {
    const now = new Date();
    return now.toISOString().slice(0, 16); // Format: YYYY-MM-DDTHH:MM
  };

  const calendarRef = useRef(null);
  const [currentView, setCurrentView] = useState('timeGridWeek');

  // Helper function to determine event color based on category and priority
  const getEventColor = (event) => {
    // Color by priority for real events
    if (event.priority === "high") return "#8b7db8";  // Bluish-purple (important)
    if (event.priority === "medium") return "#6a9bd6";  // Clear blue (balanced)
    return "#5dae9f";  // Bluish-green/teal (calm)
  };

  // Helper function to validate fixed event dates (handles overnight/multi-day events)
  const validateFixedEventDates = (startStr, endStr) => {
    const startDateTime = new Date(startStr);
    const endDateTime = new Date(endStr);
    
    // Extract just the dates (without time) for comparison
    const startDateOnly = new Date(startDateTime).setHours(0, 0, 0, 0);
    const endDateOnly = new Date(endDateTime).setHours(0, 0, 0, 0);
    
    // Case 1: End date is before start date (e.g., Oct 13 → Oct 12)
    if (endDateOnly < startDateOnly) {
      return {
        valid: false,
        message: "End date is before start date."
      };
    }
    
    // Case 2: Multi-day event (e.g., Oct 12 22:00 → Oct 13 06:00)
    // These are always valid since they span multiple days
    if (endDateOnly > startDateOnly) {
      return { valid: true };
    }
    
    // Case 3: Same-day event - check if end time is after start time
    if (endDateTime <= startDateTime) {
      return {
        valid: false,
        message: "End time must be after start time."
      };
    }
    
    return { valid: true };
  };

  const fetchEvents = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/events`);  // sends API request to backend //
      setEvents(response.data);  // updates events array with returned data //
    } catch (error) {
      console.error("Error fetching events:", error);   // error message if API call fails //
    }
  };

  // NEW: Fetch user preferences from backend
  const fetchPreferences = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/preferences`);
      setPreferences(response.data);
    } catch (error) {
      console.error("Error fetching preferences:", error);
    }
  };

  // NEW: Save user preferences to backend
  const savePreferences = async () => {
    try {
      await axios.put(`${API_BASE_URL}/preferences`, preferences);
      alert('✅ Preferences saved successfully!');
      setShowSettings(false);
    } catch (error) {
      console.error("Error saving preferences:", error);
      alert('❌ Failed to save preferences. Please try again.');
    }
  };

  // NEW: Handle preference input changes
  const handlePreferenceChange = (field, value) => {
    setPreferences(prev => ({
      ...prev,
      [field]: value
    }));
  };

  

  useEffect(() => {
    fetchEvents();  // fetches events when app is loaded, will be useful for data persistence //
    fetchPreferences();  // NEW: Fetch user preferences on mount
  }, []);

  useEffect(() => {
    // Close context menu when clicking outside
    const handleClickOutside = (event) => {
      if (contextMenu.visible) {
        const menuElement = document.querySelector('.context-menu');
        if (menuElement && !menuElement.contains(event.target)) {
          setContextMenu({ visible: false, x: 0, y: 0, event: null });
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [contextMenu.visible]);

  const handleViewChange = (viewInfo) => {
    setCurrentView(viewInfo.view.type);
  };

  const getModifiedEvents = () => {
    if (currentView !== 'dayGridMonth') {
      // For non-month views, return events as is
      return events.map(event => ({
        ...event,
        color: getEventColor(event)
      }));
    }

    return events.map(event => {
      const startDate = new Date(event.start);
      const endDate = event.end ? new Date(event.end) : null;
      
      if (endDate && startDate.toDateString() !== endDate.toDateString()) {
        // Make multi-day events appear only on the first day
        const sameDay = new Date(startDate);
        sameDay.setHours(23, 59, 59);
        
        return {
          ...event,
          end: sameDay.toISOString(),
          color: getEventColor(event)
        };
      }
      
      return {
        ...event,
        color: getEventColor(event)
      };
    });
  };
  

  const fetchStatistics = async (offset = 0) => {  // async to make this statistics thing run seperately while you can do other things //
    try {
      const response = await axios.get(`${API_BASE_URL}/statistics?week_offset=${offset}`);  // await makes the program stop until it gets API result back //
      setStatistics(response.data);  // updates statistics state to the new data it got //
      setWeekOffset(offset);  // Update the week offset state
    } catch (error) {
      console.error("Error fetching statistics:", error);  // error if not returned //
    }
  };

  const handleWeekNavigation = (direction) => {
    const newOffset = weekOffset + direction;
    setWeekOffset(newOffset);
    fetchStatistics(newOffset);
  };

  const handleInputChange = (e) => {  // best practice react pattern, handles input changes, e is the thing you changed //
    const { name, value } = e.target;  // name as in name of input field, value as in what you typed in the field // 
    setFormData({ ...formData, [name]: value });  // updates the state of the form, but copies it and just changes what you entered //
  };

  // Validate event in real-time (debounced)
  const validateEvent = async () => {
    // Only validate fixed events with start/end times
    if (activeForm !== 'fixed' || !formData.start || !formData.end) {
      setValidationResult(null);
      return;
    }

    setValidating(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/validate-event`, {
        event: {
          title: formData.title || 'Untitled',
          category: formData.category,
          priority: formData.priority,
          start: formData.start,
          end: formData.end
        },
        event_id: editingEvent?.id  // Include ID when editing
      });

      setValidationResult(response.data);
    } catch (error) {
      console.error('Validation error:', error);
      setValidationResult(null);
    } finally {
      setValidating(false);
    }
  };

  // Trigger validation when form data changes (debounced)
  useEffect(() => {
    const timer = setTimeout(() => {
      validateEvent();
    }, 500);  // Debounce 500ms

    return () => clearTimeout(timer);
  }, [formData.start, formData.end, formData.category, activeForm]);

  const resetForm = () => {  // resets all form values and closes the form and resets statistics, so just everything null basically //
    setFormData({
      title: "",
      priority: "medium",
      category: "Personal",
      start: "",
      end: "",
      duration: "",
      frequency: "",
      start_date: "",
      preferred_time: "",
      earliest_start: "",
      deadline: "",
      notes: "",
    });
    setActiveForm(null);
    setEditingEvent(null);
    setStatistics(null);
    setDurationUnit("minutes");
    setPreferredTimeEnabled(false);
    setPreferredTimeStart("09:00");
    setPreferredTimeEnd("17:00");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Handle reschedule/optimize form submission (feature, not a type)
    if (activeForm === 'reschedule') {
      try {
        // Validate 7-day maximum
        const startDate = new Date(formData.start);
        const endDate = new Date(formData.end);
        const now = new Date();
        
        // Prevent scheduling in the past
        if (startDate < now) {
          alert('Cannot reschedule past dates. Start date must be today or later.');
          return;
        }
        
        if (endDate < now) {
          alert('Cannot reschedule past dates. End date must be today or later.');
          return;
        }
        
        const daysDiff = (endDate - startDate) / (1000 * 60 * 60 * 24);
        
        if (daysDiff > 7) {
          alert('Maximum optimization range is 7 days.');
          return;
        }
        
        if (daysDiff < 0) {
          alert('End date must be after start date.');
          return;
        }
        
        const response = await axios.post(`${API_BASE_URL}/reschedule`, {
          start_date: formData.start,
          end_date: formData.end,
          confirm_partial: formData.confirmPartial || false
        });
        
        // Handle partial success requiring confirmation
        if (response.data.requires_confirmation) {
          const failedList = response.data.failed_events
            .map(e => `- ${e.title} (${e.type}, ${e.priority})`)
            .join('\n');
          
          const confirmed = window.confirm(
            `⚠️ Partial Success\n\n` +
            `${response.data.success_count} events can be optimized.\n` +
            `${response.data.failed_count} events could not be rescheduled:\n\n${failedList}\n\n` +
            `Apply changes to the ${response.data.success_count} events anyway?`
          );
          
          if (confirmed) {
            // Resubmit with confirmation
            const confirmedResponse = await axios.post(`${API_BASE_URL}/reschedule`, {
              start_date: formData.start,
              end_date: formData.end,
              confirm_partial: true
            });
            
            alert(`✓ Successfully optimized ${confirmedResponse.data.success} events!`);
            fetchEvents();
            resetForm();
          }
        } else {
          // Full success or error
          if (response.data.success > 0) {
            let message = `✓ Successfully optimized ${response.data.success} events!`;
            if (response.data.failed > 0) {
              message += `\n\n⚠️ ${response.data.failed} events could not be rescheduled.`;
            }
            alert(message);
            fetchEvents();
            resetForm();
          } else {
            alert(`No events were optimized.\n${response.data.message || ''}`);
          }
        }
      } catch (error) {
        console.error("Error optimizing schedule:", error);
        const errorMsg = error.response?.data?.error || 'Failed to optimize schedule.';
        const failedEvents = error.response?.data?.failed_events;
        
        if (failedEvents && failedEvents.length > 0) {
          alert(`❌ ${errorMsg}\n\nAffected events:\n${failedEvents.join('\n')}`);
        } else {
          alert(`❌ ${errorMsg}`);
        }
      }
      return;
    }
    
    // Validate fixed event dates (handles overnight/multi-day events)
    if (activeForm === EVENT_TYPES.FIXED) {
      const validation = validateFixedEventDates(formData.start, formData.end);
      if (!validation.valid) {
        alert(`Error: ${validation.message}`);
        return;
      }
    }
  
    try {
      let eventData = { ...formData, type: activeForm };
      
      // Add preferred_time object if enabled (for recurring/floating only)
      if (activeForm === EVENT_TYPES.RECURRING || activeForm === EVENT_TYPES.FLOATING) {
        eventData.preferred_time = {
          enabled: preferredTimeEnabled,
          start: preferredTimeEnabled ? preferredTimeStart : null,
          end: preferredTimeEnabled ? preferredTimeEnd : null
        };
      }
      
      // Convert hours to minutes if needed for events with duration
      if ((activeForm === EVENT_TYPES.RECURRING || activeForm === EVENT_TYPES.FLOATING) && durationUnit === "hours") {
        eventData = {
          ...eventData,
          duration: (parseFloat(formData.duration) * 60).toString()
        };
      }
    
      await axios.post(`${API_BASE_URL}/events`, eventData);
      alert("Event added successfully!");
      resetForm();
      fetchEvents(); // refresh events to include all new instances
    } catch (error) {
      console.error("Error adding event:", error);
      alert(handleAPIError(error, 'add event'));
    }
  };

  const handleEventClick = (clickInfo) => {
    // Prevent default FullCalendar behavior
    clickInfo.jsEvent.preventDefault();
    clickInfo.jsEvent.stopPropagation();
    
    // Get click position for context menu
    const rect = clickInfo.el.getBoundingClientRect();
    setContextMenu({
      visible: true,
      x: rect.left,
      y: rect.bottom + 5, // Position just below the event
      event: {
        id: clickInfo.event.id,
        title: clickInfo.event.title,
        locked: clickInfo.event.extendedProps.locked || false,
        extendedProps: {
          type: clickInfo.event.extendedProps.type
        }
      }
    });
  };

  const handleLockToggle = async () => {
    try {
      await axios.post(`${API_BASE_URL}/events/${contextMenu.event.id}/lock`);
      await fetchEvents();
      alert(`Event ${contextMenu.event.locked ? 'unlocked' : 'locked'} successfully!`);
      setContextMenu({ visible: false, x: 0, y: 0, event: null });
    } catch (error) {
      console.error("Error toggling lock:", error);
      alert(handleAPIError(error, 'toggle lock'));
    }
  };

  const handleEditEvent = async () => {
    const eventId = contextMenu.event.id;
    
    try {
      // Fetch full event data from backend
      const response = await axios.get(`${API_BASE_URL}/events`);
      const fullEvent = response.data.find(e => e.id == eventId);  // Use == for type coercion
      
      if (!fullEvent) {
        console.error('Event not found. Looking for ID:', eventId);
        console.error('Available events:', response.data.map(e => ({ id: e.id, title: e.title })));
        alert('Event not found');
        return;
      }
      
      // Populate form with event data
      setFormData({
        title: fullEvent.title,
        priority: fullEvent.priority,
        category: fullEvent.category || "Personal",
        start: fullEvent.start,
        end: fullEvent.end,
        duration: fullEvent.duration || "",
        frequency: fullEvent.frequency || "",
        start_date: "",
        preferred_time: "",
        earliest_start: fullEvent.earliest_start || "",
        deadline: fullEvent.deadline || "",
        notes: fullEvent.notes || "",
      });
      
      setEditingEvent(fullEvent);
      setContextMenu({ visible: false, x: 0, y: 0, event: null });
    } catch (error) {
      console.error("Error loading event for edit:", error);
      alert('Failed to load event data');
    }
  };

  const handleUpdateEvent = async (e) => {
    e.preventDefault();
    
    if (!editingEvent) return;
    
    try {
      const updates = {
        title: formData.title,
        priority: formData.priority,
        category: formData.category,
        notes: formData.notes,
      };
      
      // Only include time fields if they changed
      if (formData.start && formData.start !== editingEvent.start) {
        updates.start = formData.start;
      }
      if (formData.end && formData.end !== editingEvent.end) {
        updates.end = formData.end;
      }
      
      await axios.put(`${API_BASE_URL}/events/${editingEvent.id}`, updates);
      await fetchEvents();
      alert('Event updated successfully!');
      resetForm();
    } catch (error) {
      console.error("Error updating event:", error);
      if (error.response?.status === 409) {
        alert('The new time slot is already occupied.');
      } else {
        alert(handleAPIError(error, 'update event'));
      }
    }
  };

  const handleDelete = async (mode = 'default') => {
    const event = contextMenu.event;
    const isRecurring = event.extendedProps?.type === 'recurring_instance';
    
    // If recurring and no mode specified, show options dialog
    if (isRecurring && mode === 'default') {
      // Will be handled by the context menu showing delete options
      return;
    }
    
    // Build confirmation message
    let confirmMessage = '';
    if (mode === 'this_instance') {
      confirmMessage = `Delete only this instance of '${event.title}'?`;
    } else if (mode === 'all_future') {
      confirmMessage = `Delete this instance and all future instances of '${event.title}'?`;
    } else {
      confirmMessage = `Are you sure you want to delete '${event.title}'?`;
    }
    
    if (window.confirm(confirmMessage)) {
      try {
        // Add mode parameter to delete request
        const url = mode !== 'default' 
          ? `${API_BASE_URL}/events/${event.id}?mode=${mode}`
          : `${API_BASE_URL}/events/${event.id}`;
        
        const response = await axios.delete(url);
        await fetchEvents();
        
        // Show detailed success message
        const message = response.data.message || "Event deleted successfully!";
        alert(message);
        setContextMenu({ visible: false, x: 0, y: 0, event: null });
      } catch (error) {
        console.error("Error deleting event:", error);
        alert(handleAPIError(error, 'delete event'));
      }
    }
  };

  const handleCloseMenu = () => {
    setContextMenu({ visible: false, x: 0, y: 0, event: null });
  };

  const renderEventContent = (eventInfo) => {
    return (
      <div className="fc-event-dot-container">
        <div 
          className="fc-event-dot" 
          style={{ backgroundColor: eventInfo.event.backgroundColor || eventInfo.event.color }}
        />
        <div className="fc-event-title">
          {eventInfo.timeText && <span className="fc-event-time">{eventInfo.timeText}</span>}
          <span>{eventInfo.event.title}</span>
        </div>
      </div>
    );
  };

  // Render function for reschedule form
  const renderRescheduleForm = () => (
    <form onSubmit={handleSubmit} className="event-form">
      <h3>⚖️ Balance Workload</h3>
      <p className="form-description">
        Evenly distribute events across the selected time range to balance daily workload.
        Events are redistributed by total duration (not just count) to prevent overloaded days.
        <br /><strong>Maximum range: 7 days • Cannot schedule in the past</strong>
      </p>
      
      <div className="form-row two-cols">
        <FormField
          label="Start Date/Time"
          type="datetime-local"
          name="start"
          value={formData.start}
          onChange={handleInputChange}
          min={getCurrentDateTime()}
          required
        />
        <FormField
          label="End Date/Time (Max 7 days from start)"
          type="datetime-local"
          name="end"
          value={formData.end}
          onChange={handleInputChange}
          min={getCurrentDateTime()}
          required
        />
      </div>
      <div className="optimization-info">
        <p className="info-text">
          <strong>How workload is balanced:</strong>
        </p>
        <ul className="optimization-list">
          <li>🔒 <strong>Locked events</strong> - Never moved (immovable anchors)</li>
          <li>⚖️ <strong>Duration-based balancing</strong> - Days balanced by total hours, not just event count</li>
          <li>� <strong>Priority ordering</strong> - High priority scheduled first, then medium, then low</li>
          <li>🎯 <strong>Smart placement</strong> - Events placed in appropriate time windows by category</li>
        </ul>
      </div>
      <div className="form-buttons">
        <button type="submit">Balance Workload</button>
        <button type="button" onClick={resetForm}>Cancel</button>
      </div>
    </form>
  );

  // Render function for fixed event form
  const renderFixedEventForm = () => (
    <form onSubmit={handleSubmit} className="event-form">
      <h3>📌 Fixed Event</h3>
      <p className="form-description">
        Create a time-specific event that stays at its scheduled time. 
        Perfect for meetings, appointments, and time-sensitive commitments.
      </p>
      
      <div className="form-row three-cols">
        <FormField
          label="Title"
          type="text"
          name="title"
          value={formData.title}
          onChange={handleInputChange}
          required
        />
        <FormField
          label="Priority"
          type="select"
          name="priority"
          value={formData.priority}
          onChange={handleInputChange}
          options={PRIORITY_OPTIONS}
        />
        <FormField
          label="Category"
          type="select"
          name="category"
          value={formData.category}
          onChange={handleInputChange}
          options={CATEGORY_OPTIONS}
        />
      </div>
      
      <div className="form-row two-cols">
        <FormField
          label="Start Time"
          type="datetime-local"
          name="start"
          value={formData.start}
          onChange={handleInputChange}
          required
        />
        <FormField
          label="End Time"
          type="datetime-local"
          name="end"
          value={formData.end}
          onChange={handleInputChange}
          required
        />
      </div>
      
      <div className="form-field">
        <label>
          📝 Notes (Optional) <span className="char-count">{formData.notes.length}/200</span>
        </label>
        <textarea
          value={formData.notes}
          onChange={(e) => {
            if (e.target.value.length <= 200) {
              setFormData({ ...formData, notes: e.target.value });
            }
          }}
          placeholder="Add extra information about this event..."
          maxLength={200}
          rows={3}
          className="notes-input"
        />
      </div>
      
      {/* Real-time Validation Warnings */}
      {validating && (
        <div className="validation-loading">
          ⏳ Checking for schedule conflicts...
        </div>
      )}
      
      {validationResult && (
        <div className="validation-results">
          {/* Errors (blocking issues) */}
          {validationResult.errors && validationResult.errors.length > 0 && (
            <div className="validation-section validation-errors">
              <h4>❌ Errors</h4>
              {validationResult.errors.map((error, idx) => (
                <div key={idx} className="validation-item error">
                  <strong>{error.type}:</strong> {error.message}
                </div>
              ))}
            </div>
          )}
          
          {/* Warnings (recommended to fix) */}
          {validationResult.warnings && validationResult.warnings.length > 0 && (
            <div className="validation-section validation-warnings">
              <h4>⚠️ Warnings</h4>
              {validationResult.warnings.map((warning, idx) => (
                <div key={idx} className="validation-item warning">
                  <strong>{warning.type}:</strong> {warning.message}
                </div>
              ))}
            </div>
          )}
          
          {/* Suggestions (helpful tips) */}
          {validationResult.suggestions && validationResult.suggestions.length > 0 && (
            <div className="validation-section validation-suggestions">
              <h4>💡 Suggestions</h4>
              {validationResult.suggestions.map((suggestion, idx) => (
                <div key={idx} className="validation-item suggestion">
                  <strong>{suggestion.type}:</strong> {suggestion.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      <div className="form-buttons">
        <button type="submit" disabled={validationResult && !validationResult.valid}>
          {editingEvent ? 'Update Event' : 'Create Event'}
        </button>
        <button type="button" onClick={resetForm}>Cancel</button>
      </div>
    </form>
  );

  // Render function for recurring event form with optional preferred time
  const renderRecurringEventForm = () => {
    return (
      <form onSubmit={handleSubmit} className="event-form">
        <h3>🔁 Recurring Event</h3>
        <p className="form-description">
          Schedule a repeating task with customizable frequency. 
          The system will automatically find optimal time slots for each instance.
        </p>
        
        <div className="form-row three-cols">
          <FormField
            label="Title"
            type="text"
            name="title"
            value={formData.title}
            onChange={handleInputChange}
            required
          />
          <FormField
            label="Priority"
            type="select"
            name="priority"
            value={formData.priority}
            onChange={handleInputChange}
            options={PRIORITY_OPTIONS}
          />
          <FormField
            label="Category"
            type="select"
            name="category"
            value={formData.category}
            onChange={handleInputChange}
            options={CATEGORY_OPTIONS}
          />
        </div>
        
        <div className="form-row three-cols">
          <FormField
            label="Start Date"
            type="datetime-local"
            name="start_date"
            value={formData.start_date}
            onChange={handleInputChange}
            required
          />
          <DurationInput
            value={formData.duration}
            unit={durationUnit}
            onValueChange={handleInputChange}
            onUnitChange={(e) => setDurationUnit(e.target.value)}
          />
          <FormField
            label="Frequency (days)"
            type="number"
            name="frequency"
            value={formData.frequency}
            onChange={handleInputChange}
            required
            min="1"
          />
        </div>
        
        <div style={{ margin: '15px 0' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={preferredTimeEnabled}
              onChange={(e) => setPreferredTimeEnabled(e.target.checked)}
            />
            <span>⏰ Set Preferred Time Window</span>
          </label>
        </div>
        
        {preferredTimeEnabled && (
          <div className="form-row two-cols">
            <FormField
              label="Start Time"
              type="time"
              value={preferredTimeStart}
              onChange={(e) => setPreferredTimeStart(e.target.value)}
            />
            <FormField
              label="End Time"
              type="time"
              value={preferredTimeEnd}
              onChange={(e) => setPreferredTimeEnd(e.target.value)}
            />
          </div>
        )}
        
        <div className="form-field">
          <label>
            📝 Notes (Optional) <span className="char-count">{formData.notes.length}/200</span>
          </label>
          <textarea
            value={formData.notes}
            onChange={(e) => {
              if (e.target.value.length <= 200) {
                setFormData({ ...formData, notes: e.target.value });
              }
            }}
            placeholder="Add extra information about this event..."
            maxLength={200}
            rows={3}
            className="notes-input"
          />
        </div>
        
        <div className="form-buttons">
          <button type="submit">Create Event</button>
          <button type="button" onClick={resetForm}>Cancel</button>
        </div>
      </form>
    );
  };

  // Render function for floating event form with optional preferred time
  const renderFloatingEventForm = () => {
    return (
      <form onSubmit={handleSubmit} className="event-form">
        <h3>⏰ Floating Event</h3>
        <p className="form-description">
          Create an auto-scheduled task that finds the optimal time slot before your deadline. 
          Great for flexible tasks like studying, exercise, or project work.
        </p>
        
        <div className="form-row three-cols">
          <FormField
            label="Title"
            type="text"
            name="title"
            value={formData.title}
            onChange={handleInputChange}
            required
          />
          <FormField
            label="Priority"
            type="select"
            name="priority"
            value={formData.priority}
            onChange={handleInputChange}
            options={PRIORITY_OPTIONS}
          />
          <FormField
            label="Category"
            type="select"
            name="category"
            value={formData.category}
            onChange={handleInputChange}
            options={CATEGORY_OPTIONS}
          />
        </div>
        
        <div className="form-row three-cols">
          <DurationInput
            value={formData.duration}
            unit={durationUnit}
            onValueChange={handleInputChange}
            onUnitChange={(e) => setDurationUnit(e.target.value)}
          />
          <FormField
            label="Earliest Start"
            type="datetime-local"
            name="earliest_start"
            value={formData.earliest_start}
            onChange={handleInputChange}
            required
          />
          <FormField
            label="Deadline"
            type="datetime-local"
            name="deadline"
            value={formData.deadline}
            onChange={handleInputChange}
            required
          />
        </div>
        
        <div style={{ margin: '15px 0' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={preferredTimeEnabled}
              onChange={(e) => setPreferredTimeEnabled(e.target.checked)}
            />
            <span>⏰ Set Preferred Time Window</span>
          </label>
        </div>
        
        {preferredTimeEnabled && (
          <div className="form-row two-cols">
            <FormField
              label="Start Time"
              type="time"
              value={preferredTimeStart}
              onChange={(e) => setPreferredTimeStart(e.target.value)}
            />
            <FormField
              label="End Time"
              type="time"
              value={preferredTimeEnd}
              onChange={(e) => setPreferredTimeEnd(e.target.value)}
            />
          </div>
        )}
        
        <div className="form-field">
          <label>
            📝 Notes (Optional) <span className="char-count">{formData.notes.length}/200</span>
          </label>
          <textarea
            value={formData.notes}
            onChange={(e) => {
              if (e.target.value.length <= 200) {
                setFormData({ ...formData, notes: e.target.value });
              }
            }}
            placeholder="Add extra information about this event..."
            maxLength={200}
            rows={3}
            className="notes-input"
          />
        </div>
        
        <div className="form-buttons">
          <button type="submit">Create Event</button>
          <button type="button" onClick={resetForm}>Cancel</button>
        </div>
      </form>
    );
  };

  // Main form router - delegates to specific form renderers
  const renderForm = () => {
    if (!activeForm) return null;

    switch (activeForm) {
      case 'reschedule':  // Feature, not a type
        return renderRescheduleForm();
      case EVENT_TYPES.FIXED:
        return renderFixedEventForm();
      case EVENT_TYPES.RECURRING:
        return renderRecurringEventForm();
      case EVENT_TYPES.FLOATING:
        return renderFloatingEventForm();
      default:
        return null;
    }
  };

  return (  /* UI stuff, l. 277 header, l. 279-306 buttons to add events + buttons for statistics, (+ reschedule but logic doesnt work yet)
    l. 309 - 322 for statistics panel if clicked, l. 324 just rendering form, l. 326- 341 fullcalendar best practice to display events, rest styling*/
    <div className="calendar-container">
      {/* Context Menu for event actions */}
      {contextMenu.visible && (
        <div 
          className="context-menu" 
          style={{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }}
        >
          <button onClick={handleEditEvent}>
            ✏️ Edit Event
          </button>
          
          <button onClick={handleLockToggle}>
            {contextMenu.event.locked ? '🔓 Unlock Event' : '🔒 Lock Event'}
          </button>
          
          {/* Show different delete options for recurring events */}
          {contextMenu.event.extendedProps?.type === 'recurring_instance' ? (
            <>
              <button onClick={() => handleDelete('this_instance')}>
                🗑️ Delete This Instance
              </button>
              <button onClick={() => handleDelete('all_future')}>
                🗑️🔁 Delete This & Future Instances
              </button>
            </>
          ) : (
            <button onClick={() => handleDelete('default')}>
              🗑️ Delete Event
            </button>
          )}
          
          <button onClick={handleCloseMenu}>
            ❌ Cancel
          </button>
        </div>
      )}

      {/* Edit Event Modal */}
      {editingEvent && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleUpdateEvent} className="event-form">
              <h3>✏️ Edit Event</h3>
              
              <FormField
                label="Event Title"
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />

              <FormField
                label="Priority"
                type="select"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                options={PRIORITY_OPTIONS}
              />

              <FormField
                label="Category"
                type="select"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                options={CATEGORY_OPTIONS}
              />

              <FormField
                label="Start Time"
                type="datetime-local"
                value={formData.start}
                onChange={(e) => setFormData({ ...formData, start: e.target.value })}
              />

              <FormField
                label="End Time"
                type="datetime-local"
                value={formData.end}
                onChange={(e) => setFormData({ ...formData, end: e.target.value })}
              />

              <div className="form-field">
                <label>
                  📝 Notes <span className="char-count">{formData.notes.length}/200</span>
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => {
                    if (e.target.value.length <= 200) {
                      setFormData({ ...formData, notes: e.target.value });
                    }
                  }}
                  placeholder="Add extra information about this event..."
                  maxLength={200}
                  rows={3}
                  className="notes-input"
                />
              </div>

              <div className="form-actions">
                <button type="submit" className="submit-button">
                  💾 Save Changes
                </button>
                <button type="button" onClick={resetForm} className="cancel-button">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* NEW: Settings Modal */}
      {showSettings && (
        <div className="settings-overlay" onClick={() => setShowSettings(false)}>
          <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
            <h2>⚙️ Scheduling Preferences</h2>
            
            <div className="settings-section">
              <h3>😴 Sleep Hours</h3>
              <p className="settings-description">Events will not be scheduled during these hours</p>
              <div className="settings-row">
                <FormField
                  label="Bedtime"
                  type="time"
                  value={preferences.sleep_start}
                  onChange={(e) => handlePreferenceChange('sleep_start', e.target.value)}
                />
                <FormField
                  label="Wake Time"
                  type="time"
                  value={preferences.sleep_end}
                  onChange={(e) => handlePreferenceChange('sleep_end', e.target.value)}
                />
              </div>
            </div>

            <div className="settings-section">
              <h3>💼 Work Hours</h3>
              <p className="settings-description">Preferred hours for scheduling events</p>
              <div className="settings-row">
                <FormField
                  label="Work Start"
                  type="time"
                  value={preferences.work_start}
                  onChange={(e) => handlePreferenceChange('work_start', e.target.value)}
                />
                <FormField
                  label="Work End"
                  type="time"
                  value={preferences.work_end}
                  onChange={(e) => handlePreferenceChange('work_end', e.target.value)}
                />
              </div>
            </div>

            <div className="settings-section">
              <h3>🕐 Time Rounding</h3>
              <p className="settings-description">Round event times to nearest interval</p>
              <div className="settings-row">
                <label className="form-label">
                  Round To
                  <select 
                    className="form-input"
                    value={preferences.round_to_minutes}
                    onChange={(e) => handlePreferenceChange('round_to_minutes', parseInt(e.target.value))}
                  >
                    <option value={5}>5 minutes (:00, :05, :10, :15...)</option>
                    <option value={10}>10 minutes (:00, :10, :20, :30...)</option>
                    <option value={15}>15 minutes (:00, :15, :30, :45)</option>
                    <option value={30}>30 minutes (:00, :30)</option>
                  </select>
                </label>
              </div>
            </div>

            <div className="settings-buttons">
              <button className="btn-primary" onClick={savePreferences}>💾 Save Preferences</button>
              <button className="btn-secondary" onClick={() => setShowSettings(false)}>❌ Cancel</button>
            </div>
          </div>
        </div>
      )}

      <div className="top-controls">
        <div className="event-buttons">
          <button onClick={() => setActiveForm(EVENT_TYPES.FIXED)}>
            📌 Fixed
          </button>
          <button onClick={() => setActiveForm(EVENT_TYPES.RECURRING)}>
            🔄 Recurring
          </button>
          <button onClick={() => setActiveForm(EVENT_TYPES.FLOATING)}>
            ⏱️ Floating
          </button>
        </div>
        
        <div className="utility-buttons">
          <button onClick={() => setActiveForm('reschedule')} className="utility-button">
            ⚖️ Balance
          </button>
          <button onClick={() => fetchStatistics(0)} className="utility-button">
            📊 Statistics
          </button>
          <button onClick={() => setGuideOpen(true)} className="utility-button">
            ❓ Guide
          </button>
          <button onClick={() => setHealthScoreOpen(true)} className="utility-button">
            💚 Health
          </button>
          <button onClick={() => setProductivityScoreOpen(true)} className="utility-button">
            ⚡ Productivity
          </button>
          <button onClick={() => setShowSettings(true)} className="utility-button">
            ⚙️ Settings
          </button>
        </div>
      </div>

      <Statistics 
        statistics={statistics} 
        onClose={() => {
          setStatistics(null);
          setWeekOffset(0);  // Reset to current week when closing
        }}
        onWeekChange={handleWeekNavigation}
        weekOffset={weekOffset}
      />

      <HealthScore 
        isOpen={healthScoreOpen}
        onClose={() => setHealthScoreOpen(false)}
      />

      <ProductivityScore 
        isOpen={productivityScoreOpen}
        onClose={() => setProductivityScoreOpen(false)}
      />

      {renderForm()}

      <div className="calendar">
        <FullCalendar
          ref={calendarRef}
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          
          firstDay={1}
          allDaySlot={false}
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay",
          }}
          events={getModifiedEvents()}
          datesSet={handleViewChange}
          viewDidMount={handleViewChange}
          editable={false}
          selectable={true}
          height="100%"
          eventClick={handleEventClick}
          eventTimeFormat={TIME_FORMAT}
          slotLabelFormat={TIME_FORMAT}
          eventOverlap={false}
          slotEventOverlap={false}
          eventDidMount={(info) => {
            // Force the element's width to 100% with !important
            info.el.style.setProperty("width", "100%", "important");
            
            // Also target the parent harness element that controls positioning
            const harness = info.el.closest('.fc-timegrid-event-harness');
            if (harness) {
              harness.style.setProperty("width", "100%", "important");
            }
            
            // Add white outline for locked events (dark theme)
            if (info.event.extendedProps.locked) {
              info.el.style.outline = "2px solid white";
              info.el.style.outlineOffset = "-2px";
            }
            
            // Add glowy look to all events
            const bgColor = info.event.backgroundColor || info.event.color;
            if (bgColor) {
              // Helper function to lighten a hex color
              const lightenColor = (hex, percent) => {
                const num = parseInt(hex.replace('#', ''), 16);
                const r = Math.min(255, ((num >> 16) + Math.floor((255 - (num >> 16)) * percent)));
                const g = Math.min(255, (((num >> 8) & 0x00FF) + Math.floor((255 - ((num >> 8) & 0x00FF)) * percent)));
                const b = Math.min(255, ((num & 0x0000FF) + Math.floor((255 - (num & 0x0000FF)) * percent)));
                return `rgb(${r}, ${g}, ${b})`;
              };
              
              // Check if it's a month view event (smaller events in dayGrid)
              const isMonthView = info.el.classList.contains('fc-daygrid-event');
              
              // Reduce glow for month view (10% less than week view)
              if (isMonthView) {
                info.el.style.boxShadow = `0 0 8px ${bgColor}60, 0 0 15px ${bgColor}30`;
              } else {
                info.el.style.boxShadow = `0 0 12px ${bgColor}70, 0 0 20px ${bgColor}35`;
              }
              
              // Border color: lighter shade (50% lighter)
              const borderColor = lightenColor(bgColor, 0.5);
              
              // Text color: even lighter shade (65% lighter)
              const textColor = lightenColor(bgColor, 0.65);
              
              // Add subtle border
              info.el.style.border = `1px solid ${borderColor}`;
              
              const titleEl = info.el.querySelector('.fc-event-title');
              if (titleEl) {
                titleEl.style.color = textColor;
                titleEl.style.textShadow = `0 0 8px ${bgColor}`;
              }
              
              // Also style the time text
              const timeEl = info.el.querySelector('.fc-event-time');
              if (timeEl) {
                timeEl.style.color = textColor;
                timeEl.style.textShadow = `0 0 6px ${bgColor}`;
              }
            }
          }}
        />
      </div>

      {/* User Guide Modal */}
      <GuideModal 
        isOpen={guideOpen}
        onClose={() => setGuideOpen(false)}
        guideType="general"
      />
    </div>
  );
};

export default Calendar;