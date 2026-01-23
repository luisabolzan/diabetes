import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

export const useProfile = (session, defaultSettings) => {
    const [settings, setSettings] = useState(defaultSettings);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!session) return;

        const fetchProfile = async () => {
            const { data, error } = await supabase
                .from('profiles')
                .select('*')
                .eq('id', session.user.id)
                .single();

            if (error) {
                console.error('Error fetching profile:', error);
                // If no profile exists (shouldn't happen due to trigger, but fallback)
            } else if (data) {
                // Merge with defaults to ensure all keys exist
                setSettings({ ...defaultSettings, ...data });
            }
            setLoading(false);
        };

        fetchProfile();
    }, [session]);

    const updateSettings = async (newSettings) => {
        // Optimistic update
        setSettings(newSettings);

        const { error } = await supabase
            .from('profiles')
            .update(newSettings)
            .eq('id', session.user.id);

        if (error) {
            console.error('Error updating profile:', error);
            // Revert?
        }
    };

    return { settings, loading, updateSettings };
};
