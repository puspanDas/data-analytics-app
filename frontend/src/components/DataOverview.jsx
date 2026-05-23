import React from 'react';

const DataOverview = ({ dataInfo, sessionId }) => {
  if (!dataInfo) return null;

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl mb-6">Data Overview</h2>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="glass-panel">
          <h3 className="text-lg text-primary mb-2">Dataset Shape</h3>
          <p className="text-2xl font-bold">{dataInfo.shape[0]} <span className="text-sm font-normal text-muted">rows</span></p>
          <p className="text-2xl font-bold">{dataInfo.shape[1]} <span className="text-sm font-normal text-muted">columns</span></p>
        </div>
        
        <div className="glass-panel">
          <h3 className="text-lg text-primary mb-2">Data Quality</h3>
          <p className="mb-1">Fully Empty Rows: <span className="font-bold">{dataInfo.row_quality?.fully_empty_count || 0}</span></p>
          <p>Any NaN Rows: <span className="font-bold">{dataInfo.row_quality?.any_nan_count || 0}</span></p>
        </div>
      </div>

      <div className="glass-panel mb-6">
        <h3 className="text-lg text-primary mb-4">Columns</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {dataInfo.columns.map((col) => (
            <span key={col} style={{ 
              background: 'rgba(255,255,255,0.1)', 
              padding: '0.25rem 0.75rem', 
              borderRadius: '999px',
              fontSize: '0.875rem'
            }}>
              {col} <span className="text-muted ml-1 text-xs">({dataInfo.dtypes[col]})</span>
            </span>
          ))}
        </div>
      </div>

      <div className="glass-panel overflow-x-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg text-primary">First 5 Rows</h3>
          <div className="flex gap-4">
            <button className="btn btn-secondary" onClick={() => window.location.href = `/export?session_id=${sessionId}&type=raw&format=csv`}>
              Export CSV
            </button>
          </div>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              {dataInfo.columns.map(col => (
                <th key={col} style={{ padding: '0.75rem 1rem', color: 'var(--color-text-muted)', fontWeight: 500 }}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataInfo.first_few_rows.map((row, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                {dataInfo.columns.map(col => (
                  <td key={col} style={{ padding: '0.75rem 1rem' }}>{row[col] !== null ? String(row[col]) : 'N/A'}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataOverview;
