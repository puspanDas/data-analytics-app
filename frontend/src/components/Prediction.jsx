import React, { useState, useEffect } from 'react';

// Using window.Plotly and global scope is not ideal in React, but we need to rely on the backend state.
// We can fetch feature info from the backend, but since the original relied on a previously trained model
// in the same session, we will just present a form based on all non-target columns.
// A more robust app would explicitly return `trained_features` from `/train_model` and pass it down.
// Since we don't have global state, we'll just fetch `/feature_info` if we need it, or 
// approximate it using all columns. 

const Prediction = ({ dataInfo, sessionId }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);
  
  // Create a dynamic form state
  const [formData, setFormData] = useState({});

  useEffect(() => {
    // Initialize form with empty strings for all columns (excluding target is tricky without knowing it, 
    // so we just show all. Users will have to fill features.)
    const initial = {};
    if (dataInfo?.columns) {
      dataInfo.columns.forEach(col => {
        initial[col] = '';
      });
    }
    setFormData(initial);
  }, [dataInfo]);

  const handleChange = (col, value) => {
    setFormData(prev => ({ ...prev, [col]: value }));
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    if (!sessionId) return;
    
    setIsLoading(true);
    setError(null);
    setPrediction(null);
    
    try {
      const payload = {
        session_id: sessionId,
        features: {}
      };

      // Type conversion
      for (const col of Object.keys(formData)) {
        if (formData[col] !== '') {
          if (!dataInfo.categorical_columns.includes(col) && !dataInfo.datetime_columns?.includes(col)) {
            payload.features[col] = parseFloat(formData[col]);
            if (isNaN(payload.features[col])) {
              throw new Error(`Invalid number for ${col}`);
            }
          } else {
            payload.features[col] = formData[col];
          }
        }
      }

      const response = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      
      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to predict');
      }
      
      setPrediction(data.prediction);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl mb-6">Make Prediction</h2>
      <p className="text-muted mb-4">
        A model must be trained first in the "Model Training" tab. Fill in the feature values below.
      </p>

      <form onSubmit={handlePredict} className="glass-panel mb-8">
        <div className="grid grid-cols-3 gap-4 mb-6">
          {dataInfo?.columns.map(col => {
            const isCat = dataInfo.categorical_columns.includes(col);
            const isDate = dataInfo.datetime_columns?.includes(col);
            return (
              <div key={col} className="form-group mb-0">
                <label className="form-label">{col}</label>
                {isDate ? (
                  <input
                    type="datetime-local"
                    className="form-input"
                    value={formData[col] || ''}
                    onChange={e => handleChange(col, e.target.value)}
                  />
                ) : (
                  <input
                    type={isCat ? "text" : "number"}
                    step="any"
                    className="form-input"
                    placeholder={isCat ? "(Categorical)" : "(Numeric)"}
                    value={formData[col] || ''}
                    onChange={e => handleChange(col, e.target.value)}
                  />
                )}
              </div>
            );
          })}
        </div>

        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {isLoading ? 'Predicting...' : 'Predict'}
        </button>
      </form>

      {error && (
        <div className="glass-panel text-error mb-6" style={{ borderLeft: '4px solid var(--color-error)' }}>
          {error}
        </div>
      )}

      {prediction && (
        <div className="glass-panel animate-fade-in">
          <h3 className="text-xl mb-4 text-primary">Prediction Result</h3>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--color-secondary)' }}>
            {JSON.stringify(prediction, null, 2)}
          </div>
          <div className="mt-4 flex gap-4">
             <button className="btn btn-secondary" onClick={() => window.location.href = `/export?session_id=${sessionId}&type=prediction&format=csv`}>
               Export CSV
             </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Prediction;
