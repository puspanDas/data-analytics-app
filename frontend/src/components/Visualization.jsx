import React, { useState } from 'react';

const Visualization = ({ dataInfo, sessionId }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [plotUrl, setPlotUrl] = useState(null);
  const [error, setError] = useState(null);
  
  const [plotType, setPlotType] = useState('histogram');
  const [xCol, setXCol] = useState(dataInfo?.columns[0] || '');
  const [yCol, setYCol] = useState(dataInfo?.columns[0] || '');

  const handlePlot = async (e) => {
    e.preventDefault();
    if (!sessionId) return;
    
    setIsLoading(true);
    setError(null);
    setPlotUrl(null);
    
    try {
      const response = await fetch('/visualize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          plot_type: plotType,
          x_col: xCol,
          y_col: yCol
        })
      });
      const data = await response.json();
      
      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to generate plot');
      }
      
      setPlotUrl(`data:image/png;base64,${data.plot_url}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl mb-6">Create Visualizations</h2>
      
      <form onSubmit={handlePlot} className="glass-panel mb-8 grid grid-cols-2 gap-4">
        <div className="form-group">
          <label className="form-label">Plot Type</label>
          <select className="form-select" value={plotType} onChange={e => setPlotType(e.target.value)}>
            <option value="histogram">Histogram</option>
            <option value="scatter">Scatter Plot</option>
            <option value="boxplot">Box Plot</option>
            <option value="correlation">Correlation Matrix</option>
            <option value="pairplot">Pair Plot</option>
            <option value="strip">Strip Plot</option>
          </select>
        </div>
        
        <div className="form-group">
          <label className="form-label">X-Axis Column</label>
          <select className="form-select" value={xCol} onChange={e => setXCol(e.target.value)}>
            {dataInfo?.columns.map(col => <option key={col} value={col}>{col}</option>)}
          </select>
        </div>
        
        <div className="form-group" style={{ gridColumn: 'span 2' }}>
          <label className="form-label">Y-Axis Column (if applicable)</label>
          <select className="form-select" value={yCol} onChange={e => setYCol(e.target.value)}>
            {dataInfo?.columns.map(col => <option key={col} value={col}>{col}</option>)}
          </select>
        </div>
        
        <div style={{ gridColumn: 'span 2' }}>
          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            {isLoading ? 'Generating...' : 'Generate Plot'}
          </button>
        </div>
      </form>

      {error && (
        <div className="glass-panel text-error mb-6" style={{ borderLeft: '4px solid var(--color-error)' }}>
          {error}
        </div>
      )}

      {plotUrl && (
        <div className="glass-panel flex justify-center mt-6">
          <img src={plotUrl} alt="Visualization" style={{ maxWidth: '100%', borderRadius: 'var(--radius-md)' }} />
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

export default Visualization;
