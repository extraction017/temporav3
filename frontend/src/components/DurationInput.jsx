import React from 'react';

/**
 * Reusable duration input component with unit selector (minutes/hours)
 * Used in both recurring and flexible event forms
 */
const DurationInput = ({ 
  value, 
  unit, 
  onValueChange, 
  onUnitChange, 
  required = true 
}) => {
  return (
    <div className="form-group">
      <label>Duration:</label>
      <div className="duration-input-container">
        <input
          type="number"
          name="duration"
          value={value}
          onChange={onValueChange}
          required={required}
          min="1"
        />
        <select 
          value={unit} 
          onChange={onUnitChange}
        >
          <option value="minutes">Min</option>
          <option value="hours">Hrs</option>
        </select>
      </div>
    </div>
  );
};

export default DurationInput;
