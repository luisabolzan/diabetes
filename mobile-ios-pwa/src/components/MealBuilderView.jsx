import React, { useState, useMemo } from 'react';
import { Card, Input, Button } from './UI';
import foodData from '../data/foods.json';

export const MealBuilderView = ({ onCommitToCalculator }) => {
    const [search, setSearch] = useState("");
    const [plate, setPlate] = useState([]);

    // Memoized search to avoid lag on large list
    const filteredFoods = useMemo(() => {
        if (search.length < 2) return [];
        const lower = search.toLowerCase();
        return foodData.filter(f => f.name.toLowerCase().includes(lower)).slice(0, 20); // Limit to 20 results
    }, [search]);

    // Plate Calculations
    const totalCarbs = plate.reduce((sum, item) => sum + (item.carbs * item.quantity), 0);
    const totalKcal = plate.reduce((sum, item) => sum + (item.kcal * item.quantity), 0);

    const addToPlate = (food) => {
        // Check if already in plate
        const existing = plate.find(p => p.id === food.id);
        if (existing) {
            setPlate(plate.map(p => p.id === food.id ? { ...p, quantity: p.quantity + 1 } : p));
        } else {
            setPlate([...plate, { ...food, quantity: 1 }]);
        }
        setSearch(""); // Clear search after adding
    };

    const removeFromPlate = (index) => {
        const newPlate = [...plate];
        newPlate.splice(index, 1);
        setPlate(newPlate);
    };

    const updateQuantity = (index, delta) => {
        const newPlate = [...plate];
        const item = newPlate[index];
        const newQty = item.quantity + delta;

        if (newQty <= 0) {
            removeFromPlate(index);
        } else {
            item.quantity = newQty;
            setPlate(newPlate);
        }
    };

    return (
        <div className="pb-24 animate-fade-in px-2">
            <h2 className="text-2xl font-bold text-cyan-400 mb-4">Meal Builder</h2>

            {/* Search Section */}
            <Card className="mb-6 sticky top-0 z-30 shadow-2xl bg-slate-800/90 backdrop-blur-xl border-cyan-900/50">
                <Input
                    label="Search Food"
                    value={search}
                    onChange={setSearch}
                    placeholder="e.g. Banana, Rice, Bread..."
                />

                {/* Results Dropdown */}
                {filteredFoods.length > 0 && (
                    <div className="absolute top-full left-0 right-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl max-h-60 overflow-y-auto z-40 mt-1">
                        {filteredFoods.map(food => (
                            <button
                                key={food.id}
                                onClick={() => addToPlate(food)}
                                className="w-full text-left px-4 py-3 border-b border-slate-700 hover:bg-slate-700 transition-colors flex justify-between items-center"
                            >
                                <span className="font-medium text-slate-200">{food.name}</span>
                                <span className="text-xs text-cyan-400 bg-cyan-900/30 px-2 py-1 rounded">
                                    {food.carbs}g / {food.measure}
                                </span>
                            </button>
                        ))}
                    </div>
                )}
            </Card>

            {/* Virtual Plate */}
            <div className="mb-2 text-cyan-200 opacity-80 text-sm font-semibold uppercase tracking-wider flex justify-between items-end">
                <span>Your Plate</span>
                {plate.length > 0 && (
                    <button onClick={() => setPlate([])} className="text-xs text-red-400 hover:text-red-300">Clear All</button>
                )}
            </div>

            {plate.length === 0 ? (
                <div className="text-center py-12 border-2 border-dashed border-slate-700 rounded-xl text-slate-500">
                    <div className="text-4xl mb-2">🍽️</div>
                    Add foods to build your meal
                </div>
            ) : (
                <div className="space-y-3 mb-20">
                    {plate.map((item, idx) => (
                        <Card key={idx} className="flex justify-between items-center py-3 px-4 relative overflow-hidden group">
                            <div className="flex-1">
                                <div className="font-medium text-white truncate pr-2">{item.name}</div>
                                <div className="text-xs text-slate-400">
                                    {item.quantity} x ({item.carbs}g ca. - {item.measure})
                                </div>
                            </div>

                            <div className="flex items-center gap-3">
                                <div className="font-bold text-cyan-400 w-12 text-right">
                                    {(item.carbs * item.quantity).toFixed(0)}g
                                </div>

                                <div className="flex flex-col gap-1">
                                    <button
                                        onClick={() => updateQuantity(idx, 1)}
                                        className="w-6 h-6 bg-slate-700 hover:bg-cyan-600 rounded flex items-center justify-center text-xs transition-colors"
                                    >
                                        +
                                    </button>
                                    <button
                                        onClick={() => updateQuantity(idx, -1)}
                                        className="w-6 h-6 bg-slate-700 hover:bg-red-500/50 rounded flex items-center justify-center text-xs transition-colors"
                                    >
                                        -
                                    </button>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}

            {/* Floating Bottom Summary */}
            <div className={`fixed bottom-[80px] left-4 right-4 bg-slate-900/90 backdrop-blur-lg border border-cyan-500/30 rounded-2xl p-4 shadow-2xl transition-transform duration-300 ${plate.length > 0 ? 'translate-y-0' : 'translate-y-32'}`}>
                <div className="flex justify-between items-end mb-3">
                    <div>
                        <div className="text-xs text-slate-400">Total Carbs</div>
                        <div className="text-3xl font-black text-cyan-400">{totalCarbs.toFixed(1)} <span className="text-sm font-normal text-slate-400">g</span></div>
                    </div>
                    <div className="text-right">
                        <div className="text-xs text-slate-400">Energy</div>
                        <div className="text-xl font-bold text-yellow-500">{totalKcal.toFixed(0)} <span className="text-sm font-normal text-slate-400">kcal</span></div>
                    </div>
                </div>

                <Button onClick={() => onCommitToCalculator(Math.round(totalCarbs))}>
                    Use Total ({Math.round(totalCarbs)}g) in Calculator
                </Button>
            </div>
        </div>
    );
};
