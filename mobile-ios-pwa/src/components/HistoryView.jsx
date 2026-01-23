import React from 'react';
import { Card, Button } from './UI';

export const HistoryView = ({ logs, deleteLog }) => {

    const [isExporting, setIsExporting] = React.useState(false);

    const handleExport = () => {
        if (!logs.length || isExporting) return;

        setIsExporting(true);
        setTimeout(() => setIsExporting(false), 1000); // 1s Debounce

        // Create CSV content
        const headers = ["Timestamp", "Glucose", "Carbs", "Activity", "Emotion", "Recommended Dose", "Actual Dose"];
        const rows = logs.map(l => [
            l.timestamp,
            l.glucose,
            l.carbs,
            l.activity,
            l.emotion,
            l.recommended_dose,
            l.actual_dose
        ]);

        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += headers.join(",") + "\n";
        rows.forEach(row => {
            csvContent += row.join(",") + "\n";
        });

        // Trigger download
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "diabetes_logs.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Basic delete function
    const handleDelete = (id) => {
        if (confirm("Delete this log?")) {
            deleteLog(id);
        }
    };

    return (
        <div className="pb-24 animate-fade-in">
            <div className="flex justify-between items-center mb-6 px-2">
                <h2 className="text-2xl font-bold text-cyan-400">History</h2>
                <Button onClick={handleExport} className="w-auto py-2 px-4 text-sm" secondary>Export CSV</Button>
            </div>

            {logs.length === 0 && (
                <div className="text-center text-slate-500 mt-10 italic">
                    No logs recorded yet.
                </div>
            )}

            <div className="space-y-4">
                {logs.map((log, idx) => (
                    <Card key={idx} className="border-l-4 border-cyan-500 relative">
                        <div className="flex justify-between items-start mb-2">
                            <div>
                                <div className="text-xs text-slate-400 font-mono">
                                    {new Date(log.timestamp).toLocaleString()}
                                </div>
                                <div className="font-bold text-white text-lg mt-1">
                                    {log.actual_dose} u
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-slate-400 text-sm">Target: {log.glucose} mg/dL</div>
                                <div className="text-slate-400 text-sm">{log.carbs}g CHO</div>
                            </div>
                        </div>

                        <div className="flex justify-between items-center pt-2 border-t border-slate-700/50">
                            <div className="flex gap-2 text-xs">
                                <span className="bg-slate-800 px-2 py-1 rounded text-cyan-200">{log.activity}</span>
                                <span className="bg-slate-800 px-2 py-1 rounded text-purple-200">{log.emotion}</span>
                            </div>
                            <button
                                onClick={() => handleDelete(log.id)}
                                className="text-red-400 text-xs hover:text-red-300"
                            >
                                Delete
                            </button>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
};
