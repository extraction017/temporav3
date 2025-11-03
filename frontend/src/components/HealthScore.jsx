import React, { useState, useEffect } from 'react';
import './HealthScore.css';
import GuideModal from './GuideModal';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function HealthScore({ isOpen, onClose }) {
  const [scoreData, setScoreData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [weekOffset, setWeekOffset] = useState(0);
  const [error, setError] = useState(null);
  const [guideOpen, setGuideOpen] = useState(false);
  
  useEffect(() => {
    if (isOpen) {
      fetchHealthScore();
    }
  }, [isOpen, weekOffset]);
  
  const fetchHealthScore = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/health-score?week_offset=${weekOffset}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch health score');
      }
      
      const data = await response.json();
      console.log('[HealthScore] API Response:', data);
      setScoreData(data);
    } catch (err) {
      console.error('Health score error:', err);
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

  // Generate detailed manual recommendations based on score data
  const getManualRecommendations = () => {
    if (!scoreData || !scoreData.details) return [];
    
    const recommendations = [];
    
    // Sleep respect issues
    if (scoreData.details.sleep_respect && scoreData.details.sleep_respect.score < 70) {
      const intrusions = scoreData.details.sleep_respect.intrusion_count || 0;
      if (intrusions > 0) {
        recommendations.push({
          urgency: 1, // Most urgent
          category: 'Sleep',
          icon: '😴',
          title: 'Fix Sleep Schedule Violations',
          problem: `${intrusions} event(s) intrude into sleep hours (${scoreData.details.sleep_respect.sleep_start || '22:00'} - ${scoreData.details.sleep_respect.sleep_end || '07:00'})`,
          impact: 'Insufficient sleep reduces cognitive performance by 40% and increases health risks',
          action: `Manually reschedule ${intrusions} conflicting event(s) to daytime hours. Aim for 7-9 hours of uninterrupted sleep.`,
          steps: [
            'Review events during sleep hours in your calendar',
            'Move late-night events to earlier time slots',
            'Move early-morning events to after 7 AM',
            'Consider declining recurring meetings that conflict with sleep'
          ]
        });
      }
    }
    
    // Recovery time issues
    if (scoreData.details.recovery && scoreData.details.recovery.score < 70) {
      const activeHours = scoreData.details.recovery.active_recovery_hours || 0;
      const needed = Math.max(0, 7 - activeHours);
      if (needed > 0) {
        recommendations.push({
          urgency: 2,
          category: 'Recovery',
          icon: '🧘',
          title: 'Increase Active Recovery Time',
          problem: `Only ${activeHours.toFixed(1)}h of active recovery this week (target: 7-14h)`,
          impact: 'Active recovery (exercise, hobbies, social meals) reduces burnout by 68% and improves resilience',
          action: `Schedule ${needed.toFixed(1)}h more Recreational or Meal events this week.`,
          steps: [
            `Add ${Math.ceil(needed / 2)} Recreational events (exercise, hobbies, social activities)`,
            'Schedule proper meal breaks with "Meal" event type',
            'Block time for walks, sports, or creative activities',
            'Passive gaps help slightly, but active recovery is 16x more effective'
          ]
        });
      }
    }
    
    // Meeting load issues
    if (scoreData.details.meetings && scoreData.details.meetings.score < 70) {
      const b2bCount = scoreData.details.meetings.b2b_count || 0;
      const meetingShare = scoreData.details.meetings.share || 0;
      
      if (b2bCount > 0) {
        recommendations.push({
          urgency: 2,
          category: 'Meetings',
          icon: '📅',
          title: 'Add Gaps Between Meetings',
          problem: `${b2bCount} back-to-back meetings without mental reset time`,
          impact: 'Back-to-back meetings increase stress by 13% and reduce engagement by 20% (Microsoft research)',
          action: `Add 5-10 minute gaps after ${b2bCount} consecutive meetings.`,
          steps: [
            'Identify chains of back-to-back meetings in calendar',
            'Shorten meetings by 5-10 minutes to create buffer',
            'Use "speedy meetings" setting (25/50 min instead of 30/60)',
            'Leave gaps empty - no need to schedule break events'
          ]
        });
      }
      
      if (meetingShare > 50) {
        recommendations.push({
          urgency: 3,
          category: 'Meetings',
          icon: '📉',
          title: 'Reduce Overall Meeting Load',
          problem: `Meetings consume ${meetingShare}% of work time (healthy: <40%)`,
          impact: 'Excessive meetings reduce deep work time and increase context switching',
          action: 'Decline, delegate, or convert meetings to async communication.',
          steps: [
            'Review recurring meetings - decline optional ones',
            'Suggest email updates instead of status meetings',
            'Batch similar meetings on specific days',
            `Target: Reduce meeting time by ${Math.round(meetingShare - 40)}%`
          ]
        });
      }
    }
    
    // Focus blocks
    if (scoreData.details.focus_blocks && scoreData.details.focus_blocks.score < 70) {
      const focusHours = scoreData.weekly_stats?.focus_hours || 0;
      recommendations.push({
        urgency: 3,
        category: 'Focus',
        icon: '🎯',
        title: 'Protect Deep Work Time',
        problem: `Only ${focusHours}h of uninterrupted focus time this week`,
        impact: 'Deep work blocks (90+ min) are 3x more productive than fragmented time',
        action: 'Schedule 2-3 hour blocks for focused work without interruptions.',
        steps: [
          'Block 2-3 hour windows for priority work',
          'Turn off notifications during focus blocks',
          'Decline meetings during peak productivity hours',
          'Aim for at least 15-20h of deep work per week'
        ]
      });
    }
    
    // Work-life balance
    if (scoreData.details.work_life_balance && scoreData.details.work_life_balance.score < 70) {
      const workHours = scoreData.weekly_stats?.total_work_hours || 0;
      const personalHours = scoreData.details.work_life_balance.personal_time_hours || 0;
      
      recommendations.push({
        urgency: 2,
        category: 'Balance',
        icon: '⚖️',
        title: 'Improve Work-Life Balance',
        problem: `${workHours}h work vs ${personalHours}h personal time this week`,
        impact: 'Imbalance leads to burnout, reduced creativity, and health issues',
        action: 'Reduce work hours or increase personal time allocation.',
        steps: [
          `Schedule ${Math.max(5 - personalHours, 0).toFixed(1)}h more personal events`,
          'Set hard stop time for work (e.g., 6 PM)',
          'Block personal time as "busy" to prevent work creep',
          'Target: At least 5-10h personal time per week'
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
      <div className="health-modal-overlay" onClick={onClose}>
        <div className="health-modal-content" onClick={e => e.stopPropagation()}>
        <div className="health-modal-header">
          <h2>📊 Scheduling Health Score</h2>
          <div className="health-header-buttons">
            <button className="health-guide-btn" onClick={() => setGuideOpen(true)} title="Help & Guide">
              ❓
            </button>
            <button className="health-close-btn" onClick={onClose}>×</button>
          </div>
        </div>
        
        {loading && (
          <div className="health-loading">
            <div className="spinner"></div>
            <p>Calculating health score...</p>
          </div>
        )}
        
        {error && (
          <div className="health-error">
            <p>⚠️ {error}</p>
            <button onClick={fetchHealthScore}>Retry</button>
          </div>
        )}
        
        {!loading && !error && scoreData && (
          <>
            {/* Week Navigation */}
            <div className="health-week-nav">
              <button onClick={() => setWeekOffset(weekOffset - 1)}>← Previous</button>
              <span className="health-week-label">
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
              <div className={`health-score-circle ${getScoreColor(scoreData.score)}`}>
                <span className="score-value">{scoreData.score}</span>
                <span className="score-label">/ 100</span>
                <span className="score-description">{getScoreLabel(scoreData.score)}</span>
              </div>
              
              {/* 5 Metric Bars */}
              <div className="health-metrics">
                <MetricBar 
                  label="Work/Life Balance" 
                  score={scoreData.breakdown.work_life} 
                  weight={25}
                  details={scoreData.details.work_life}
                />
                <MetricBar 
                  label="Sleep Respect" 
                  score={scoreData.breakdown.sleep_respect} 
                  weight={20}
                  details={scoreData.details.sleep_respect}
                />
                <MetricBar 
                  label="Focus Blocks" 
                  score={scoreData.breakdown.focus_blocks} 
                  weight={20}
                  details={scoreData.details.focus_blocks}
                />
                <MetricBar 
                  label="Meeting Load" 
                  score={scoreData.breakdown.meetings} 
                  weight={15}
                  details={scoreData.details.meetings}
                />
                <MetricBar 
                  label="Recovery Time" 
                  score={scoreData.breakdown.recovery} 
                  weight={20}
                  details={scoreData.details.recovery}
                />
              </div>
            </div>
            
            {/* Weekly Stats Summary */}
            <div className="health-stats-summary">
              <h3>📈 Weekly Summary</h3>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-value">{scoreData.weekly_stats.total_work_hours}h</span>
                  <span className="stat-label">Total Work</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{scoreData.weekly_stats.focus_hours}h</span>
                  <span className="stat-label">Deep Focus</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{scoreData.weekly_stats.meeting_hours}h</span>
                  <span className="stat-label">Meetings</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{scoreData.weekly_stats.long_days}</span>
                  <span className="stat-label">Long Days (&gt;10h)</span>
                </div>
              </div>
            </div>
            
            {/* Manual Recommendations Section */}
            <div className="health-actions">
              <h3>🎯 Top Priority Recommendations</h3>
              
              {recommendations.length > 0 ? (
                <>
                  <p className="actions-subtitle">Manual actions you should take to improve your schedule health</p>
                  
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
                <p className="no-recommendations">✅ Excellent! Your schedule is well-balanced. No urgent actions needed.</p>
              )}
            </div>
            
            {/* Combined Additional Insights Section */}
            {((scoreData.issues && scoreData.issues.length > 0) || 
              (scoreData.suggestions && scoreData.suggestions.length > 0)) && (
              <div className="health-additional-insights">
                <h4>📋 Additional Insights & Suggestions</h4>
                <p className="insights-subtitle">Other health considerations not covered in top priorities</p>
                
                {scoreData.issues && scoreData.issues.length > 0 && (
                  <div className="insights-subsection">
                    <strong>Issues detected:</strong>
                    {scoreData.issues.map((issue, i) => (
                      <div key={i} className="insight-item">• {issue}</div>
                    ))}
                  </div>
                )}
                
                {scoreData.suggestions && scoreData.suggestions.length > 0 && (
                  <div className="insights-subsection">
                    <strong>Improvement suggestions:</strong>
                    {scoreData.suggestions.map((sug, i) => (
                      <div key={i} className="insight-item">• {sug}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Science Badge */}
            <div className="health-science-badge">
              <small>✨ Based on 16 peer-reviewed studies (WHO, Microsoft, UCI, AASM, NASA)</small>
            </div>
          </>
        )}
      </div>
    </div>

    {/* User Guide Modal */}
    <GuideModal 
      isOpen={guideOpen}
      onClose={() => setGuideOpen(false)}
      guideType="health"
    />
    </>
  );
}

function MetricBar({ label, score, weight, details }) {
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
          if (key === 'score') return null; // Skip score in details
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
        <div className="metric-label-row">
          <span className="metric-label">{label}</span>
          <span className="metric-weight">({weight}%)</span>
        </div>
        <span className="metric-score">{score}</span>
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
