import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

export const useLogs = (session) => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!session) return;

        // Fetch initial logs
        const fetchLogs = async () => {
            const { data, error } = await supabase
                .from('logs')
                .select('*')
                .order('timestamp', { ascending: false });

            if (error) console.error('Error fetching logs:', error);
            else setLogs(data);
            setLoading(false);
        };

        fetchLogs();

        // Subscribe to changes
        const subscription = supabase
            .channel('logs_channel')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'logs', filter: `user_id=eq.${session.user.id}` }, (payload) => {
                if (payload.eventType === 'INSERT') {
                    setLogs((prev) => [payload.new, ...prev]);
                } else if (payload.eventType === 'DELETE') {
                    setLogs((prev) => prev.filter(log => log.id !== payload.old.id));
                }
            })
            .subscribe();

        return () => {
            supabase.removeChannel(subscription);
        };
    }, [session]);

    const addLog = async (newLog) => {
        // Optimistic update done by subscription or manual? 
        // Let's rely on subscription for sync, or do manual for speed.
        // For now, simple insert.
        const { error } = await supabase.from('logs').insert([{ ...newLog, user_id: session.user.id }]);
        if (error) {
            console.error('Error adding log:', error);
            alert('Failed to save log');
        }
    };

    const deleteLog = async (id) => {
        const { error } = await supabase.from('logs').delete().match({ id });
        if (error) console.error('Error deleting log:', error);
    };

    return { logs, loading, addLog, deleteLog };
};
