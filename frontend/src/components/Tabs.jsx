import React from 'react';

const Tabs = ({ tabs, activeTab, onTabChange }) => {
  return (
    <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid var(--color-border)', overflowX: 'auto', paddingBottom: '2px' }}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.75rem 1rem',
            fontSize: '0.95rem',
            fontWeight: activeTab === tab.id ? 600 : 500,
            color: activeTab === tab.id ? 'var(--color-primary)' : 'var(--color-text-muted)',
            borderBottom: activeTab === tab.id ? '2px solid var(--color-primary)' : '2px solid transparent',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            whiteSpace: 'nowrap'
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};

export default Tabs;
