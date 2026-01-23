import React, { useState, useEffect } from 'react';
import { useProfile } from './hooks/useProfile';
import { useLogs } from './hooks/useLogs';
import { Navigation } from './components/Navigation';
import { CalculatorView } from './components/CalculatorView';
import { HistoryView } from './components/HistoryView';
import { SettingsView } from './components/SettingsView';
import { AuthView } from './components/AuthView';
import { supabase } from './lib/supabase';
import './styles/index.css';

function App() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    // Listen for changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  const [activeTab, setActiveTab] = useState('calculator');

  // Shared State for Calculator Interaction
  const [sharedCarbs, setSharedCarbs] = useState(0);

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

  const { settings, updateSettings } = useProfile(session, defaultSettings);
  const { logs, addLog, deleteLog } = useLogs(session);

  const handleSaveLog = (newLog) => {
    addLog(newLog);
    setActiveTab('history');
    setSharedCarbs(0); // Reset after save
  };

  const handleCommitMeal = (totalCarbs) => {
    setSharedCarbs(totalCarbs);
    setActiveTab('calculator');
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-cyan-400">Loading...</div>;
  }

  if (!session) {
    return <AuthView />;
  }

  return (
    <div className="app-container">
      <header className="app-header mb-4 flex justify-between items-center px-6 pt-4">
        <div>
          <h1 className="text-2xl">Diabetes Manager</h1>
          <p className="subtitle text-xs truncate max-w-[200px]">{session.user.email}</p>
        </div>
        <button onClick={handleSignOut} className="text-xs text-red-400 border border-red-500/30 px-2 py-1 rounded hover:bg-red-500/20">
          Sign Out
        </button>
      </header>

      <main className="main-content flex-1 overflow-y-auto w-full max-w-lg mx-auto pb-24 px-6 no-scrollbar">
        {activeTab === 'calculator' && (
          <CalculatorView
            settings={settings}
            logs={logs}
            onSaveLog={handleSaveLog}
            initialCarbs={sharedCarbs}
            setSharedCarbs={setSharedCarbs}
          />
        )}
        {activeTab === 'history' && (
          <HistoryView logs={logs} deleteLog={deleteLog} />
        )}
        {activeTab === 'settings' && (
          <SettingsView settings={settings} setSettings={updateSettings} />
        )}
      </main>

      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}

export default App;
