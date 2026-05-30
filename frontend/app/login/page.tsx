'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '../../lib/store';
import { ShieldAlert, Mail, Lock, ArrowRight } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  
  const router = useRouter();
  const { login, isAuthenticated, isLoading, error, clearError } = useAuthStore();

  useEffect(() => {
    clearError();
    setLocalError(null);
  }, [clearError]);

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email || !password) {
      setLocalError('Please fill in all fields.');
      return;
    }

    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err: any) {
      // Error handled by store
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center items-center px-4 font-sans">
      {/* Background Glow */}
      <div className="absolute w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] -z-10 top-1/4 left-1/4 animate-pulse"></div>
      <div className="absolute w-[400px] h-[400px] bg-violet-500/10 rounded-full blur-[100px] -z-10 bottom-1/4 right-1/4 animate-pulse"></div>

      <div className="w-full max-w-md bg-slate-900 border border-slate-800/80 rounded-2xl shadow-2xl shadow-indigo-500/5 p-8 backdrop-blur-md">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-2xl mb-4">
            <ShieldAlert size={28} className="animate-pulse" />
          </div>
          <h1 className="text-xl font-bold text-slate-100 tracking-wide">AI Compliance Risk Copilot</h1>
          <p className="text-xs text-slate-400 mt-1.5 uppercase tracking-widest font-bold text-indigo-400">Enterprise GRC Portal</p>
        </div>

        {/* Errors */}
        {(localError || error) && (
          <div className="mb-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold">
            {localError || error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input
                type="email"
                placeholder="analyst@compliance.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-800 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-all duration-200"
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">Password</label>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-800 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-all duration-200"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white rounded-lg text-sm font-semibold tracking-wide shadow-lg shadow-indigo-600/10 hover:shadow-indigo-600/20 active:scale-[0.98] transition-all duration-200 mt-2"
          >
            {isLoading ? (
              <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <>
                Access Portal
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-8 text-center border-t border-slate-800/80 pt-6">
          <p className="text-xs text-slate-400">
            First time here?{' '}
            <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-bold transition-colors">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
