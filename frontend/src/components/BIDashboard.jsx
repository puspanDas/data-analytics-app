import React, { useState, useEffect, useRef } from 'react';

const BIDashboard = ({ 
  dataInfo, 
  sessionId,
  dimensions: propsDimensions,
  setDimensions: propsSetDimensions,
  measures: propsMeasures,
  setMeasures: propsSetMeasures,
  timeDimension: propsTimeDimension,
  setTimeDimension: propsSetTimeDimension,
  timeFrequency: propsTimeFrequency,
  setTimeFrequency: propsSetTimeFrequency
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const chartRef = useRef(null);
  
  // Lifted state fallbacks
  const [localDimensions, localSetDimensions] = useState([]);
  const dimensions = propsDimensions !== undefined ? propsDimensions : localDimensions;
  const setDimensions = propsSetDimensions !== undefined ? propsSetDimensions : localSetDimensions;

  const [localMeasures, localSetMeasures] = useState([]);
  const measures = propsMeasures !== undefined ? propsMeasures : localMeasures;
  const setMeasures = propsSetMeasures !== undefined ? propsSetMeasures : localSetMeasures;

  const [localTimeDimension, localSetTimeDimension] = useState('');
  const timeDimension = propsTimeDimension !== undefined ? propsTimeDimension : localTimeDimension;
  const setTimeDimension = propsSetTimeDimension !== undefined ? propsSetTimeDimension : localSetTimeDimension;

  const [localTimeFrequency, localSetTimeFrequency] = useState('ME');
  const timeFrequency = propsTimeFrequency !== undefined ? propsTimeFrequency : localTimeFrequency;
  const setTimeFrequency = propsSetTimeFrequency !== undefined ? propsSetTimeFrequency : localSetTimeFrequency;

  const [aggregations, setAggregations] = useState({});
  const [chartType, setChartType] = useState('auto');
  const [isDragOver, setIsDragOver] = useState(false);

  // Drag & drop handlers
  const handleDragStart = (e, col) => {
    e.dataTransfer.setData('text/plain', col);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const colName = e.dataTransfer.getData('text/plain');
    if (colName && !measures.includes(colName)) {
      addMeasure(colName);
    }
  };

  const addMeasure = (colName) => {
    if (measures.includes(colName)) return;
    const isNumeric = dataInfo?.numeric_columns?.includes(colName);
    setMeasures([...measures, colName]);
    setAggregations(prev => ({
      ...prev,
      [colName]: isNumeric ? 'sum' : 'count'
    }));
  };

  const removeMeasure = (colName) => {
    setMeasures(measures.filter(m => m !== colName));
    const newAggs = { ...aggregations };
    delete newAggs[colName];
    setAggregations(newAggs);
  };

  const toggleDimension = (colName) => {
    if (dimensions.includes(colName)) {
      setDimensions(dimensions.filter(d => d !== colName));
    } else {
      setDimensions([...dimensions, colName]);
    }
  };

  // When measures change, initialize/update aggregations safely
  useEffect(() => {
    const newAggs = { ...aggregations };
    let changed = false;
    measures.forEach(m => {
      if (!newAggs[m]) {
        const isNumeric = dataInfo?.numeric_columns?.includes(m);
        newAggs[m] = isNumeric ? 'sum' : 'count';
        changed = true;
      }
    });
    // Remove aggregations for measures that are no longer selected
    Object.keys(newAggs).forEach(k => {
      if (!measures.includes(k)) {
        delete newAggs[k];
        changed = true;
      }
    });
    if (changed) {
      setAggregations(newAggs);
    }
  }, [measures, dataInfo]);

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
    
    const colorsPalette = [
      '#3b82f6', // primary blue
      '#8b5cf6', // secondary violet
      '#06b6d4', // cyan
      '#ec4899', // pink
      '#10b981', // green
      '#f59e0b', // warning orange/amber
      '#6366f1'  // indigo
    ];

    let plotData = [];
    
    const xKey = time_dimension || (dimensions.length > 0 ? dimensions[0] : null);
    if (!xKey) {
        setError('Could not determine chart type. Please select a dimension.');
        return;
    }

    let layout = {
        title: {
            text: `${measure} by ${xKey}`,
            font: { color: '#f8fafc', size: 16, family: "'Inter', sans-serif" }
        },
        xaxis: {
            title: {
                text: xKey,
                font: { color: '#94a3b8', size: 12, family: "'Inter', sans-serif" }
            },
            tickfont: { color: '#94a3b8', size: 10, family: "'Inter', sans-serif" },
            gridcolor: 'rgba(255, 255, 255, 0.08)',
            zerolinecolor: 'rgba(255, 255, 255, 0.15)'
        },
        yaxis: {
            title: {
                text: measure,
                font: { color: '#94a3b8', size: 12, family: "'Inter', sans-serif" }
            },
            tickfont: { color: '#94a3b8', size: 10, family: "'Inter', sans-serif" },
            gridcolor: 'rgba(255, 255, 255, 0.08)',
            zerolinecolor: 'rgba(255, 255, 255, 0.15)'
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#f8fafc', family: "'Inter', sans-serif" },
        legend: {
            font: { color: '#f8fafc', size: 10, family: "'Inter', sans-serif" },
            bgcolor: 'rgba(15, 23, 42, 0.6)',
            bordercolor: 'rgba(255, 255, 255, 0.1)',
            borderwidth: 1
        },
        margin: { t: 50, b: 60, l: 60, r: 20 }
    };

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
        layout.title.text = `${measure} by ${xKey}`;
        plotData.push({
            values: data.map(row => row[measure]),
            labels: data.map(row => row[xKey]),
            type: 'pie',
            name: measure,
            marker: {
                colors: colorsPalette
            },
            textinfo: 'percent+label',
            insidetextorientation: 'radial'
        });
    } else if (dimensions.length <= 1 || (time_dimension && dimensions.length === 0)) {
        layout.title.text = `${measure} by ${xKey}`;
        
        let trace = {
            x: data.map(row => row[xKey]),
            y: data.map(row => row[measure]),
            type: type,
            mode: mode,
            fill: fill,
            name: measure
        };
        
        if (type === 'bar') {
            trace.marker = {
                color: 'rgba(59, 130, 246, 0.7)',
                line: {
                    color: '#60a5fa',
                    width: 1.5
                }
            };
        } else if (type === 'scatter') {
            trace.marker = { color: '#3b82f6', size: 8 };
            trace.line = { color: '#3b82f6', width: 2.5 };
        }
        
        plotData.push(trace);
    } else {
        const groupKey = time_dimension ? dimensions[0] : dimensions[1];
        layout.title.text = `${measure} by ${xKey}, grouped by ${groupKey}`;
        if (type === 'bar') layout.barmode = 'group';
        
        const groups = [...new Set(data.map(row => row[groupKey]))];
        groups.forEach((group, idx) => {
            const groupData = data.filter(row => row[groupKey] === group);
            const color = colorsPalette[idx % colorsPalette.length];
            
            let trace = {
                x: groupData.map(row => row[xKey]),
                y: groupData.map(row => row[measure]),
                type: type,
                mode: mode,
                fill: fill,
                name: String(group)
            };
            
            if (type === 'bar') {
                trace.marker = {
                    color: color + 'cc', // 80% opacity
                    line: {
                        color: color,
                        width: 1.5
                    }
                };
            } else if (type === 'scatter') {
                trace.marker = { color: color, size: 8 };
                trace.line = { color: color, width: 2.5 };
            }
            
            plotData.push(trace);
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
        <div className="dd-container">
          {/* Dimensions / Available Fields */}
          <div className="dd-column">
            <div className="dd-column-title">
              <span>Dimensions / Fields</span>
              <span className="text-muted text-xs">Click to select group-by</span>
            </div>
            <div className="dd-list">
              {(dataInfo?.columns || []).map(col => {
                const isActive = dimensions.includes(col);
                const isNumeric = dataInfo?.numeric_columns?.includes(col);
                const isDatetime = dataInfo?.datetime_columns?.includes(col) || timeCandidates.includes(col);
                
                let typeIcon = 'A';
                let typeClass = 'dd-type-categorical';
                if (isNumeric) {
                  typeIcon = '#';
                  typeClass = 'dd-type-numeric';
                } else if (isDatetime) {
                  typeIcon = '🕒';
                  typeClass = 'dd-type-datetime';
                }

                return (
                  <div
                    key={col}
                    draggable
                    onDragStart={(e) => handleDragStart(e, col)}
                    onClick={() => toggleDimension(col)}
                    className={`dd-item ${isActive ? 'is-active' : ''}`}
                    title="Drag to Measures or click to toggle as Dimension"
                  >
                    <div className="dd-item-left">
                      <span className="dd-handle">⋮⋮</span>
                      <span className={`dd-type-icon ${typeClass}`}>{typeIcon}</span>
                      <span className="dd-item-name">{col}</span>
                    </div>
                    <div className="dd-item-actions" onClick={(e) => e.stopPropagation()}>
                      <button
                        type="button"
                        onClick={() => addMeasure(col)}
                        className="dd-btn-icon"
                        title="Add to Measures"
                      >
                        ＋
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Measures Drop Target */}
          <div className="dd-column">
            <div className="dd-column-title">
              <span>Measures / Aggregations</span>
              <span className="text-muted text-xs">Drag fields here</span>
            </div>
            
            {measures.length === 0 ? (
              <div
                className={`dd-dropzone ${isDragOver ? 'is-dragover' : ''}`}
                onDragOver={handleDragOver}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="dd-dropzone-icon">📥</div>
                <p className="text-xs text-muted mb-0">Drag columns here or click ＋ to analyze them as measures</p>
              </div>
            ) : (
              <div
                className={`dd-list ${isDragOver ? 'is-dragover' : ''}`}
                onDragOver={handleDragOver}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                style={{ minHeight: '100%' }}
              >
                {measures.map(m => {
                  const isNumeric = dataInfo?.numeric_columns?.includes(m);
                  // Numeric allows all aggregations. Non-numeric allows count, nunique, min, max.
                  const allowedAggs = isNumeric 
                    ? ['sum', 'mean', 'count', 'min', 'max', 'nunique'] 
                    : ['count', 'nunique', 'min', 'max'];

                  return (
                    <div key={m} className="dd-item dd-measure-card" onClick={(e) => e.stopPropagation()}>
                      <div className="dd-item-left">
                        <span className="dd-type-icon dd-type-numeric">∑</span>
                        <span className="dd-item-name">{m}</span>
                      </div>
                      
                      <div className="dd-item-actions">
                        <select
                          className="dd-measure-select"
                          value={aggregations[m] || (isNumeric ? 'sum' : 'count')}
                          onChange={e => setAggregations({ ...aggregations, [m]: e.target.value })}
                        >
                          {allowedAggs.map(f => (
                            <option key={f} value={f}>
                              {f.toUpperCase()}
                            </option>
                          ))}
                        </select>
                        
                        <button
                          type="button"
                          onClick={() => removeMeasure(m)}
                          className="dd-btn-icon remove-btn"
                          title="Remove Measure"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
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
                <option value="ME">Monthly</option>
                <option value="QE">Quarterly</option>
                <option value="YE">Yearly</option>
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
