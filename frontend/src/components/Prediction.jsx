import React, { useState, useEffect } from 'react';

const Prediction = ({ dataInfo, sessionId }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);
  
  // Dynamic form state
  const [formData, setFormData] = useState({});

  // Auto-fill state
  const [searchColumn, setSearchColumn] = useState('');
  const [searchValue, setSearchValue] = useState('');
  const [autoFillLoading, setAutoFillLoading] = useState(false);
  const [autoFillError, setAutoFillError] = useState(null);
  const [autoFillSuccess, setAutoFillSuccess] = useState(false);

  useEffect(() => {
    const initial = {};
    if (dataInfo?.columns) {
      dataInfo.columns.forEach(col => {
        initial[col] = '';
      });
      // Default search column to first column
      if (!searchColumn && dataInfo.columns.length > 0) {
        setSearchColumn(dataInfo.columns[0]);
      }
    }
    setFormData(initial);
  }, [dataInfo]);

  const handleChange = (col, value) => {
    setFormData(prev => ({ ...prev, [col]: value }));
  };

  const handleAutoFill = async () => {
    if (!sessionId || !searchColumn || !searchValue.trim()) {
      setAutoFillError('Please select a column and enter a value to search.');
      return;
    }

    setAutoFillLoading(true);
    setAutoFillError(null);
    setAutoFillSuccess(false);

    try {
      const response = await fetch('/get_sample_row', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          search_column: searchColumn,
          search_value: searchValue.trim()
        })
      });
      const data = await response.json();

      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to find matching row');
      }

      // Populate the form with the returned row data
      const row = data.row;
      const newFormData = {};
      if (dataInfo?.columns) {
        dataInfo.columns.forEach(col => {
          if (row[col] !== undefined && row[col] !== null) {
            newFormData[col] = String(row[col]);
          } else {
            newFormData[col] = '';
          }
        });
      }
      setFormData(newFormData);
      setAutoFillSuccess(true);
      // Auto-clear the success message after 3 seconds
      setTimeout(() => setAutoFillSuccess(false), 3000);
    } catch (err) {
      setAutoFillError(err.message);
    } finally {
      setAutoFillLoading(false);
    }
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

      {/* ── Auto-Fill Section ── */}
      <div className="glass-panel mb-8" style={{ borderLeft: '4px solid var(--color-primary)' }}>
        <h3 className="text-lg mb-4" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.25rem' }}>⚡</span> Auto-fill from Dataset
        </h3>
        <p className="text-muted mb-4" style={{ fontSize: '0.875rem' }}>
          Select a column and enter a value to automatically fill the entire form with matching data from your dataset.
        </p>
        <div className="grid grid-cols-3 gap-4 mb-4" style={{ alignItems: 'flex-end' }}>
          <div className="form-group mb-0">
            <label className="form-label">Search Column</label>
            <select
              className="form-select"
              value={searchColumn}
              onChange={e => setSearchColumn(e.target.value)}
            >
              {dataInfo?.columns.map(col => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>
          <div className="form-group mb-0">
            <label className="form-label">Value</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. USA, 12345, John..."
              value={searchValue}
              onChange={e => setSearchValue(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAutoFill(); } }}
            />
          </div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleAutoFill}
            disabled={autoFillLoading}
            style={{ height: 'fit-content' }}
          >
            {autoFillLoading ? 'Searching...' : '⚡ Auto-fill Form'}
          </button>
        </div>

        {autoFillError && (
          <div className="text-error" style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
            {autoFillError}
          </div>
        )}
        {autoFillSuccess && (
          <div className="text-success" style={{ fontSize: '0.875rem', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span>✓</span> Form auto-filled successfully! Review the values below and click Predict.
          </div>
        )}
      </div>

      {/* ── Prediction Form ── */}
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

      {prediction !== null && (
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
