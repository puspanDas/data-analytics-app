import React, { useState, useEffect, useRef } from 'react';

const AICopilot = ({ 
  sessionId, 
  dataInfo, 
  activeTab,
  targetColumn,
  selectedFeatures,
  dimensions,
  measures,
  timeDimension,
  timeFrequency
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [warnings, setWarnings] = useState([]);
  const [hasUnread, setHasUnread] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Focus input when drawer opens
  useEffect(() => {
    if (isOpen) {
      setHasUnread(false);
      setTimeout(() => inputRef.current?.focus(), 400);
    }
  }, [isOpen]);

  // Format timestamp
  const getTimestamp = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Initial greeting message when dataset loads
  useEffect(() => {
    if (dataInfo) {
      const rows = dataInfo.shape?.[0] || 0;
      const cols = dataInfo.shape?.[1] || 0;
      setMessages([
        {
          sender: 'ai',
          text: `Hello! I'm your **AI Copilot** — your intelligent AutoML guide.\n\nI've analyzed your dataset: it contains **${rows.toLocaleString()}** rows and **${cols}** columns.\n\nHow can I help you today? I can assist with data visualization, BI dashboards, model training, and predictions.`,
          time: getTimestamp()
        }
      ]);
    } else {
      setMessages([
        {
          sender: 'ai',
          text: "Hello! I'm your **AI Copilot**. Please upload a dataset so I can analyze it and guide you through your analytics journey!",
          time: getTimestamp()
        }
      ]);
    }
  }, [dataInfo]);

  // Periodic static analyzer (runs whenever activeTab or selections change)
  useEffect(() => {
    if (!sessionId) return;
    
    const checkState = async () => {
      // Calculate features array
      const features = Object.keys(selectedFeatures || {}).filter(k => selectedFeatures[k]);
      
      const payload = {
        session_id: sessionId,
        message: "", // Empty message to trigger diagnostics check only
        active_tab: activeTab,
        target_column: targetColumn,
        selected_features: features,
        selected_dimensions: dimensions,
        selected_measures: measures,
        time_dimension: timeDimension,
        time_frequency: timeFrequency
      };

      try {
        const response = await fetch('/ai_chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
          console.warn('AI diagnostics: non-OK response', response.status);
          return;
        }
        
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
          console.warn('AI diagnostics: unexpected content type', contentType);
          return;
        }

        const data = await response.json();
        if (data.success) {
          // Client-side + backend warning aggregation
          const localWarnings = [];
          
          // Data Leakage check
          if (activeTab === 'training' && targetColumn && selectedFeatures && selectedFeatures[targetColumn]) {
            localWarnings.push({
              type: 'data-leakage',
              title: 'Data Leakage Alert',
              message: `You selected target column '${targetColumn}' in the Feature checklist. This gives the model the answers, causing 100% false accuracy. Please uncheck it!`
            });
          }

          // Combine with backend warnings (high cardinality, etc.)
          const allWarnings = [...localWarnings, ...(data.warnings || [])];
          setWarnings(allWarnings);
        }
      } catch (err) {
        console.error("AI diagnostics fetch error:", err);
      }
    };

    // Debounce state checks to avoid flooding the backend
    const timer = setTimeout(checkState, 600);
    return () => clearTimeout(timer);
  }, [sessionId, activeTab, targetColumn, selectedFeatures, dimensions, measures, timeDimension, timeFrequency]);

  const handleSendMessage = async (text) => {
    const msg = text || inputText;
    if (!msg.trim()) return;

    // Add user message to chat
    setMessages(prev => [...prev, { sender: 'user', text: msg, time: getTimestamp() }]);
    setInputText('');
    setIsTyping(true);

    const features = Object.keys(selectedFeatures || {}).filter(k => selectedFeatures[k]);
    const payload = {
      session_id: sessionId,
      message: msg,
      active_tab: activeTab,
      target_column: targetColumn,
      selected_features: features,
      selected_dimensions: dimensions,
      selected_measures: measures,
      time_dimension: timeDimension,
      time_frequency: timeFrequency
    };

    try {
      const response = await fetch('/ai_chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        throw new Error('Server returned non-JSON response. The AI service may be unavailable.');
      }

      const data = await response.json();
      
      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to communicate with AI');
      }

      // Simulate typing effect for AI response
      setIsTyping(false);
      setMessages(prev => [...prev, { sender: 'ai', text: data.reply, time: getTimestamp() }]);
      
      // Mark unread if drawer is closed
      if (!isOpen) setHasUnread(true);
      
      // Update warnings if diagnostics came back
      if (data.warnings) {
        setWarnings(data.warnings);
      }
    } catch (err) {
      setIsTyping(false);
      setMessages(prev => [...prev, { sender: 'ai', text: `Sorry, I encountered an error: ${err.message}`, time: getTimestamp() }]);
    }
  };

  // Simple markdown-like rendering: bold, newlines, code
  const renderFormattedText = (text) => {
    if (!text) return '';
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.*?)`/g, '<code class="ai-inline-code">$1</code>')
      .replace(/\n/g, '<br/>');
    return html;
  };

  const getQuickActionChips = () => {
    switch (activeTab) {
      case 'bi-dashboard':
        return [
          { icon: "📊", text: "How to set up BI Dashboard?" },
          { icon: "📐", text: "Explain dimensions & measures" },
          { icon: "🔀", text: "Suggest a grouping dimension" }
        ];
      case 'visualization':
        return [
          { icon: "📈", text: "Which chart should I use?" },
          { icon: "🔗", text: "Explain correlation plot" },
          { icon: "📉", text: "What is a strip plot?" }
        ];
      case 'training':
        return [
          { icon: "🔍", text: "Check my settings for errors" },
          { icon: "🏆", text: "Which model is best?" },
          { icon: "⚠️", text: "What is data leakage?" }
        ];
      case 'comparison':
        return [
          { icon: "📋", text: "How to read comparison scores?" },
          { icon: "⚡", text: "SVM vs XGBoost" },
          { icon: "🎯", text: "What is overfitting?" }
        ];
      case 'prediction':
        return [
          { icon: "🎲", text: "How to make predictions?" },
          { icon: "📊", text: "Explain feature stats" }
        ];
      default:
        return [
          { icon: "🚀", text: "Help me get started" },
          { icon: "🔧", text: "Check my dataset for issues" },
          { icon: "✨", text: "What features are available?" }
        ];
    }
  };

  // AI Avatar SVG
  const AiAvatar = () => (
    <div className="ai-avatar ai-avatar-bot">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/>
        <path d="M20 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M4 21v-2a4 4 0 0 1 3-3.87"/>
        <circle cx="12" cy="17" r="4"/>
        <path d="M12 13v4"/>
        <path d="M10 17h4"/>
      </svg>
    </div>
  );

  const UserAvatar = () => (
    <div className="ai-avatar ai-avatar-user">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    </div>
  );

  return (
    <div className="ai-copilot-container">
      {/* Backdrop overlay when drawer is open */}
      <div 
        className={`ai-copilot-backdrop ${isOpen ? 'visible' : ''}`} 
        onClick={() => setIsOpen(false)}
      />

      {/* Floating Glowing Button */}
      <button 
        className={`ai-copilot-btn ${warnings.length > 0 ? 'has-warning' : ''} ${isOpen ? 'is-active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title={warnings.length > 0 ? `AI Advisor detected ${warnings.length} issues!` : 'Open AI Copilot'}
        aria-label="Open AI Copilot"
      >
        <svg className="ai-copilot-btn-icon" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
        </svg>
        {(warnings.length > 0 || hasUnread) && (
          <span className="ai-copilot-badge">
            {warnings.length > 0 ? warnings.length : ''}
          </span>
        )}
      </button>

      {/* Sliding Chat Drawer */}
      <div className={`ai-copilot-drawer ${isOpen ? 'open' : ''}`}>
        {/* Gradient Header */}
        <div className="ai-drawer-header">
          <div className="ai-drawer-title-container">
            <div className="ai-drawer-title">
              <div className="ai-header-icon-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
                </svg>
              </div>
              <span>AI Copilot</span>
            </div>
            <div className="ai-status-indicator">
              <span className="ai-status-dot"></span>
              <span>Online &middot; Ready to assist</span>
            </div>
          </div>
          <button className="ai-drawer-close-btn" onClick={() => setIsOpen(false)} title="Close AI Copilot" aria-label="Close AI Copilot">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Real-time Warnings Banner */}
        {warnings.length > 0 && (
          <div className="ai-warnings-container">
            <div className="ai-warnings-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <span>{warnings.length} issue{warnings.length > 1 ? 's' : ''} detected</span>
            </div>
            {warnings.map((warn, i) => (
              <div key={i} className="ai-warning-card">
                <div className="ai-warning-title">{warn.title}</div>
                <div className="ai-warning-message">{warn.message}</div>
              </div>
            ))}
          </div>
        )}

        {/* Chat Messages */}
        <div className="ai-chat-messages">
          {messages.map((m, i) => (
            <div key={i} className={`ai-message-wrapper ${m.sender}`}>
              <div className="ai-message-row">
                {m.sender === 'ai' && <AiAvatar />}
                <div className="ai-message-content">
                  <div 
                    className="ai-chat-bubble" 
                    dangerouslySetInnerHTML={{ __html: renderFormattedText(m.text) }} 
                  />
                  <span className="ai-message-time">{m.time}</span>
                </div>
                {m.sender === 'user' && <UserAvatar />}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="ai-message-wrapper ai">
              <div className="ai-message-row">
                <AiAvatar />
                <div className="ai-message-content">
                  <div className="ai-chat-bubble">
                    <div className="ai-typing-indicator">
                      <span className="ai-typing-dot"></span>
                      <span className="ai-typing-dot"></span>
                      <span className="ai-typing-dot"></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        <div className="ai-suggestions-bar">
          {getQuickActionChips().map((chip, idx) => (
            <button 
              key={idx} 
              className="ai-suggest-chip"
              onClick={() => handleSendMessage(chip.text)}
            >
              <span className="ai-chip-icon">{chip.icon}</span>
              <span>{chip.text}</span>
            </button>
          ))}
        </div>

        {/* Chat Input Box */}
        <div className="ai-chat-footer">
          <div className="ai-input-wrapper">
            <input 
              ref={inputRef}
              type="text" 
              className="ai-chat-input"
              placeholder="Ask anything about your data..."
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }}}
            />
            <button 
              className={`ai-btn-send ${inputText.trim() ? 'active' : ''}`} 
              onClick={() => handleSendMessage()}
              disabled={!inputText.trim()}
              aria-label="Send message"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
          <div className="ai-footer-hint">
            Press <kbd>Enter</kbd> to send
          </div>
        </div>
      </div>
    </div>
  );
};

export default AICopilot;
