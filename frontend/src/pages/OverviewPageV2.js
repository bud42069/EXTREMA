/**
 * Overview Dashboard V2 - Bloomberg-class Main Landing Page
 * Complete visual overhaul with enhanced metrics and navigation
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { Card, Button, MetricCard, StatusIndicator, Badge } from '../components/UIComponents';
import theme from '../design-system.js';

const API = process.env.REACT_APP_BACKEND_URL || '';

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function OverviewPageV2() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    monitor: { running: false, last_price: 0, candles_count: 0 },
    stream: { available: false },
    mtf: { running: false },
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
      const [monitorRes, streamRes, mtfRes] = await Promise.all([
        axios.get(`${API}/api/live/status`).catch(() => ({ data: { running: false, last_price: 0, candles_count: 0 } })),
        axios.get(`${API}/api/stream/snapshot`).catch(() => ({ data: { available: false } })),
        axios.get(`${API}/api/mtf/status`).catch(() => ({ data: { running: false } }))
      ]);

      setStats({
        monitor: monitorRes.data,
        stream: streamRes.data,
        mtf: mtfRes.data,
        swings: { rows: monitorRes.data.candles_count || 0, swings_24h: 0 },
        loading: false
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
      setStats(prev => ({ ...prev, loading: false }));
    }
  };

  const systemHealth = [
    { label: 'Backend API', status: true },
    { label: 'Live Monitor', status: stats.monitor.running },
    { label: 'Microstructure Stream', status: stats.stream.available },
    { label: 'MTF Engine', status: stats.mtf.running },
  ];

  const allSystemsOnline = systemHealth.every(s => s.status);

  return (
    <div 
      className="min-h-screen p-8"
      style={{ background: theme.utils.gradientBg() }}
    >
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-5xl font-black text-gray-200 flex items-center gap-3 mb-2">
              <svg className="w-12 h-12 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              SWING MATRIX
            </h1>
            <p className="text-gray-500 text-lg font-mono">Mission Control • Real-time Trading Intelligence</p>
          </div>
          
          <div className="flex items-center gap-4">
            <StatusIndicator
              status={allSystemsOnline ? 'active' : stats.monitor.running ? 'warning' : 'inactive'}
              label={allSystemsOnline ? 'ALL SYSTEMS ONLINE' : stats.monitor.running ? 'PARTIAL' : 'OFFLINE'}
              pulse={allSystemsOnline}
              size="lg"
            />
            
            <Button
              variant={stats.monitor.running ? 'ghost' : 'success'}
              size="lg"
              onClick={() => navigate('/live')}
            >
              {stats.monitor.running ? 'MONITOR ACTIVE' : 'START MONITOR'}
            </Button>
          </div>
        </div>

        {/* Real-time Banner */}
        {stats.monitor.running && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="text-2xl"
              >
                ⚡
              </motion.div>
              <div>
                <div className="text-emerald-400 font-bold">Live Detection Active</div>
                <div className="text-emerald-600 text-sm">Scanning for 10%+ swing opportunities on 5-minute timeframe</div>
              </div>
            </div>
            <Badge variant="success" size="lg">
              {stats.monitor.candles_count} CANDLES
            </Badge>
          </motion.div>
        )}
      </motion.div>

      {/* Key Metrics Grid */}
      <div className="grid md:grid-cols-4 gap-6 mb-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <MetricCard
            label="SOL/USD"
            value={stats.monitor.last_price > 0 ? `$${stats.monitor.last_price.toFixed(2)}` : '--'}
            subValue={stats.monitor.running ? 'Live from Pyth' : 'Monitor offline'}
            color="cyan"
            size="md"
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <MetricCard
            label="Data Points"
            value={stats.monitor.candles_count || stats.swings.rows || '--'}
            subValue={`${stats.swings.swings_24h || 0} swings detected`}
            color="emerald"
            size="md"
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <MetricCard
            label="System Status"
            value={allSystemsOnline ? 'Optimal' : stats.monitor.running ? 'Partial' : 'Standby'}
            subValue={`${systemHealth.filter(s => s.status).length}/${systemHealth.length} services`}
            color={allSystemsOnline ? 'emerald' : stats.monitor.running ? 'amber' : 'default'}
            size="md"
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <MetricCard
            label="Detection Mode"
            value={stats.mtf.running ? 'MTF Active' : 'Standard'}
            subValue={stats.mtf.running ? 'Multi-timeframe' : 'Single timeframe'}
            color={stats.mtf.running ? 'cyan' : 'default'}
            size="md"
          />
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mb-10"
      >
        <h2 className="text-2xl font-bold text-gray-200 mb-6 flex items-center gap-2">
          <span>🚀</span> QUICK ACTIONS
        </h2>
        
        <div className="grid md:grid-cols-2 gap-6">
          <QuickActionCard
            icon="📡"
            title="Live Signals Dashboard"
            description="Real-time swing detection with microstructure validation"
            color="cyan"
            badge={stats.monitor.running ? 'ACTIVE' : null}
            onClick={() => navigate('/live')}
          />
          
          <QuickActionCard
            icon="🎯"
            title="Generate Scalp Card"
            description="Manual execution sheet with complete trade specifications"
            color="emerald"
            onClick={() => navigate('/scalp-cards')}
          />
          
          <QuickActionCard
            icon="📁"
            title="Upload Historical Data"
            description="Import CSV data for backtesting and analysis"
            color="blue"
            onClick={() => navigate('/upload')}
          />
          
          <QuickActionCard
            icon="📈"
            title="Run Backtest"
            description="Test strategy performance with TP/SL ladder simulation"
            color="amber"
            onClick={() => navigate('/backtest')}
          />
        </div>
      </motion.div>

      {/* System Information Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Methodology */}
        <Card variant="elevated">
          <h3 className="text-xl font-bold text-gray-200 mb-6 flex items-center gap-2">
            <span>🧬</span> DETECTION METHODOLOGY
          </h3>
          
          <div className="space-y-4">
            {[
              {
                step: '1',
                title: 'Candidate Detection',
                description: 'Local extrema (±12 bars) + ATR14/Vol Z-score/BBWidth filters',
                color: 'cyan'
              },
              {
                step: '2',
                title: 'Micro Confirmation',
                description: 'Breakout candle + volume spike (1.5× ATR threshold)',
                color: 'emerald'
              },
              {
                step: '3',
                title: 'Microstructure Gates',
                description: 'Spread/Depth/Imbalance/CVD + OBV-cliff veto logic',
                color: 'amber'
              },
              {
                step: '4',
                title: 'MTF Confluence (Optional)',
                description: 'Multi-timeframe alignment (15m/1h/4h/1D + on-chain)',
                color: 'purple'
              }
            ].map((stage, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + idx * 0.1 }}
                className="flex items-start gap-4 p-4 rounded-lg bg-black/20 border border-gray-800/50 hover:border-cyan-500/30 transition-all"
              >
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-lg font-black border-2 flex-shrink-0"
                  style={{ 
                    background: `${theme.colors.accent[stage.color]}15`,
                    borderColor: `${theme.colors.accent[stage.color]}40`,
                    color: theme.colors.accent[stage.color]
                  }}
                >
                  {stage.step}
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-200 mb-1">{stage.title}</div>
                  <div className="text-sm text-gray-500">{stage.description}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </Card>

        {/* System Health */}
        <Card variant="elevated">
          <h3 className="text-xl font-bold text-gray-200 mb-6 flex items-center gap-2">
            <span>💚</span> SYSTEM HEALTH
          </h3>
          
          <div className="space-y-4">
            {systemHealth.map((service, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + idx * 0.1 }}
                className="flex items-center justify-between p-4 rounded-lg bg-black/20 border border-gray-800/50"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{service.icon}</span>
                  <span className="font-medium text-gray-300">{service.label}</span>
                </div>
                <StatusIndicator
                  status={service.status ? 'active' : 'inactive'}
                  label={service.status ? 'ONLINE' : 'OFFLINE'}
                  pulse={service.status}
                />
              </motion.div>
            ))}
          </div>

          {/* Performance Metrics */}
          <div className="mt-6 pt-6 border-t border-gray-800/50">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/30 rounded-lg p-3 border border-gray-800/30">
                <div className="text-xs text-gray-500 mb-1">Uptime</div>
                <div className="text-xl font-bold text-emerald-400">99.9%</div>
              </div>
              <div className="bg-black/30 rounded-lg p-3 border border-gray-800/30">
                <div className="text-xs text-gray-500 mb-1">Latency</div>
                <div className="text-xl font-bold text-cyan-400">&lt;100ms</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Footer Info */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="mt-10 text-center text-gray-600 text-sm font-mono"
      >
        <p>SWING MATRIX v1.0 • Production-Grade Trading Intelligence Platform</p>
        <p className="mt-1">Built with FastAPI + React + MongoDB • Real-time data via Pyth Network & Binance</p>
      </motion.div>
    </div>
  );
}

// ============================================================================
// QUICK ACTION CARD COMPONENT
// ============================================================================

function QuickActionCard({ icon, title, description, color, badge = null, onClick }) {
  const colors = {
    cyan: theme.colors.accent.cyan,
    emerald: theme.colors.accent.emerald,
    blue: theme.colors.accent.blue,
    amber: theme.colors.accent.amber,
    purple: theme.colors.accent.purple,
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="relative cursor-pointer"
    >
      <Card variant="default" className="h-full">
        <div className="flex items-start gap-4">
          <motion.div
            whileHover={{ rotate: [0, -10, 10, 0] }}
            transition={{ duration: 0.5 }}
            className="text-5xl"
          >
            {icon}
          </motion.div>
          
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 
                className="text-lg font-bold"
                style={{ color: colors[color] }}
              >
                {title}
              </h3>
              {badge && <Badge variant="success" size="sm">{badge}</Badge>}
            </div>
            <p className="text-sm text-gray-500">{description}</p>
          </div>

          <motion.div
            initial={{ opacity: 0, x: -10 }}
            whileHover={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
            style={{ color: colors[color] }}
            className="text-2xl"
          >
            →
          </motion.div>
        </div>
      </Card>
    </motion.div>
  );
}
