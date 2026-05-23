import React, { useState } from 'react';

const ModelComparison = ({ dataInfo, sessionId }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // In the original, it used the target and features from the ModelTraining tab.
  // Here, we'll give it its own selectors for safety, defaulting to first column.
  const [targetColumn, setTargetColumn] = useState(dataInfo?.columns[0] || '');
  const [testSize, setTestSize] = useState(0.2);

  const handleCompare = async (e) => {
    e.preventDefault();
    if (!sessionId) return;

    // By default, use all other columns as features
    const features = dataInfo?.columns.filter(c => c !== targetColumn) || [];
    
    if (features.length === 0) {
      setError('Not enough columns for comparison.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch('/compare_models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          target_column: targetColumn,
          feature_columns: features,
          test_size: parseFloat(testSize)
        })
      });
      const data = await response.json();
      
      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to compare models');
      }
      
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl mb-6">Compare Models</h2>
      <p className="text-muted mb-4">
        This will train SVM, Random Forest, and XGBoost on the data to compare performance.
      </p>

      <form onSubmit={handleCompare} className="glass-panel mb-8">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="form-group mb-0">
            <label className="form-label">Target Column</label>
            <select className="form-select" value={targetColumn} onChange={e => setTargetColumn(e.target.value)}>
              {dataInfo?.columns.map(col => <option key={col} value={col}>{col}</option>)}
            </select>
          </div>
          <div className="form-group mb-0">
            <label className="form-label">Test Size: {testSize}</label>
            <input 
              type="range" 
              min="0.1" max="0.5" step="0.05" 
              value={testSize} 
              onChange={e => setTestSize(e.target.value)}
              style={{ width: '100%', accentColor: 'var(--color-primary)' }}
            />
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={isLoading} style={{ width: '100%' }}>
          {isLoading ? 'Running Comparison...' : 'Run Comparison'}
        </button>
      </form>

      {error && (
        <div className="glass-panel text-error mb-6" style={{ borderLeft: '4px solid var(--color-error)' }}>
          {error}
        </div>
      )}

      {results && (
        <div className="glass-panel animate-fade-in">
          <h3 className="text-xl mb-4 text-primary">Comparison Results</h3>
          <div style={{ overflowX: 'auto' }}>
            <pre style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
              {JSON.stringify(results, null, 2)}
            </pre>
          </div>
        </div>
      )}
      
      {isLoading && (
        <div className="flex justify-center mt-6">
          <div className="spinner"></div>
        </div>
      )}
    </div>
  );
};

export default ModelComparison;
