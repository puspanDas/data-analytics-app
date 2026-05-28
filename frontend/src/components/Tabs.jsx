import React from 'react';

const Tabs = ({ tabs, activeTab, onTabChange }) => {
  return (
    <div style={{ 
      display: 'flex', 
      gap: '0.5rem', 
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      overflowX: 'auto', 
      paddingBottom: '0px',
      scrollBehavior: 'smooth',
      WebkitOverflowScrolling: 'touch',
      scrollbarWidth: 'none',
      msOverflowStyle: 'none',
    }}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          style={{
            background: activeTab === tab.id 
              ? 'rgba(59, 130, 246, 0.1)' 
              : 'transparent',
            border: 'none',
            padding: '0.75rem 1.15rem',
            fontSize: '0.9rem',
            fontWeight: activeTab === tab.id ? 600 : 500,
            color: activeTab === tab.id ? '#60a5fa' : 'var(--color-text-muted)',
            borderBottom: activeTab === tab.id 
              ? '2px solid #3b82f6' 
              : '2px solid transparent',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            whiteSpace: 'nowrap',
            borderRadius: '8px 8px 0 0',
            fontFamily: 'inherit',
            letterSpacing: '0.01em',
            flexShrink: 0,
          }}
          onMouseEnter={e => {
            if (activeTab !== tab.id) {
              e.target.style.background = 'rgba(255, 255, 255, 0.04)';
              e.target.style.color = 'var(--color-text)';
            }
          }}
          onMouseLeave={e => {
            if (activeTab !== tab.id) {
              e.target.style.background = 'transparent';
              e.target.style.color = 'var(--color-text-muted)';
            }
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};

export default Tabs;
