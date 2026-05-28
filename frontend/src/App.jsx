import { useState } from 'react';
import './index.css';
import FileUpload from './components/FileUpload';
import Tabs from './components/Tabs';
import DataOverview from './components/DataOverview';
import BIDashboard from './components/BIDashboard';
import Visualization from './components/Visualization';
import ModelTraining from './components/ModelTraining';
import ModelComparison from './components/ModelComparison';
import Prediction from './components/Prediction';
import DataFixBanner from './components/DataFixBanner';
import AICopilot from './components/AICopilot';

function App() {
  const [sessionData, setSessionData] = useState(null);
  const [activeTab, setActiveTab] = useState('data-overview');
  const [message, setMessage] = useState({ text: '', isError: false, visible: false });

  // Lifted states shared with AI Copilot for diagnostics checking
  const [biDimensions, setBiDimensions] = useState([]);
  const [biMeasures, setBiMeasures] = useState([]);
  const [biTimeDimension, setBiTimeDimension] = useState('');
  const [biTimeFrequency, setBiTimeFrequency] = useState('ME');
  
  const [trainTarget, setTrainTarget] = useState('');
  const [trainFeatures, setTrainFeatures] = useState({});

  const showMessage = (text, isError = false) => {
    setMessage({ text, isError, visible: true });
    setTimeout(() => {
      setMessage((prev) => ({ ...prev, visible: false }));
    }, 5000);
  };

  const handleUploadSuccess = (data) => {
    setSessionData(data);
    showMessage('File uploaded and analyzed successfully!');
    setActiveTab('data-overview');
  };

  const handleFixApplied = (fixData) => {
    // Update sessionData with the fixed data_info while preserving session_id
    setSessionData((prev) => ({
      ...prev,
      data_info: fixData.data_info,
      diagnosis: fixData.diagnosis,
    }));
    showMessage(`Data fixed successfully! ${fixData.fixes_applied.length} fix(es) applied.`);
  };

  const tabs = [
    { id: 'data-overview', label: 'Data Overview' },
    { id: 'bi-dashboard', label: 'BI Dashboard' },
    { id: 'visualization', label: 'Visualization' },
    { id: 'training', label: 'Model Training' },
    { id: 'comparison', label: 'Model Comparison' },
    { id: 'prediction', label: 'Make Prediction' },
  ];

  return (
    <div className="container animate-fade-in">
      <header className="mb-8 text-center">
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--color-text)' }}>
          AutoML Analysis <span className="text-primary">&</span> Prediction
        </h1>
        <p className="text-muted mt-2 text-lg">
          Upload your data to visualize, train models, and get predictions instantly.
        </p>
      </header>

      {message.visible && (
        <div 
          className="glass-panel" 
          style={{ 
            position: 'fixed', top: '20px', right: '20px', zIndex: 50,
            borderLeft: `4px solid var(--color-${message.isError ? 'error' : 'success'})`
          }}
        >
          <p style={{ color: message.isError ? 'var(--color-error)' : 'var(--color-success)' }}>
            {message.text}
          </p>
        </div>
      )}

      <div className="glass-panel mb-8">
        <h2 className="mb-4 text-xl">1. Upload Your Data</h2>
        <FileUpload onUploadSuccess={handleUploadSuccess} onError={showMessage} />
      </div>

      {sessionData && (
        <main>
          {/* Smart Data Fixer Banner */}
          <DataFixBanner
            diagnosis={sessionData.diagnosis}
            sessionId={sessionData.session_id}
            onFixApplied={handleFixApplied}
          />

          <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
          
          <div className="mt-8">
            {activeTab === 'data-overview' && <DataOverview dataInfo={sessionData.data_info} sessionId={sessionData.session_id} />}
            {activeTab === 'bi-dashboard' && (
              <BIDashboard 
                dataInfo={sessionData.data_info} 
                sessionId={sessionData.session_id} 
                dimensions={biDimensions}
                setDimensions={setBiDimensions}
                measures={biMeasures}
                setMeasures={setBiMeasures}
                timeDimension={biTimeDimension}
                setTimeDimension={setBiTimeDimension}
                timeFrequency={biTimeFrequency}
                setTimeFrequency={setBiTimeFrequency}
              />
            )}
            {activeTab === 'visualization' && <Visualization dataInfo={sessionData.data_info} sessionId={sessionData.session_id} />}
            {activeTab === 'training' && (
              <ModelTraining 
                dataInfo={sessionData.data_info} 
                sessionId={sessionData.session_id} 
                targetColumn={trainTarget}
                setTargetColumn={setTrainTarget}
                selectedFeatures={trainFeatures}
                setSelectedFeatures={setTrainFeatures}
              />
            )}
            {activeTab === 'comparison' && <ModelComparison dataInfo={sessionData.data_info} sessionId={sessionData.session_id} />}
            {activeTab === 'prediction' && <Prediction dataInfo={sessionData.data_info} sessionId={sessionData.session_id} />}
          </div>
        </main>
      )}

      {sessionData && (
        <AICopilot
          sessionId={sessionData.session_id}
          dataInfo={sessionData.data_info}
          activeTab={activeTab}
          targetColumn={trainTarget}
          selectedFeatures={trainFeatures}
          dimensions={biDimensions}
          measures={biMeasures}
          timeDimension={biTimeDimension}
          timeFrequency={biTimeFrequency}
        />
      )}
    </div>
  );
}

export default App;
