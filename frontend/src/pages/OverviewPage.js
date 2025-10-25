import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function OverviewPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    monitor: { running: false, last_price: 0, candles_count: 0 },
    swings: { rows: 0, swings_24h: 0 },
    loading: true
  });

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const [monitorRes, swingsRes] = await Promise.all([
        axios.get(`${API}/live/status`),
        axios.get(`${API}/swings/`)
      ]);
      setStats({
        monitor: monitorRes.data,
        swings: swingsRes.data,
        loading: false
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
      setStats(prev => ({ ...prev, loading: false }));
    }
  };

  const StatCard = ({ icon, label, value, subtext, gradient, onClick }) => (
    <div 
      onClick={onClick}
      className={`group relative overflow-hidden rounded-2xl ${onClick ? 'cursor-pointer' : ''}`}
    >
      {/* Glassmorphic background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl"></div>
      
      {/* Gradient overlay on hover */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}></div>
      
      {/* Border */}
      <div className="absolute inset-0 border border-slate-700/50 group-hover:border-emerald-500/30 rounded-2xl transition-colors"></div>
      
      {/* Content */}
      <div className="relative p-8">
        <div className="flex items-start justify-between mb-6">
          <div className="text-5xl">{icon}</div>
          {onClick && (
            <div className="opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-emerald-400 text-sm">View →</span>
            </div>
          )}
        </div>
        
        <div className="text-sm text-slate-400 mb-2 font-medium uppercase tracking-wider">{label}</div>
        <div className="text-4xl font-bold text-white mb-1">{value}</div>
        {subtext && <div className="text-sm text-slate-500">{subtext}</div>}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/30 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-5xl font-bold bg-gradient-to-r from-white to-emerald-400 bg-clip-text text-transparent mb-2">
                Overview
              </h1>
              <p className="text-slate-400 text-lg">System status and key metrics</p>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg backdrop-blur-xl ${
                stats.monitor.running 
                  ? 'bg-emerald-500/10 border border-emerald-500/30' 
                  : 'bg-slate-800/50 border border-slate-700'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  stats.monitor.running ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
                }`}></div>
                <span className={`text-sm font-medium ${
                  stats.monitor.running ? 'text-emerald-400' : 'text-slate-400'
                }`}>
                  {stats.monitor.running ? 'Live' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Stats Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <StatCard
            icon="💰"
            label="SOL/USD Price"
            value={stats.monitor.last_price > 0 ? `$${stats.monitor.last_price.toFixed(2)}` : '--'}
            subtext={stats.monitor.running ? 'Live from Pyth Network' : 'Monitor offline'}
            gradient="from-emerald-500 to-cyan-500"
            onClick={() => navigate('/live')}
          />
          
          <StatCard
            icon="📊"
            label="Candles Loaded"
            value={stats.monitor.candles_count || stats.swings.rows || 0}
            subtext={`${stats.swings.swings_24h || 0} swings detected`}
            gradient="from-cyan-500 to-blue-500"
            onClick={() => navigate('/analysis')}
          />
          
          <StatCard
            icon="⚡"
            label="Monitor Status"
            value={stats.monitor.running ? 'Active' : 'Standby'}
            subtext={stats.monitor.running ? 'Real-time detection enabled' : 'Start monitor to begin'}
            gradient="from-emerald-500 to-green-500"
            onClick={() => navigate('/live')}
          />
        </div>

        {/* Quick Actions */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Quick Actions</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              {
                icon: '🎯',
                title: 'Generate Scalp Card',
                description: 'Create manual execution trade card with complete specs',
                action: () => navigate('/scalp-cards'),
                color: 'emerald'
              },
              {
                icon: '📡',
                title: 'View Live Signals',
                description: 'Real-time swing detection and signal monitoring',
                action: () => navigate('/live'),
                color: 'cyan'
              },
              {
                icon: '📁',
                title: 'Upload Data',
                description: 'Import historical CSV data for analysis',
                action: () => navigate('/upload'),
                color: 'blue'
              },
              {
                icon: '📈',
                title: 'Run Backtest',
                description: 'Test strategy performance on historical data',
                action: () => navigate('/backtest'),
                color: 'purple'
              }
            ].map((action, i) => (
              <button
                key={i}
                onClick={action.action}
                className="group relative overflow-hidden rounded-2xl text-left transition-all hover:scale-[1.02]"
              >
                {/* Glassmorphic background */}
                <div className="absolute inset-0 bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl"></div>
                
                {/* Gradient overlay */}
                <div className={`absolute inset-0 bg-gradient-to-br from-${action.color}-500/0 to-${action.color}-500/0 group-hover:from-${action.color}-500/10 group-hover:to-transparent transition-all duration-300`}></div>
                
                {/* Border */}
                <div className="absolute inset-0 border border-slate-700/50 group-hover:border-emerald-500/30 rounded-2xl transition-colors"></div>
                
                {/* Content */}
                <div className="relative p-6 flex items-center space-x-6">
                  <div className="text-5xl">{action.icon}</div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white mb-1 group-hover:text-emerald-400 transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-slate-400 text-sm">{action.description}</p>
                  </div>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="text-emerald-400">→</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* System Info */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="relative overflow-hidden rounded-2xl">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl"></div>
            <div className="absolute inset-0 border border-slate-700/50 rounded-2xl"></div>
            <div className="relative p-6">
              <h3 className="text-lg font-bold text-white mb-4">Methodology</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-sm">1</div>
                  <span className="text-slate-300">Candidate Detection (Extrema + Filters)</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-sm">2</div>
                  <span className="text-slate-300">Micro-Confirmation (Breakout + Volume)</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-sm">3</div>
                  <span className="text-slate-300">Microstructure Gates (7 Checks)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-2xl">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl"></div>
            <div className="absolute inset-0 border border-slate-700/50 rounded-2xl"></div>
            <div className="relative p-6">
              <h3 className="text-lg font-bold text-white mb-4">System Status</h3>
              <div className="space-y-3">
                {[
                  { label: 'Backend API', status: true },
                  { label: 'WebSocket', status: stats.monitor.running },
                  { label: 'Data Pipeline', status: stats.swings.rows > 0 },
                  { label: 'Live Monitor', status: stats.monitor.running }
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-slate-400">{item.label}</span>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${item.status ? 'bg-emerald-400' : 'bg-slate-500'}`}></div>
                      <span className={`text-sm ${item.status ? 'text-emerald-400' : 'text-slate-500'}`}>
                        {item.status ? 'Online' : 'Offline'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
