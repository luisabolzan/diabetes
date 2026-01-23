import { useState } from 'react';
import { usePersistentState } from './hooks/usePersistentState';
import { Navigation } from './components/Navigation';
import { CalculatorView } from './components/CalculatorView';
import { HistoryView } from './components/HistoryView';
import { SettingsView } from './components/SettingsView';
import './styles/index.css';

function App() {
  const [activeTab, setActiveTab] = useState('calculator');

  // Default Settings
  const defaultSettings = {
    icr_breakfast: 10.0,
    icr_lunch: 15.0,
    icr_dinner: 20.0,
    icr_snack: 15.0,
    isf: 50.0,
    target_glucose: 90,
    correction_threshold: 120,
    weight: 70.0,
    mod_gym: 0.10,
    mod_run: -0.30,
    mod_swim: -0.30,
    mod_beach_tennis: -0.20,
    mod_stress: 0.20,
    mod_anxious: 0.10
  };

  const [settings, setSettings] = usePersistentState('diabetes-settings', defaultSettings);
  const [logs, setLogs] = usePersistentState('diabetes-logs', []);

  const handleSaveLog = (newLog) => {
    setLogs([newLog, ...logs]);
    setActiveTab('history');
  };

  return (
    <div className="app-container">
      <header className="app-header mb-4">
        <h1 className="text-2xl">Diabetes Manager</h1>
        <p className="subtitle text-xs">Local PWA Mode</p>
      </header>

      <main className="main-content flex-1 overflow-y-auto w-full max-w-lg mx-auto pb-24">
        {activeTab === 'calculator' && (
          <CalculatorView settings={settings} logs={logs} onSaveLog={handleSaveLog} />
        )}
        {activeTab === 'history' && (
          <HistoryView logs={logs} setLogs={setLogs} />
        )}
        {activeTab === 'settings' && (
          <SettingsView settings={settings} setSettings={setSettings} />
        )}
      </main>

      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}

export default App;
