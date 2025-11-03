import React from 'react';

/**
 * Reusable form field component that wraps inputs in consistent styling
 * Handles text, number, datetime-local, and select input types
 */
const FormField = ({ 
  label, 
  type = 'text', 
  name, 
  value, 
  onChange, 
  required = false,
  placeholder = '',
  min,
  options = [] // For select inputs: [{ value: 'high', label: 'High' }, ...]
}) => {
  return (
    <div className="form-group">
      <label>{label}:</label>
      {type === 'select' ? (
        <select 
          name={name} 
          value={value} 
          onChange={onChange}
          required={required}
        >
          {options.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          min={min}
        />
      )}
    </div>
  );
};

export default FormField;
