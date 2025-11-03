import React, { useState, useEffect } from 'react';
import './ProductivityScore.css';
import GuideModal from './GuideModal';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function ProductivityScore({ isOpen, onClose }) {
  const [scoreData, setScoreData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [weekOffset, setWeekOffset] = useState(0);
  const [error, setError] = useState(null);
  const [guideOpen, setGuideOpen] = useState(false);
  
  useEffect(() => {
    if (isOpen) {
      fetchProductivityScore();
    }
  }, [isOpen, weekOffset]);
  
  const fetchProductivityScore = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/productivity-score?week_offset=${weekOffset}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch productivity score');
      }
      
      const data = await response.json();
      console.log('[ProductivityScore] API Response:', data);
      setScoreData(data);
    } catch (err) {
      console.error('Productivity score error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const getScoreColor = (score) => {
    if (score >= 90) return 'blue';
    if (score >= 80) return 'dark-green';
    if (score >= 70) return 'light-green';
    if (score >= 60) return 'yellow';
    return 'red';
  };
  
  const getScoreLabel = (score) => {
    if (score >= 90) return 'Outstanding';
    if (score >= 80) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 60) return 'Fair';
    return 'Poor';
  };
  
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  // Generate detailed manual recommendations for productivity
  const getManualRecommendations = () => {
    if (!scoreData || !scoreData.details) return [];
    
    const recommendations = [];
    
    // Fragmentation issues
    if (scoreData.details.fragmentation && scoreData.details.fragmentation.score < 70) {
      const transitions = scoreData.details.fragmentation.transitions || 0;
      recommendations.push({
        urgency: 2,
        category: 'Schedule Fragmentation',
        icon: '🔀',
        title: 'Reduce Context Switching',
        problem: `${transitions} task transitions this week - high fragmentation reduces productivity`,
        impact: 'Each context switch costs 23 minutes of focus time (University of California research)',
        action: `Group similar tasks together and batch related activities.`,
        steps: [
          'Identify similar tasks (emails, coding, meetings, admin)',
          'Block dedicated time for each task type',
          'Batch email/message checking into 2-3 time blocks per day',
          `Target: Reduce transitions by ${Math.floor(transitions * 0.3)} (~30% reduction)`
        ]
      });
    }
    
    // Block structure issues
    if (scoreData.details.block_structure && scoreData.details.block_structure.score < 70) {
      const deepHours = scoreData.details.block_structure.deep_hours || 0;
      const needed = Math.max(0, 15 - deepHours);
      recommendations.push({
        urgency: 1, // Most urgent for productivity
        category: 'Deep Work',
        icon: '🎯',
        title: 'Increase Deep Work Blocks',
        problem: `Only ${deepHours}h of deep work this week (target: 15-25h)`,
        impact: 'Deep work blocks are 3x more productive than fragmented time and critical for complex tasks',
        action: `Schedule ${needed.toFixed(1)}h more uninterrupted deep work blocks (90+ min each).`,
        steps: [
          'Identify your peak focus hours (usually morning)',
          `Block ${Math.ceil(needed / 2)} × 2-hour windows for deep work`,
          'Mark these blocks as "Do Not Disturb" or "Busy"',
          'Turn off all notifications during deep work',
          'Tackle most complex tasks during these blocks'
        ]
      });
    }
    
    // Recovery support issues
    if (scoreData.details.recovery_support && scoreData.details.recovery_support.score < 70) {
      const recoveryHours = scoreData.details.recovery_support.recovery_hours || 0;
      recommendations.push({
        urgency: 2,
        category: 'Recovery',
        icon: '⚡',
        title: 'Add Recovery Time',
        problem: `Only ${recoveryHours}h recovery time this week (target: 10-15h)`,
        impact: 'Adequate recovery prevents burnout and maintains sustainable high performance',
        action: 'Schedule more breaks and personal time to recharge.',
        steps: [
          'Add Recreational events (exercise, hobbies)',
          'Schedule proper meal breaks',
          'Leave 5-10 minute gaps between meetings',
          'Plan at least one full rest day per week'
        ]
      });
    }
    
    // Priority alignment issues
    if (scoreData.details.priority_alignment && scoreData.details.priority_alignment.score < 70) {
      const highPriorityHours = scoreData.details.priority_alignment.high_priority_hours || 0;
      recommendations.push({
        urgency: 1,
        category: 'Priority Alignment',
        icon: '🎖️',
        title: 'Focus on High-Priority Tasks',
        problem: `Only ${highPriorityHours}h on high-priority tasks this week`,
        impact: 'Focusing on high-impact work drives 80% of results (Pareto Principle)',
        action: 'Allocate more time to high-priority tasks and reduce low-priority work.',
        steps: [
          'Review all tasks and mark top priorities',
          'Schedule high-priority work during peak energy hours',
          'Delegate or defer low-priority tasks',
          'Aim for 60-70% of work time on high-priority items'
        ]
      });
    }
    
    // Peak hours utilization
    if (scoreData.details.peak_hours && scoreData.details.peak_hours.score < 70) {
      const utilization = scoreData.details.peak_hours.productive_peak_pct || 0;
      recommendations.push({
        urgency: 2,
        category: 'Peak Hours',
        icon: '⏰',
        title: 'Optimize Peak Productivity Hours',
        problem: `Only ${utilization}% of peak hours used for productive work`,
        impact: 'Peak hours (typically 9-11 AM) offer 2-3x better focus than afternoon',
        action: 'Protect peak hours for most important work.',
        steps: [
          'Identify your personal peak productivity hours',
          'Block these hours for high-priority deep work',
          'Move meetings and admin tasks to afternoon',
          'Decline morning meetings when possible'
        ]
      });
    }
    
    // Time boxing effectiveness
    if (scoreData.details.time_boxing && scoreData.details.time_boxing.score < 70) {
      recommendations.push({
        urgency: 3,
        category: 'Time Management',
        icon: '📦',
        title: 'Improve Time Boxing',
        problem: 'Poor time allocation and task duration estimates',
        impact: 'Effective time boxing prevents overcommitment and improves task completion',
        action: 'Create realistic time estimates and stick to allocated time blocks.',
        steps: [
          'Review how long tasks actually take vs. estimates',
          'Add 25% buffer to estimates (Planning Fallacy)',
          'Use timers to stay within time boxes',
          'Track completion rates to improve estimates'
        ]
      });
    }
    
    // Sort by urgency and return top 3
    return recommendations
      .sort((a, b) => a.urgency - b.urgency)
      .slice(0, 3);
  };
  
  if (!isOpen) return null;
  
  const recommendations = scoreData ? getManualRecommendations() : [];
  
  return (
    <>
      <div className="prod-modal-overlay" onClick={onClose}>
      <div className="prod-modal-content" onClick={e => e.stopPropagation()}>
        <div className="prod-modal-header">
          <h2>⚡ Productivity Score</h2>
          <div className="prod-header-buttons">
            <button className="prod-guide-btn" onClick={() => setGuideOpen(true)} title="Help & Guide">
              ❓
            </button>
            <button className="prod-close-btn" onClick={onClose}>×</button>
          </div>
        </div>
        
        {loading && (
          <div className="prod-loading">
            <div className="spinner-prod"></div>
            <p>Analyzing time allocation efficiency...</p>
          </div>
        )}
        
        {error && (
          <div className="prod-error">
            <p>⚠️ {error}</p>
            <button onClick={fetchProductivityScore}>Retry</button>
          </div>
        )}
        
        {!loading && !error && scoreData && (
          <>
            {/* Week Navigation */}
            <div className="prod-week-nav">
              <button onClick={() => setWeekOffset(weekOffset - 1)}>← Previous</button>
              <span className="prod-week-label">
                {formatDate(scoreData.week_start)} - {formatDate(scoreData.week_end)}
                {weekOffset === 0 && ' (Current Week)'}
              </span>
              <button 
                onClick={() => setWeekOffset(weekOffset + 1)}
                disabled={weekOffset >= 0}
              >
                Next →
              </button>
            </div>
            
            {/* Score and Metrics Layout */}
            <div className="score-metrics-container">
              {/* Score Circle */}
              <div className={`prod-score-circle ${getScoreColor(scoreData.score)}`}>
                <span className="score-value">{scoreData.score}</span>
                <span className="score-label">/ 100</span>
                <span className="score-description">{getScoreLabel(scoreData.score)}</span>
              </div>
              
              {/* 5 Metric Bars */}
              <div className="prod-metrics">
                <MetricBar 
                  label="Block Structure" 
                  score={scoreData.breakdown.block_structure} 
                  weight={30}
                  details={scoreData.details.block_structure}
                  description="Deep work time chunking"
                />
                <MetricBar 
                  label="Fragmentation" 
                  score={scoreData.breakdown.fragmentation} 
                  weight={15}
                  details={scoreData.details.fragmentation}
                  description="Context switching cost"
                />
                <MetricBar 
                  label="Schedule Balance" 
                  score={scoreData.breakdown.schedule_balance} 
                  weight={20}
                  details={scoreData.details.schedule_balance}
                  description="Utilization & planning buffer"
                />
                <MetricBar 
                  label="Meeting Efficiency" 
                  score={scoreData.breakdown.meeting_efficiency} 
                  weight={20}
                  details={scoreData.details.meeting_efficiency}
                  description="Meeting-to-work flow"
                />
                <MetricBar 
                  label="Recovery Support" 
                  score={scoreData.breakdown.recovery_support} 
                  weight={15}
                  details={scoreData.details.recovery_support}
                  description="Non-work recovery"
                />
              </div>
            </div>
            
            {/* Efficiency Stats Summary */}
            <div className="prod-stats-summary">
              <h3>📊 Efficiency Metrics</h3>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-value">{scoreData.efficiency_stats.deep_work_hours}h</span>
                  <span className="stat-label">Deep Work</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{scoreData.efficiency_stats.context_switches}</span>
                  <span className="stat-label">Transitions</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{scoreData.efficiency_stats.wasted_hours}h</span>
                  <span className="stat-label">Wasted (Switching)</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{scoreData.efficiency_stats.work_utilization}%</span>
                  <span className="stat-label">Utilization</span>
                </div>
              </div>
            </div>
            
            {/* Manual Recommendations Section */}
            <div className="prod-actions">
              <h3>🎯 Top Priority Recommendations</h3>
              
              {recommendations.length > 0 ? (
                <>
                  <p className="actions-subtitle">Manual actions to boost your productivity</p>
                  
                  <div className="manual-recommendations">
                    {recommendations.map((rec, idx) => (
                      <div key={idx} className="recommendation-card">
                        <div className="rec-header">
                          <span className="rec-icon">{rec.icon}</span>
                          <div className="rec-title-section">
                            <h4>{rec.title}</h4>
                            <span className="rec-category">{rec.category}</span>
                          </div>
                        </div>
                        
                        <div className="rec-problem">
                          <strong>Problem:</strong> {rec.problem}
                        </div>
                        
                        <div className="rec-impact">
                          <strong>Why it matters:</strong> {rec.impact}
                        </div>
                        
                        <div className="rec-action">
                          <strong>What to do:</strong> {rec.action}
                        </div>
                        
                        <div className="rec-steps">
                          <strong>Action steps:</strong>
                          <ol>
                            {rec.steps.map((step, i) => (
                              <li key={i}>{step}</li>
                            ))}
                          </ol>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="no-recommendations">✅ Excellent! Your schedule is highly productive. No urgent actions needed.</p>
              )}
            </div>
            
            {/* Combined Additional Insights Section */}
            {((scoreData.inefficiencies && scoreData.inefficiencies.length > 0) || 
              (scoreData.optimizations && scoreData.optimizations.length > 0)) && (
              <div className="prod-additional-insights">
                <h4>📋 Additional Insights & Suggestions</h4>
                <p className="insights-subtitle">Other optimization opportunities not covered in top priorities</p>
                
                {scoreData.inefficiencies && scoreData.inefficiencies.length > 0 && (
                  <div className="insights-subsection">
                    <strong>Inefficiencies detected:</strong>
                    {scoreData.inefficiencies.map((item, i) => (
                      <div key={i} className="insight-item">• {item}</div>
                    ))}
                  </div>
                )}
                
                {scoreData.optimizations && scoreData.optimizations.length > 0 && (
                  <div className="insights-subsection">
                    <strong>Optimization suggestions:</strong>
                    {scoreData.optimizations.map((opt, i) => (
                      <div key={i} className="insight-item">• {opt}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Science Badge */}
            <div className="prod-science-badge">
              <small>✨ Based on 7+ studies: Time blocking, fragmentation costs, ETTO principle, planning research</small>
            </div>
          </>
        )}
      </div>
    </div>

    {/* User Guide Modal */}
    <GuideModal 
      isOpen={guideOpen}
      onClose={() => setGuideOpen(false)}
      guideType="productivity"
    />
    </>
  );
}

function MetricBar({ label, score, weight, details, description }) {
  const [showDetails, setShowDetails] = useState(false);
  
  const getBarColor = (score) => {
    if (score >= 90) return '#2196f3';
    if (score >= 80) return '#4caf50';
    if (score >= 70) return '#8bc34a';
    if (score >= 60) return '#ffc107';
    return '#f44336';
  };
  
  const renderDetails = () => {
    if (!details) return null;
    
    return (
      <div className="metric-details">
        {Object.entries(details).map(([key, value]) => {
          if (key === 'score') return null;
          return (
            <div key={key} className="detail-item">
              <span className="detail-label">{formatKey(key)}:</span>
              <span className="detail-value">{value}</span>
            </div>
          );
        })}
      </div>
    );
  };
  
  const formatKey = (key) => {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };
  
  return (
    <div className="metric-bar-container">
      <div className="metric-header" onClick={() => setShowDetails(!showDetails)}>
        <div className="metric-label-col">
          <span className="metric-label">{label}</span>
          <span className="metric-desc">{description}</span>
        </div>
        <div className="metric-info">
          <span className="metric-weight">({weight}%)</span>
          <span className="metric-score">{score}</span>
        </div>
      </div>
      
      <div className="metric-bar-bg">
        <div 
          className="metric-bar-fill" 
          style={{ 
            width: `${score}%`,
            backgroundColor: getBarColor(score)
          }}
        />
      </div>
      
      {showDetails && renderDetails()}
    </div>
  );
}
