import React, { useState, useEffect, useRef } from 'react';

const BIDashboard = ({ dataInfo, sessionId }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const chartRef = useRef(null);
  
  const [dimensions, setDimensions] = useState([]);
  const [measures, setMeasures] = useState([]);
  const [aggregations, setAggregations] = useState({});
  const [chartType, setChartType] = useState('auto');
  const [timeDimension, setTimeDimension] = useState('');
  const [timeFrequency, setTimeFrequency] = useState('M');

  // Multi-select handler
  const handleSelect = (e, setter) => {
    const values = Array.from(e.target.selectedOptions, option => option.value);
    setter(values);
  };

  // When measures change, initialize aggregations
  useEffect(() => {
    const newAggs = { ...aggregations };
    measures.forEach(m => {
      if (!newAggs[m]) newAggs[m] = 'sum';
    });
    setAggregations(newAggs);
  }, [measures]);

  const handleAggregate = async (e) => {
    e.preventDefault();
    if (!sessionId) return;
    if (measures.length === 0 || (dimensions.length === 0 && !timeDimension)) {
      setError('Must select at least one Measure and at least one Dimension (or Time Dimension).');
      return;
    }

    setIsLoading(true);
    setError(null);

    const payload = {
      session_id: sessionId,
      dimensions: dimensions,
      measures: measures,
      aggregations: aggregations,
      time_dimension: timeDimension || null,
      time_frequency: timeDimension ? timeFrequency : null,
      chart_type: chartType
    };

    try {
      const response = await fetch('/aggregate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      
      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to aggregate');
      }
      
      renderChart(data.data, payload);
    } catch (err) {
      setError(err.message);
      if (window.Plotly && chartRef.current) {
        window.Plotly.purge(chartRef.current);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const renderChart = (data, settings) => {
    if (!window.Plotly || !chartRef.current) return;
    
    window.Plotly.purge(chartRef.current);
    
    if (data.length === 0) {
      setError('Query returned no data.');
      return;
    }

    const { dimensions, measures, time_dimension, chart_type } = settings;
    const measure = measures[0]; // Simplification for MVP
    let plotData = [];
    let layout = {
        title: 'BI Chart',
        xaxis: { title: 'Category' },
        yaxis: { title: measure },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: 'var(--color-text)' }
    };

    const xKey = time_dimension || (dimensions.length > 0 ? dimensions[0] : null);
    if (!xKey) {
        setError('Could not determine chart type. Please select a dimension.');
        return;
    }
    
    layout.xaxis.title = xKey;

    let type = 'bar';
    let mode = null;
    let fill = null;
    
    if (chart_type === 'auto') {
        if (time_dimension) {
            type = 'scatter';
            mode = 'lines+markers';
        } else if (dimensions.length === 1) {
            type = 'bar';
        } else {
            type = 'bar';
            layout.barmode = 'group';
        }
    } else {
        if (chart_type === 'line') { type = 'scatter'; mode = 'lines+markers'; }
        else if (chart_type === 'bar') { type = 'bar'; }
        else if (chart_type === 'pie') { type = 'pie'; }
        else if (chart_type === 'area') { type = 'scatter'; mode = 'lines'; fill = 'tozeroy'; }
        else if (chart_type === 'scatter') { type = 'scatter'; mode = 'markers'; }
    }

    if (type === 'pie') {
        layout.title = `${measure} by ${xKey}`;
        plotData.push({
            values: data.map(row => row[measure]),
            labels: data.map(row => row[xKey]),
            type: 'pie',
            name: measure
        });
    } else if (dimensions.length <= 1 || (time_dimension && dimensions.length === 0)) {
        layout.title = `${measure} by ${xKey}`;
        plotData.push({
            x: data.map(row => row[xKey]),
            y: data.map(row => row[measure]),
            type: type,
            mode: mode,
            fill: fill,
            name: measure
        });
    } else {
        const groupKey = time_dimension ? dimensions[0] : dimensions[1];
        layout.title = `${measure} by ${xKey}, grouped by ${groupKey}`;
        if (type === 'bar') layout.barmode = 'group';
        
        const groups = [...new Set(data.map(row => row[groupKey]))];
        groups.forEach(group => {
            const groupData = data.filter(row => row[groupKey] === group);
            plotData.push({
                x: groupData.map(row => row[xKey]),
                y: groupData.map(row => row[measure]),
                type: type,
                mode: mode,
                fill: fill,
                name: group
            });
        });
        layout.showlegend = true;
    }
    
    window.Plotly.newPlot(chartRef.current, plotData, layout, {responsive: true});
  };

  const timeCandidates = Array.from(new Set([...(dataInfo?.datetime_columns || []), ...(dataInfo?.columns || [])]));

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl mb-6">BI Dashboard</h2>

      <form onSubmit={handleAggregate} className="glass-panel mb-8">
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="form-group mb-0">
            <label className="form-label">Dimensions</label>
            <select multiple className="form-select" style={{ height: '120px' }} value={dimensions} onChange={(e) => handleSelect(e, setDimensions)}>
              {dataInfo?.columns.map(col => <option key={col} value={col}>{col}</option>)}
            </select>
          </div>
          
          <div className="form-group mb-0">
            <label className="form-label">Measures</label>
            <select multiple className="form-select" style={{ height: '120px' }} value={measures} onChange={(e) => handleSelect(e, setMeasures)}>
              {dataInfo?.numeric_columns.map(col => <option key={col} value={col}>{col}</option>)}
            </select>
          </div>

          <div className="form-group mb-0" style={{ gridColumn: 'span 2', maxHeight: '120px', overflowY: 'auto' }}>
            <label className="form-label">Measure Aggregations</label>
            {measures.length === 0 ? (
              <p className="text-sm text-muted">Select measures to see aggregation options.</p>
            ) : (
              measures.map(m => (
                <div key={m} className="flex gap-2 mb-2 items-center">
                  <span className="text-sm" style={{ width: '50%' }}>{m}:</span>
                  <select 
                    className="form-select" 
                    style={{ padding: '0.25rem' }}
                    value={aggregations[m] || 'sum'}
                    onChange={e => setAggregations({...aggregations, [m]: e.target.value})}
                  >
                    {['sum', 'mean', 'count', 'min', 'max', 'nunique'].map(f => <option key={f} value={f}>{f}</option>)}
                  </select>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="form-group mb-0">
            <label className="form-label">Chart Type</label>
            <select className="form-select" value={chartType} onChange={e => setChartType(e.target.value)}>
              <option value="auto">Auto (Recommended)</option>
              <option value="line">Line Chart</option>
              <option value="bar">Bar Chart</option>
              <option value="pie">Pie Chart</option>
              <option value="area">Area Chart</option>
              <option value="scatter">Scatter Plot</option>
            </select>
          </div>

          <div className="form-group mb-0">
            <label className="form-label">Time Dimension (Optional)</label>
            <select className="form-select" value={timeDimension} onChange={e => setTimeDimension(e.target.value)}>
              <option value="">None</option>
              {timeCandidates.map(col => <option key={col} value={col}>{col}</option>)}
            </select>
          </div>

          {timeDimension && (
            <div className="form-group mb-0">
              <label className="form-label">Time Frequency</label>
              <select className="form-select" value={timeFrequency} onChange={e => setTimeFrequency(e.target.value)}>
                <option value="D">Daily</option>
                <option value="W">Weekly</option>
                <option value="M">Monthly</option>
                <option value="Q">Quarterly</option>
                <option value="Y">Yearly</option>
              </select>
            </div>
          )}
        </div>

        <button type="submit" className="btn btn-primary" disabled={isLoading} style={{ width: '100%' }}>
          {isLoading ? 'Generating Chart...' : 'Generate Chart'}
        </button>
      </form>

      {error && (
        <div className="glass-panel text-error mb-6" style={{ borderLeft: '4px solid var(--color-error)' }}>
          {error}
        </div>
      )}

      <div className="glass-panel" style={{ minHeight: '400px' }}>
        <div ref={chartRef} style={{ width: '100%', height: '100%' }}></div>
      </div>
    </div>
  );
};

export default BIDashboard;
