import React, { useState } from 'react';

const SEVERITY_ICONS = {
  critical: '🔴',
  warning: '🟡',
  info: '🔵',
};

const DataFixBanner = ({ diagnosis, sessionId, onFixApplied }) => {
  const [isFixing, setIsFixing] = useState(false);
  const [fixResult, setFixResult] = useState(null);
  const [dismissed, setDismissed] = useState(false);

  // Don't render if no issues or already dismissed
  if (!diagnosis || !diagnosis.has_issues || dismissed) {
    // Show success banner if fix was just applied
    if (fixResult) {
      return (
        <div className="data-fix-banner severity-success" id="data-fix-success-banner">
          <div className="data-fix-banner-inner">
            <div className="data-fix-header">
              <div className="data-fix-title">
                <span style={{ fontSize: '1.5rem' }}>✅</span>
                <span>Data Fixed Successfully!</span>
              </div>
              <button
                className="btn btn-secondary"
                style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                onClick={() => setFixResult(null)}
              >
                Dismiss
              </button>
            </div>

            {/* Before / After stats */}
            <div className="fix-result-summary">
              <div className="fix-stat-card">
                <span className="fix-stat-label">Before</span>
                <span className="fix-stat-value">
                  {fixResult.original_shape[0]}×{fixResult.original_shape[1]}
                </span>
              </div>
              <div className="fix-stat-card">
                <span className="fix-stat-label">After</span>
                <span className="fix-stat-value">
                  {fixResult.new_shape[0]}×{fixResult.new_shape[1]}
                </span>
              </div>
              <div className="fix-stat-card">
                <span className="fix-stat-label">Fixes Applied</span>
                <span className="fix-stat-value">{fixResult.fixes_applied.length}</span>
              </div>
            </div>

            {/* List of fixes applied */}
            <div className="fix-applied-list">
              {fixResult.fixes_applied.map((fix, idx) => (
                <div key={idx} className="fix-applied-item">
                  <span>✓</span>
                  <span>{fix}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }
    return null;
  }

  const bannerSeverity = diagnosis.has_critical ? 'critical' : 'warning';

  const handleFix = async () => {
    setIsFixing(true);
    try {
      const response = await fetch('/fix_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
      const data = await response.json();

      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to fix data');
      }

      setFixResult(data);
      setDismissed(true); // Hide the warning banner

      // Notify parent to update data
      if (onFixApplied) {
        onFixApplied(data);
      }
    } catch (err) {
      alert('Error fixing data: ' + (err.message || 'Unknown error'));
    } finally {
      setIsFixing(false);
    }
  };

  return (
    <div className={`data-fix-banner severity-${bannerSeverity}`} id="data-fix-warning-banner">
      <div className="data-fix-banner-inner">
        {/* Header */}
        <div className="data-fix-header">
          <div className="data-fix-title">
            <span className="icon-pulse">⚠️</span>
            <span>Data Structure Issues Detected</span>
            <span className="issue-count-badge">{diagnosis.issue_count}</span>
          </div>
          <button
            className="btn-fix"
            onClick={handleFix}
            disabled={isFixing}
            id="auto-fix-button"
          >
            {isFixing ? (
              <>
                <div className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
                <span>Fixing...</span>
              </>
            ) : (
              <>
                <span>✨</span>
                <span>Auto-Fix Data</span>
              </>
            )}
          </button>
        </div>

        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
          Your file has structural issues that may affect analysis and model predictions.
          Click <strong>"Auto-Fix Data"</strong> to automatically restructure your data into clean rows and columns.
        </p>

        {/* Issue list */}
        <div className="data-fix-issues">
          {diagnosis.issues.map((issue, idx) => (
            <div key={idx} className="data-fix-issue">
              <span className={`severity-badge ${issue.severity}`}>
                {SEVERITY_ICONS[issue.severity] || '⚪'} {issue.severity}
              </span>
              <div className="issue-content">
                <div className="issue-description">{issue.description}</div>
                {issue.detail && (
                  <div className="issue-detail">💡 Fix: {issue.detail}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DataFixBanner;
