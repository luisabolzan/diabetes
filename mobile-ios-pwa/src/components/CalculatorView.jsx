import React, { useState, useEffect, useMemo } from 'react';
import { Card, Input, Select, Button } from './UI';
import { InsulinCalculator } from '../utils/calculator';
import foodData from '../data/foods.json';

export const CalculatorView = ({ settings, logs, onSaveLog, initialCarbs, setSharedCarbs }) => {
    // Calculator State
    const [glucose, setGlucose] = useState(120);
    const [activity, setActivity] = useState('None');
    const [emotion, setEmotion] = useState('Calm');
    const [duration, setDuration] = useState(30);
    const [intensity, setIntensity] = useState('Moderate');
    const [lastDoseMin, setLastDoseMin] = useState(180);
    const [result, setResult] = useState(null);

    // Meal Builder State
    const [searchQuery, setSearchQuery] = useState("");
    const [plate, setPlate] = useState([]);
    const [manualCarbs, setManualCarbs] = useState(initialCarbs || 0);

    // Filter Foods for Search
    const filteredFoods = useMemo(() => {
        if (!searchQuery || !isNaN(searchQuery)) return []; // Don't search if it's a number or empty
        const lower = searchQuery.toLowerCase();
        return foodData.filter(f => f.name.toLowerCase().includes(lower)).slice(0, 10);
    }, [searchQuery]);

    // Calculate Totals
    const plateCarbs = plate.reduce((sum, item) => sum + (item.carbs * item.quantity), 0);
    const totalCarbs = Math.round(plateCarbs + (parseFloat(manualCarbs) || 0));

    // Handle Input Change (Smart search vs Manual)
    const handleInputChange = (val) => {
        setSearchQuery(val);
        // If it's a number, update manual carbs immediately
        if (!isNaN(val) && val.trim() !== '') {
            setManualCarbs(parseFloat(val));
        } else if (val.trim() === '') {
            setManualCarbs(0);
        }
    };

    const addFoodToPlate = (food) => {
        const existing = plate.find(p => p.id === food.id);
        if (existing) {
            setPlate(plate.map(p => p.id === food.id ? { ...p, quantity: p.quantity + 1 } : p));
        } else {
            setPlate([...plate, { ...food, quantity: 1 }]);
        }
        setSearchQuery(""); // Clear search
    };

    const updateQuantity = (index, delta) => {
        const newPlate = [...plate];
        const item = newPlate[index];
        const newQty = item.quantity + delta;
        if (newQty <= 0) {
            newPlate.splice(index, 1);
        } else {
            item.quantity = newQty;
        }
        setPlate(newPlate);
    };

    // Calculation Logic
    const handleCalculate = () => {
        const calc = new InsulinCalculator(settings);
        const res = calc.calculate_dose(
            parseInt(glucose),
            parseInt(totalCarbs),
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
            carbs: parseInt(totalCarbs),
            activity,
            emotion,
            recommended_dose: result.recommended_dose,
            actual_dose: result.recommended_dose,
            notes: `Plate: ${plate.map(p => p.name).join(', ')}`
        });
        setResult(null);
        setPlate([]);
        setManualCarbs(0);
        setSearchQuery("");
    };

    // Live status check
    const isPeak = lastDoseMin >= 60 && lastDoseMin <= 120;

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

            <h2 className="text-3xl font-bold text-center text-cyan-400 mb-6">Dashboard</h2>

            {/* Smart Input Card */}
            <Card className="mb-4 overflow-visible relative z-20">
                <div className="grid grid-cols-2 gap-4 mb-2">
                    <Input label="Glucose (mg/dL)" value={glucose} onChange={setGlucose} type="number" />
                    <div className="relative">
                        <Input
                            label="Carbs / Food Search"
                            value={searchQuery}
                            onChange={handleInputChange}
                            placeholder="45 or 'Apple'"
                            type="text"
                        />
                        {/* Search Results Dropdown */}
                        {filteredFoods.length > 0 && (
                            <div className="absolute top-full left-0 right-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl max-h-60 overflow-y-auto z-50 mt-1">
                                {filteredFoods.map(food => (
                                    <button
                                        key={food.id}
                                        onClick={() => addFoodToPlate(food)}
                                        className="w-full text-left px-4 py-3 border-b border-slate-700 hover:bg-slate-700 transition-colors flex justify-between items-center"
                                    >
                                        <span className="font-medium text-slate-200">{food.name}</span>
                                        <span className="text-xs text-cyan-400 bg-cyan-900/30 px-2 py-1 rounded">
                                            {food.carbs}g
                                        </span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Virtual Plate Display */}
                {(plate.length > 0 || manualCarbs > 0) && (
                    <div className="bg-slate-900/50 rounded-lg p-3 mt-2 border border-slate-700/50">
                        <div className="flex justify-between items-center mb-2 border-b border-slate-700 pb-1">
                            <span className="text-xs font-bold text-slate-400 uppercase">Current Plate</span>
                            <span className="text-lg font-bold text-cyan-400">{totalCarbs}g</span>
                        </div>

                        <div className="space-y-2 max-h-32 overflow-y-auto custom-scrollbar">
                            {/* Manual Entry Item */}
                            {manualCarbs > 0 && (
                                <div className="flex justify-between items-center text-sm">
                                    <span className="text-slate-300 italic">Manual Entry</span>
                                    <span className="text-cyan-400">{manualCarbs}g</span>
                                </div>
                            )}

                            {/* Plate Items */}
                            {plate.map((item, idx) => (
                                <div key={idx} className="flex justify-between items-center text-sm">
                                    <div className="flex items-center gap-2 overflow-hidden">
                                        <button onClick={() => updateQuantity(idx, -1)} className="text-red-400 hover:text-red-300 font-bold px-1 py-0.5 rounded bg-slate-800">-</button>
                                        <span className="text-slate-200 truncate max-w-[120px]">{item.quantity}x {item.name}</span>
                                        <button onClick={() => updateQuantity(idx, 1)} className="text-green-400 hover:text-green-300 font-bold px-1 py-0.5 rounded bg-slate-800">+</button>
                                    </div>
                                    <span className="text-cyan-400">{(item.carbs * item.quantity).toFixed(0)}g</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <div className="mt-4">
                    <Input label="Mins since last dose" value={lastDoseMin} onChange={setLastDoseMin} type="number" />
                </div>
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
                    <div className="grid grid-cols-2 gap-4 mt-4">
                        <Input label="Duration (min)" value={duration} onChange={setDuration} type="number" />
                        <Select
                            label="Intensity"
                            options={['Slow', 'Moderate', 'Fast']}
                            value={intensity}
                            onChange={setIntensity}
                        />
                    </div>
                )}
                <div className="mt-4">
                    <Select
                        label="Emotion"
                        options={['Calm', 'Stress', 'Anxious']}
                        value={emotion}
                        onChange={setEmotion}
                    />
                </div>
            </Card>

            <Button onClick={handleCalculate} className="mb-6 text-lg">CALCULATE DOSE</Button>

            {/* Result Card */}
            {result && (
                <div className="animate-slide-up">
                    <Card className="border-t-4 border-cyan-500 shadow-2xl bg-slate-800">
                        <div className="text-center mb-6">
                            <div className="text-6xl font-black text-cyan-400 drop-shadow-glow">
                                {result.recommended_dose} u
                            </div>
                            <div className="text-slate-400 text-sm uppercase tracking-widest mt-2">Recommended Dose</div>
                        </div>

                        <div className="bg-slate-900/50 rounded-lg p-4 text-sm text-slate-300 space-y-2 mb-6">
                            <div className="flex justify-between"><span>Carb Dose:</span> <span>{result.carb_dose.toFixed(2)} u</span></div>
                            <div className="flex justify-between"><span>Correction:</span> <span>{result.correction_dose.toFixed(2)} u</span></div>
                            <div className="border-t border-slate-700 pt-2 flex justify-between text-slate-500 text-xs">
                                <span>Modifiers: {(result.final_modifier_used * 100).toFixed(0)}%</span>
                            </div>
                        </div>

                        <Button onClick={handleSave} secondary>Save to History</Button>
                    </Card>
                </div>
            )}
        </div>
    );
};
