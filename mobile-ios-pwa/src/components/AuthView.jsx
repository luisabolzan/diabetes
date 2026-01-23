import React, { useState } from 'react';
import { Card, Button, Input } from './UI';
import { supabase } from '../lib/supabase';

export const AuthView = () => {
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isSignUp, setIsSignUp] = useState(false);
    const [message, setMessage] = useState(null);

    const handleAuth = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        try {
            if (isSignUp) {
                const { error } = await supabase.auth.signUp({
                    email,
                    password,
                });
                if (error) throw error;
                setMessage('Check your email for the confirmation link!');
            } else {
                const { error } = await supabase.auth.signInWithPassword({
                    email,
                    password,
                });
                if (error) throw error;
            }
        } catch (error) {
            setMessage(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen p-6 animate-fade-in">
            <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600 mb-8 drop-shadow-glow">
                Diabetes Manager
            </h1>

            <Card className="w-full max-w-sm">
                <h2 className="text-2xl font-bold text-white mb-6 text-center">
                    {isSignUp ? 'Create Account' : 'Welcome Back'}
                </h2>

                {message && (
                    <div className={`p-3 rounded mb-4 text-sm font-bold text-center ${message.includes('Check') ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                        {message}
                    </div>
                )}

                <form onSubmit={handleAuth}>
                    <Input
                        label="Email"
                        type="email"
                        value={email}
                        onChange={setEmail}
                        placeholder="you@example.com"
                    />
                    <Input
                        label="Password"
                        type="password"
                        value={password}
                        onChange={setPassword}
                        placeholder="••••••••"
                    />

                    <Button className="mt-4" disabled={loading} type="submit">
                        {loading ? 'Processing...' : (isSignUp ? 'Sign Up' : 'Sign In')}
                    </Button>
                </form>

                <div className="mt-6 text-center">
                    <button
                        onClick={() => {
                            setIsSignUp(!isSignUp);
                            setMessage(null);
                        }}
                        className="text-slate-400 hover:text-cyan-400 text-sm font-medium transition-colors"
                    >
                        {isSignUp ? 'Already have an account? Sign In' : 'Need an account? Sign Up'}
                    </button>
                </div>
            </Card>
        </div>
    );
};
