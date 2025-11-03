import React from 'react';
import { Pie, Bar, Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
import './Statistics.css';

// Register Chart.js components
ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

// Chart color palette for statistics
const CHART_COLORS = [
  '#8e44ad', // purple
  '#3498db', // blue
  '#f1c40f', // yellow
  '#1abc9c', // turquoise
  '#34495e', // dark grey
  '#95a5a6'  // light grey
];

const Statistics = ({ statistics, onClose, onWeekChange, weekOffset }) => {
  // Category-specific colors matching our design system (muted palette)
  const CATEGORY_COLORS = {
    'Work': '#5d7a8c',        // Muted blue-grey
    'Meeting': '#8e7a9a',     // Muted purple
    'Personal': '#7ba372',    // Muted green
    'Recreational': '#d4a574', // Muted orange
    'Meal': '#c77c7c'         // Muted red
  };

  // Helper function to generate pie chart configuration for categories
  const getPieChartConfig = (categoryDurations) => {
    if (!categoryDurations || Object.keys(categoryDurations).length === 0) {
      return {
        labels: ['No data'],
        datasets: [{
          data: [1],
          backgroundColor: ['#e0e0e0'],
          hoverBackgroundColor: ['#e0e0e0']
        }]
      };
    }
    
    const categories = Object.keys(categoryDurations);
    const colors = categories.map(cat => CATEGORY_COLORS[cat] || '#95a5a6');
    
    return {
      labels: categories,
      datasets: [
        {
          data: Object.values(categoryDurations).map(duration => Math.round(duration * 10) / 10), // Round to 1 decimal
          backgroundColor: colors,
          hoverBackgroundColor: colors
        }
      ]
    };
  };

  // Helper function to generate bar chart config for daily event trends
  const getBarChartConfig = (dailyBreakdown) => {
    const days = [
      'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ];
    const counts = days.map(day => dailyBreakdown[day]?.count || 0);
    return {
      labels: days,
      datasets: [
        {
          label: 'Events per Day',
          data: counts,
          backgroundColor: '#3498db',
          borderRadius: 6,
          maxBarThickness: 32,
        }
      ]
    };
  };

  // STEP 4.2: Helper function to generate donut chart config for priority breakdown
  const getDonutChartConfig = (priorityDurations) => {
    if (!priorityDurations || Object.keys(priorityDurations).length === 0) {
      return {
        labels: ['No data'],
        datasets: [{
          data: [1],
          backgroundColor: ['#e0e0e0'],
          hoverBackgroundColor: ['#e0e0e0']
        }]
      };
    }

    // Priority colors matching event colors
    const priorityColors = {
      'high': '#c77c7c',     // Muted red
      'medium': '#d4a574',   // Muted orange
      'low': '#7ba372'       // Muted green
    };

    const labels = Object.keys(priorityDurations).map(p => 
      p.charAt(0).toUpperCase() + p.slice(1) + ' Priority'
    );
    const data = Object.values(priorityDurations).map(duration => Math.round(duration));
    const colors = Object.keys(priorityDurations).map(p => priorityColors[p] || '#95a5a6');

    return {
      labels: labels,
      datasets: [
        {
          data: data,
          backgroundColor: colors,
          hoverBackgroundColor: colors,
          borderWidth: 2,
          borderColor: '#ffffff'
        }
      ]
    };
  };

  if (!statistics) return null;

  const handleOverlayClick = (e) => {
    // Close if clicking the overlay background (not the modal content)
    if (e.target.className === 'statistics-overlay') {
      onClose();
    }
  };

  return (
    <div className="statistics-overlay" onClick={handleOverlayClick}>
      <div className="statistics-modal">
        <div className="stats-header">
          <h3>📊 Weekly Statistics</h3>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>
        
        {/* Week Navigation */}
        <div className="week-navigation">
          <button 
            className="week-nav-button" 
            onClick={() => onWeekChange(-1)}
            title="Previous Week"
          >
            ← Previous Week
          </button>
          <p className="stats-date-range">
            {weekOffset === 0 && <span className="current-week-badge">Current Week • </span>}
            {weekOffset < 0 && <span className="past-week-badge">{Math.abs(weekOffset)} {Math.abs(weekOffset) === 1 ? 'week' : 'weeks'} ago • </span>}
            {weekOffset > 0 && <span className="future-week-badge">{weekOffset} {weekOffset === 1 ? 'week' : 'weeks'} ahead • </span>}
            {new Date(statistics.week_start).toLocaleDateString()} - {new Date(statistics.week_end).toLocaleDateString()}
          </p>
          <button 
            className="week-nav-button" 
            onClick={() => onWeekChange(1)}
            title="Next Week"
          >
            Next Week →
          </button>
        </div>
      
      {/* Summary Cards */}
      {statistics.summary && (
        <div className="summary-cards">
          <div className="summary-card">
            <div className="card-icon">📅</div>
            <div className="card-content">
              <div className="card-value">{statistics.summary.total_events}</div>
              <div className="card-label">Total Events</div>
            </div>
          </div>
          
          <div className="summary-card">
            <div className="card-icon">⏰</div>
            <div className="card-content">
              <div className="card-value">{statistics.summary.total_hours}h</div>
              <div className="card-label">Total Hours</div>
            </div>
          </div>
          
          <div className="summary-card">
            <div className="card-icon">📊</div>
            <div className="card-content">
              <div className="card-value">{statistics.summary.avg_events_per_day}</div>
              <div className="card-label">Avg Events/Day</div>
            </div>
          </div>
          
          <div className="summary-card">
            <div className="card-icon">⚡</div>
            <div className="card-content">
              <div className="card-value">{statistics.summary.avg_event_duration} min</div>
              <div className="card-label">Avg Duration</div>
            </div>
          </div>
          
          <div className="summary-card">
            <div className="card-icon">💼</div>
            <div className="card-content">
              <div className="card-value">{statistics.summary.productive_hours || 0}h</div>
              <div className="card-label">Productive Time</div>
            </div>
          </div>
          
          <div className="summary-card">
            <div className="card-icon">☕</div>
            <div className="card-content">
              <div className="card-value">{statistics.summary.rest_hours || 0}h</div>
              <div className="card-label">Rest Time</div>
            </div>
          </div>
          
          {statistics.summary.busiest_day && (
            <div className="summary-card highlight">
              <div className="card-icon">🔥</div>
              <div className="card-content">
                <div className="card-value">{statistics.summary.busiest_day.day}</div>
                <div className="card-label">{statistics.summary.busiest_day.event_count} events, {statistics.summary.busiest_day.total_hours}h</div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Charts Section with Header */}
      <div className="charts-section">
        <div className="charts-section-header">
          <span className="icon">📈</span>
          <h3>Visual Analytics</h3>
        </div>
        
        <div className="charts-container">
          {/* Bar Chart for Daily Event Trends */}
          <div className="bar-chart-container">
            <h4>📊 Daily Distribution</h4>
            <div className="chart-wrapper">
              <Bar
                data={getBarChartConfig(statistics.daily_breakdown)}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                      tooltip: { 
                        enabled: true,
                        callbacks: {
                          title: function(context) {
                            return context[0].label;
                          },
                          label: function(context) {
                            const value = context.parsed.y;
                            return `Events: ${value}`;
                          }
                        }
                      }
                  },
                  scales: {
                    x: {
                      grid: { display: false },
                      ticks: { 
                        font: { family: 'Inter', size: 10 },
                        maxRotation: 0,
                        minRotation: 0
                      }
                    },
                    y: {
                      beginAtZero: true,
                      ticks: { 
                        stepSize: 1,
                        font: { family: 'Inter', size: 10 }
                      },
                      grid: { color: '#e8ecf1' }
                    }
                  }
                }}
              />
            </div>
          </div>
        
        {/* Pie Chart for Category Distribution */}
        <div className="pie-chart-container">
          <h4>📊 Category Distribution</h4>
          <div className="chart-wrapper">
            <Pie
              data={getPieChartConfig(statistics.category_durations)}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { 
                    position: 'right',
                    labels: { 
                      font: { family: 'Inter', size: 10 },
                      boxWidth: 12,
                      padding: 8
                    }
                  },
                  tooltip: {
                    callbacks: {
                      label: function(context) {
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        const hours = Math.floor(value / 60);
                        const minutes = Math.round(value % 60);
                        return `${label}: ${hours}h ${minutes}m`;
                      }
                    }
                  }
                }
              }}
            />
          </div>
        </div>

        {/* STEP 4.2: Donut Chart for Priority Breakdown */}
        <div className="donut-chart-container">
          <h4>🎯 Priority Distribution</h4>
          <div className="chart-wrapper">
              <Doughnut
                data={getDonutChartConfig(statistics.priority_durations)}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { 
                      position: 'bottom',
                      labels: { 
                        font: { family: 'Inter', size: 10 },
                        boxWidth: 12,
                        padding: 8
                      }
                    },
                    tooltip: {
                      callbacks: {
                        label: function(context) {
                          const label = context.label || '';
                          const value = context.parsed || 0;
                          const hours = Math.floor(value / 60);
                          const minutes = Math.round(value % 60);
                          return `${label}: ${hours}h ${minutes}m`;
                        }
                      }
                    }
                  },
                  cutout: '60%'
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  );
};

export default Statistics;
