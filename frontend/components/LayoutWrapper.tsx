'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '../lib/store';
import { 
  LayoutDashboard, 
  UploadCloud, 
  FileText, 
  FileCheck, 
  History, 
  LogOut, 
  ShieldAlert, 
  Menu, 
  X,
  User as UserIcon
} from 'lucide-react';

export default function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, isLoading, checkAuth, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    checkAuth();
  }, [checkAuth]);

  const isAuthPage = pathname === '/login' || pathname === '/register';

  useEffect(() => {
    if (isMounted && !isLoading) {
      if (!isAuthenticated && !isAuthPage) {
        router.push('/login');
      } else if (isAuthenticated && isAuthPage) {
        router.push('/dashboard');
      }
    }
  }, [isMounted, isAuthenticated, isLoading, isAuthPage, router]);

  // Prevent hydration discrepancies
  if (!isMounted) return null;

  // Show fullscreen loading while checking authentication
  if (isLoading && !isAuthPage) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center text-slate-100">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-slate-400 font-medium tracking-wide">Authenticating GRC Copilot...</p>
      </div>
    );
  }

  // If not authenticated and on an auth page, render clean page
  if (isAuthPage) {
    return <>{children}</>;
  }

  // If not authenticated and not on an auth page (redirecting), show empty space
  if (!isAuthenticated) {
    return null;
  }

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Upload PDF', path: '/upload', icon: UploadCloud },
    { name: 'Documents', path: '/documents', icon: FileText },
    { name: 'Executive Reports', path: '/reports', icon: FileCheck },
    { name: 'Audit Logs', path: '/audit', icon: History },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans">
      {/* Mobile Sidebar Trigger */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 focus:outline-none"
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-300 lg:translate-x-0 lg:static
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div>
          {/* Brand Header */}
          <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg">
              <ShieldAlert size={20} className="animate-pulse" />
            </div>
            <div>
              <h1 className="font-bold text-slate-100 tracking-wide text-sm">AI Compliance Risk</h1>
              <p className="text-[10px] text-indigo-400 uppercase tracking-widest font-semibold">GRC Copilot</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.path || pathname.startsWith(item.path + '/');
              return (
                <Link
                  key={item.name}
                  href={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 group
                    ${isActive 
                      ? 'bg-indigo-600/90 text-white shadow-lg shadow-indigo-600/10' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent hover:border-slate-800/50'
                    }
                  `}
                >
                  <Icon size={18} className={`transition-transform duration-300 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Card & Logout */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/50">
          <div className="flex items-center gap-3 px-3 py-2 mb-3 bg-slate-950/40 rounded-lg border border-slate-800/40">
            <div className="w-9 h-9 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <UserIcon size={16} />
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-slate-200 truncate">{user?.name}</p>
              <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              router.push('/login');
            }}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 rounded-lg text-xs font-semibold border border-rose-500/20 bg-rose-500/5 hover:bg-rose-500/10 text-rose-400 hover:text-rose-300 transition-all duration-200"
          >
            <LogOut size={14} />
            Logout Session
          </button>
        </div>
      </aside>

      {/* Main Panel */}
      <div className="flex-1 flex flex-col min-w-0 lg:max-h-screen overflow-y-auto">
        <header className="h-16 border-b border-slate-800/80 bg-slate-900/20 backdrop-blur-md flex items-center justify-between px-8 sticky top-0 z-30">
          <div>
            <h2 className="text-xs text-indigo-400 font-bold tracking-widest uppercase">System Active</h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              Secure Tunnel
            </div>
          </div>
        </header>
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
