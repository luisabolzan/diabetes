import React from 'react';

export const Card = ({ children, className = "" }) => (
    <div className={`glass-panel ${className}`}>
        {children}
    </div>
);

export const Button = ({ children, onClick, className = "", secondary = false, danger = false }) => {
    let baseClass = "bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold py-3 px-6 rounded-xl w-full shadow-lg transition-transform active:scale-95";

    if (secondary) {
        baseClass = "bg-slate-700 text-slate-200 py-3 px-6 rounded-xl w-full hover:bg-slate-600 transition-colors";
    }
    if (danger) {
        baseClass = "bg-red-500/20 text-red-300 border border-red-500/50 py-2 px-4 rounded-lg w-full hover:bg-red-500/30 transition-colors";
    }

    return (
        <button onClick={onClick} className={`${baseClass} ${className}`}>
            {children}
        </button>
    );
};

export const Input = ({ label, type = "number", value, onChange, placeholder = "" }) => (
    <div className="mb-4">
        <label className="block text-slate-400 text-sm font-bold mb-2">{label}</label>
        <input
            type={type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full bg-slate-800/50 border border-slate-700 rounded-lg py-3 px-4 text-white focus:outline-none focus:border-cyan-500 transition-colors"
        />
    </div>
);

export const Select = ({ label, options, value, onChange }) => (
    <div className="mb-4">
        <label className="block text-slate-400 text-sm font-bold mb-2">{label}</label>
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full bg-slate-800/50 border border-slate-700 rounded-lg py-3 px-4 text-white focus:outline-none focus:border-cyan-500 appearance-none"
        >
            {options.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
            ))}
        </select>
    </div>
);
