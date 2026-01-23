import React, { useState, useEffect } from 'react';
import { Card, Input, Select, Button } from './UI';
import { InsulinCalculator } from '../utils/calculator';

export const CalculatorView = ({ settings, logs, onSaveLog }) => {
    const [glucose, setGlucose] = useState(120);
    const [carbs, setCarbs] = useState(0);
    const [activity, setActivity] = useState('None');
    const [emotion, setEmotion] = useState('Calm');
    const [duration, setDuration] = useState(30);
    const [intensity, setIntensity] = useState('Moderate');
    const [lastDoseMin, setLastDoseMin] = useState(180);

    const [result, setResult] = useState(null);

    // Live status check
    const isPeak = lastDoseMin >= 60 && lastDoseMin <= 120;

    const handleCalculate = () => {
        const calc = new InsulinCalculator(settings);
        const res = calc.calculate_dose(
            parseInt(glucose),
            parseInt(carbs),
            activity,
            emotion,
            logs,
            parseInt(duration),
            intensity,
            settings.weight,
            parseInt(lastDoseMin)
        );
        setResult(res);
    };

    const handleSave = () => {
        if (!result) return;
        onSaveLog({
            timestamp: new Date().toISOString(),
            glucose: parseInt(glucose),
            carbs: parseInt(carbs),
            activity,
            emotion,
            recommended_dose: result.recommended_dose,
            actual_dose: result.recommended_dose // Defaulting to recommended
        });
        setResult(null); // Reset after save
        // Maybe show a toast/notification
    };

    return (
        <div className="pb-24 animate-fade-in">
            <div className="flex justify-center mb-6">
                {isPeak ? (
                    <div className="bg-red-500/20 border border-red-500 rounded-full px-4 py-1 flex items-center gap-2">
                        <span className="text-red-400 font-bold">⚠️ PEAK ACTION</span>
                    </div>
                ) : (
                    <div className="bg-green-500/20 border border-green-500 rounded-full px-4 py-1 flex items-center gap-2">
                        <span className="text-green-400 font-bold">✓ SAFE TAIL</span>
                    </div>
                )}
            </div>

            <h2 className="text-3xl font-bold text-center text-cyan-400 mb-8">Bolus Calculator</h2>

            <Card className="mb-6">
                <div className="grid grid-cols-2 gap-4">
                    <Input label="Glucose (mg/dL)" value={glucose} onChange={setGlucose} />
                    <Input label="Carbs (g)" value={carbs} onChange={setCarbs} />
                </div>
                <Input label="Mins since last dose" value={lastDoseMin} onChange={setLastDoseMin} />
            </Card>

            <div className="mb-2 px-2 text-cyan-200 opacity-80 text-sm font-semibold uppercase tracking-wider">Context</div>
            <Card className="mb-8">
                <Select
                    label="Activity"
                    options={['None', 'Gym/Weights', 'Running', 'Swimming', 'Beach Tennis']}
                    value={activity}
                    onChange={setActivity}
                />
                {activity !== 'None' && (
                    <>
                        <div className="grid grid-cols-2 gap-4">
                            <Input label="Duration (min)" value={duration} onChange={setDuration} />
                            <Select
                                label="Intensity"
                                options={['Slow', 'Moderate', 'Fast']}
                                value={intensity}
                                onChange={setIntensity}
                            />
                        </div>
                    </>
                )}

                <Select
                    label="Emotion"
                    options={['Calm', 'Stress', 'Anxious']}
                    value={emotion}
                    onChange={setEmotion}
                />
            </Card>

            <Button onClick={handleCalculate} className="mb-6 text-lg">CALCULATE</Button>

            {result && (
                <div className="animate-slide-up">
                    <Card className="border-t-4 border-cyan-500">
                        {result.risk_state === 'HIGH' && (
                            <div className="bg-red-500/20 border border-red-500/50 p-2 rounded mb-4 text-center text-red-300 font-bold text-sm">
                                HIGH EXERCISE RISK
                            </div>
                        )}

                        {result.energy_expended > 0 && (
                            <div className="text-center text-yellow-300 font-bold text-xs mb-4">
                                Est. Burn: ~{result.energy_expended} Kcal ({result.mets} METs)
                            </div>
                        )}

                        <div className="text-center mb-6">
                            <div className="text-6xl font-black text-cyan-400 drop-shadow-glow">
                                {result.recommended_dose} u
                            </div>
                            <div className="text-slate-400 text-sm uppercase tracking-widest mt-2">Recommended Dose</div>
                        </div>

                        <div className="bg-slate-900/50 rounded-lg p-4 text-sm text-slate-300 space-y-2 mb-6">
                            <div className="flex justify-between">
                                <span>Gross Dose:</span>
                                <span>{result.gross_dose.toFixed(2)} u</span>
                            </div>
                            <div className="flex justify-between pl-4 text-slate-500">
                                <span>Carbs:</span>
                                <span>{result.carb_dose.toFixed(2)} u</span>
                            </div>
                            <div className="flex justify-between pl-4 text-slate-500">
                                <span>Correction:</span>
                                <span>{result.correction_dose.toFixed(2)} u</span>
                            </div>
                            <div className="border-t border-slate-700 my-2 pt-2">
                                <div className="flex justify-between">
                                    <span>Modifiers:</span>
                                    <span>{Math.round(result.final_modifier_used * 100)}%</span>
                                </div>
                                <div className="text-xs text-slate-500 italic mt-1">
                                    {result.notes}
                                </div>
                            </div>
                        </div>

                        <Button onClick={handleSave} secondary>Save to History</Button>
                    </Card>
                </div>
            )}
        </div>
    );
};
