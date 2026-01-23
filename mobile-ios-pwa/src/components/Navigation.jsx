import React from 'react';

export const Navigation = ({ activeTab, onTabChange }) => {
    const tabs = [
        { id: 'calculator', label: 'Calculator', icon: '🧮' },
        { id: 'history', label: 'History', icon: 'mb:list' },
        { id: 'settings', label: 'Settings', icon: '⚙️' },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-slate-900/90 backdrop-blur-lg border-t border-slate-800 pb-safe pt-2 px-6 flex justify-between items-center z-50">
            {tabs.map((tab) => (
                <button
                    key={tab.id}
                    onClick={() => onTabChange(tab.id)}
                    className={`flex flex-col items-center p-2 min-w-[64px] rounded-lg transition-colors ${activeTab === tab.id ? 'text-cyan-400' : 'text-slate-500'
                        }`}
                    style={{ background: 'transparent', boxShadow: 'none' }} // Override default button style
                >
                    <span className="text-xl mb-1">{tab.icon === 'mb:list' ? '📜' : tab.icon}</span>
                    <span className="text-xs font-medium">{tab.label}</span>
                </button>
            ))}
        </div>
    );
};
