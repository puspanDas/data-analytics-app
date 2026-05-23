import React, { useState, useEffect } from 'react';

const ModelTraining = ({ dataInfo, sessionId }) => {
  const [targetColumn, setTargetColumn] = useState('');
  const [modelType, setModelType] = useState('random_forest');
  const [testSize, setTestSize] = useState(0.2);
  const [selectedFeatures, setSelectedFeatures] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Initialize selected features to true for all except target
  useEffect(() => {
    if (dataInfo?.columns && targetColumn) {
      const initialFeatures = {};
      dataInfo.columns.forEach(col => {
        if (col !== targetColumn) {
          initialFeatures[col] = true;
        }
      });
      setSelectedFeatures(initialFeatures);
    }
  }, [targetColumn, dataInfo]);

  // Set initial target
  useEffect(() => {
    if (dataInfo?.columns && !targetColumn) {
      setTargetColumn(dataInfo.columns[0]);
    }
  }, [dataInfo, targetColumn]);

  const handleFeatureToggle = (col) => {
    setSelectedFeatures(prev => ({ ...prev, [col]: !prev[col] }));
  };

  const handleTrain = async (e) => {
    e.preventDefault();
    if (!sessionId) return;

    const features = Object.keys(selectedFeatures).filter(k => selectedFeatures[k]);
    if (features.length === 0) {
      setError('Please select at least one feature column.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch('/train_model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          target_column: targetColumn,
          feature_columns: features,
          test_size: parseFloat(testSize),
          model_type: modelType
        })
      });
      const data = await response.json();
      
      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to train model');
      }
      
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl mb-6">Train a Model</h2>

      <form onSubmit={handleTrain} className="glass-panel mb-8">
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="form-group">
            <label className="form-label">Target Column (Y)</label>
            <select className="form-select" value={targetColumn} onChange={e => setTargetColumn(e.target.value)}>
              {dataInfo?.columns.map(col => <option key={col} value={col}>{col}</option>)}
            </select>
          </div>
          
          <div className="form-group">
            <label className="form-label">Model Type</label>
            <select className="form-select" value={modelType} onChange={e => setModelType(e.target.value)}>
              <option value="random_forest">Random Forest</option>
              <option value="xgboost">XGBoost</option>
              <option value="lightgbm">LightGBM (Fastest)</option>
              <option value="svm">SVM</option>
            </select>
          </div>
        </div>

        <div className="form-group mb-6">
          <label className="form-label flex justify-between">
            <span>Test Size: {testSize}</span>
          </label>
          <input 
            type="range" 
            min="0.1" max="0.5" step="0.05" 
            value={testSize} 
            onChange={e => setTestSize(e.target.value)}
            style={{ width: '100%', accentColor: 'var(--color-primary)' }}
          />
        </div>

        <div className="form-group mb-6">
          <label className="form-label">Feature Columns (X)</label>
          <div className="grid grid-cols-3 gap-2" style={{ maxHeight: '200px', overflowY: 'auto', padding: '1rem', background: 'rgba(0,0,0,0.1)', borderRadius: 'var(--radius-md)' }}>
            {Object.keys(selectedFeatures).map(col => (
              <label key={col} className="flex items-center gap-2" style={{ fontSize: '0.875rem', cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  checked={selectedFeatures[col]} 
                  onChange={() => handleFeatureToggle(col)} 
                  style={{ accentColor: 'var(--color-primary)', width: '16px', height: '16px' }}
                />
                {col}
              </label>
            ))}
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={isLoading} style={{ width: '100%' }}>
          {isLoading ? 'Training...' : 'Train Model'}
        </button>
      </form>

      {error && (
        <div className="glass-panel text-error mb-6" style={{ borderLeft: '4px solid var(--color-error)' }}>
          {error}
        </div>
      )}

      {results && (
        <div className="glass-panel animate-fade-in">
          <h3 className="text-xl mb-4 text-primary">Training Results</h3>
          <p className="mb-6 text-lg">
            Problem Type: <span className="font-bold text-secondary capitalize">{results.problem_type}</span> <br/>
            {results.problem_type === 'classification' ? 'Accuracy' : 'R² Score'}: <span className="font-bold text-success">{(results.accuracy * (results.problem_type === 'classification' ? 100 : 1)).toFixed(2)}{results.problem_type === 'classification' ? '%' : ''}</span>
          </p>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="text-lg mb-2">Evaluation Plot</h4>
              <img src={`data:image/png;base64,${results.evaluation_plot}`} alt="Evaluation" style={{ maxWidth: '100%', borderRadius: 'var(--radius-md)' }} />
            </div>
            
            <div style={{ overflowX: 'auto' }}>
              <h4 className="text-lg mb-2">Report</h4>
              <pre style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-md)', fontSize: '0.875rem', overflowX: 'auto' }}>
                {JSON.stringify(results.classification_report, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelTraining;
