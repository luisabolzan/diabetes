import React from 'react';
import { Card, Input, Button } from './UI';

export const SettingsView = ({ settings, setSettings }) => {

    const handleChange = (key, val) => {
        setSettings(prev => ({ ...prev, [key]: parseFloat(val) }));
    };

    return (
        <div className="pb-24 animate-fade-in">
            <h2 className="text-2xl font-bold text-cyan-400 mb-6 px-2">Configuration</h2>

            <Card className="mb-6">
                <h3 className="text-lg font-semibold text-slate-200 mb-4 border-b border-slate-700 pb-2">Insulin-to-Carb Ratios</h3>
                <div className="grid grid-cols-2 gap-4">
                    <Input label="Breakfast (1:x)" value={settings.icr_breakfast} onChange={v => handleChange('icr_breakfast', v)} />
                    <Input label="Lunch (1:x)" value={settings.icr_lunch} onChange={v => handleChange('icr_lunch', v)} />
                    <Input label="Dinner (1:x)" value={settings.icr_dinner} onChange={v => handleChange('icr_dinner', v)} />
                    <Input label="Snack (1:x)" value={settings.icr_snack} onChange={v => handleChange('icr_snack', v)} />
                </div>
            </Card>

            <Card className="mb-6">
                <h3 className="text-lg font-semibold text-slate-200 mb-4 border-b border-slate-700 pb-2">Personal Factors</h3>
                <Input label="Weight (kg)" value={settings.weight} onChange={v => handleChange('weight', v)} />
                <Input label="ISF (1u drops X mg/dL)" value={settings.isf} onChange={v => handleChange('isf', v)} />
                <Input label="Target Glucose (mg/dL)" value={settings.target_glucose} onChange={v => handleChange('target_glucose', v)} />
                <Input label="Correction Threshold (mg/dL)" value={settings.correction_threshold} onChange={v => handleChange('correction_threshold', v)} />
            </Card>

            <Card>
                <h3 className="text-lg font-semibold text-slate-200 mb-4 border-b border-slate-700 pb-2">Activity Modifiers</h3>
                <div className="grid grid-cols-2 gap-4">
                    <Input label="Gym" value={settings.mod_gym} onChange={v => handleChange('mod_gym', v)} />
                    <Input label="Run" value={settings.mod_run} onChange={v => handleChange('mod_run', v)} />
                    <Input label="Swim" value={settings.mod_swim} onChange={v => handleChange('mod_swim', v)} />
                    <Input label="Beach Tennis" value={settings.mod_beach_tennis} onChange={v => handleChange('mod_beach_tennis', v)} />
                </div>
            </Card>
        </div>
    );
};
