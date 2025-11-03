import React from 'react';
import './PreviewModal.css';

export default function PreviewModal({ 
  isOpen, 
  onClose, 
  previewData, 
  onApply, 
  onCancel,
  applying 
}) {
  if (!isOpen || !previewData) return null;

  const { action, modifications, score_improvement, recommendations } = previewData;
  
  const healthDelta = score_improvement?.health?.delta || 0;
  const prodDelta = score_improvement?.productivity?.delta || 0;
  
  const formatDateTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const dayName = dayNames[date.getDay()];
    const month = monthNames[date.getMonth()];
    const day = date.getDate();
    const hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    const displayMinutes = minutes.toString().padStart(2, '0');
    
    return `${dayName}, ${month} ${day} at ${displayHours}:${displayMinutes} ${ampm}`;
  };
  
  const getActionTitle = (action) => {
    const titles = {
      'consolidate_schedule': 'Consolidate Schedule',
      'group_deep_work': 'Group Deep Work',
      'add_planning_buffer': 'Add Planning Buffers',
      'reduce_meeting_load': 'Reduce Meeting Load',
      'add_recovery_time': 'Add Recovery Time',
      'fix_sleep_schedule': 'Fix Sleep Schedule'
    };
    return titles[action] || action;
  };
  
  const getDeltaColor = (delta) => {
    if (delta > 0) return '#4caf50';
    if (delta < 0) return '#f44336';
    return '#666';
  };
  
  const getDeltaSymbol = (delta) => {
    if (delta > 0) return '+';
    if (delta < 0) return '';
    return '';
  };

  return (
    <div className="preview-modal-overlay" onClick={onCancel}>
      <div className="preview-modal-content" onClick={e => e.stopPropagation()}>
        <div className="preview-modal-header">
          <h2>🔍 Preview: {getActionTitle(action)}</h2>
          <button className="preview-close-btn" onClick={onCancel}>×</button>
        </div>
        
        {applying ? (
          <div className="preview-loading">
            <div className="spinner"></div>
            <p>Applying optimization...</p>
          </div>
        ) : (
          <>
            {/* Score Impact */}
            <div className="preview-score-impact">
              <h3>📊 Predicted Score Changes</h3>
              <div className="score-changes">
                <div className="score-change">
                  <span className="score-label">Health:</span>
                  <span className="score-values">
                    {score_improvement.health.before} → {score_improvement.health.after}
                    <span 
                      className="score-delta" 
                      style={{ color: getDeltaColor(healthDelta) }}
                    >
                      ({getDeltaSymbol(healthDelta)}{healthDelta})
                    </span>
                  </span>
                </div>
                <div className="score-change">
                  <span className="score-label">Productivity:</span>
                  <span className="score-values">
                    {score_improvement.productivity.before} → {score_improvement.productivity.after}
                    <span 
                      className="score-delta" 
                      style={{ color: getDeltaColor(prodDelta) }}
                    >
                      ({getDeltaSymbol(prodDelta)}{prodDelta})
                    </span>
                  </span>
                </div>
              </div>
              
              {healthDelta === 0 && prodDelta === 0 && (
                <p className="no-improvement-note">
                  ℹ️ No score improvement predicted. Your schedule may already be optimal for this metric.
                </p>
              )}
            </div>
            
            {/* Modifications */}
            {modifications && modifications.length > 0 && (
              <div className="preview-modifications">
                <h3>📝 Proposed Changes ({modifications.length})</h3>
                <div className="modifications-list">
                  {modifications.map((mod, index) => (
                    <div key={index} className="modification-item">
                      <div className="mod-title">
                        <strong>{mod.title}</strong>
                      </div>
                      <div className="mod-times">
                        <div className="mod-time old">
                          <span className="time-label">Current:</span>
                          <span className="time-value">{formatDateTime(mod.old_start)}</span>
                        </div>
                        <div className="mod-arrow">→</div>
                        <div className="mod-time new">
                          <span className="time-label">New:</span>
                          <span className="time-value">{formatDateTime(mod.new_start)}</span>
                        </div>
                      </div>
                      {mod.reason && (
                        <div className="mod-reason">
                          <em>{mod.reason}</em>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Recommendations */}
            {recommendations && recommendations.length > 0 && (
              <div className="preview-recommendations">
                <h3>💡 Recommendations</h3>
                <ul>
                  {recommendations.map((rec, index) => (
                    <li key={index}>
                      <strong>{rec.action}:</strong> {rec.reason}
                    </li>
                  ))}
                </ul>
                <p className="rec-note">
                  <small>ℹ️ Recommendations are suggestions only and won't be applied automatically.</small>
                </p>
              </div>
            )}
            
            {/* No changes */}
            {(!modifications || modifications.length === 0) && (!recommendations || recommendations.length === 0) && (
              <div className="preview-no-changes">
                <p>✅ No changes needed. Your schedule is already optimized for this action!</p>
              </div>
            )}
            
            {/* Recommendations only (no modifications) */}
            {(!modifications || modifications.length === 0) && recommendations && recommendations.length > 0 && (
              <div className="preview-recommendations-only">
                <p>💡 This optimization provides recommendations for manual review rather than automatic changes.</p>
                <p className="rec-subtitle">Review the recommendations above and make changes manually in your calendar.</p>
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="preview-actions">
              <button 
                className="preview-btn cancel-btn" 
                onClick={onCancel}
                disabled={applying}
              >
                {(!modifications || modifications.length === 0) ? 'Close' : 'Cancel'}
              </button>
              <button 
                className="preview-btn apply-btn" 
                onClick={onApply}
                disabled={applying || (!modifications || modifications.length === 0)}
              >
                {modifications && modifications.length > 0 
                  ? `Apply ${modifications.length} Change${modifications.length > 1 ? 's' : ''}`
                  : 'No Changes to Apply'
                }
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
