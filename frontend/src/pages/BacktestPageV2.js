/**
 * Backtest Page V2 - Bloomberg-class Performance Testing Interface
 * Complete visual overhaul with equity curves and metrics
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { Card, Button, Input, MetricCard, Badge, ProgressBar } from '../components/UIComponents';
import theme from '../design-system.js';

const API = process.env.REACT_APP_BACKEND_URL || '';

export default function BacktestPageV2() {
  const navigate = useNavigate();
  const [backtesting, setBacktesting] = useState(false);
  const [backtestResult, setBacktestResult] = useState(null);
  const [dataLoaded, setDataLoaded] = useState(false);
  
  const [config, setConfig] = useState({
    initial_capital: '10000',
    risk_per_trade: '2',
    tp1_r: '1.0',
    tp2_r: '2.0',
    tp3_r: '3.5',
    tp1_scale: '50',
    tp2_scale: '30'
  });

  useEffect(() => {
    checkDataAvailability();
  }, []);

  const checkDataAvailability = async () => {
    try {
      const response = await axios.get(`${API}/api/swings/`);
      setDataLoaded(response.data.rows > 0);
    } catch (error) {
      console.error('Error checking data:', error);
      setDataLoaded(false);
    }
  };

  const handleBacktest = async () => {
    if (!dataLoaded) {
      toast.error('⚠️ Please upload data first');
      navigate('/upload');
      return;
    }

    setBacktesting(true);
    try {
      // First run analysis to get signal
      const analysisRes = await axios.get(`${API}/api/signals/latest`, {
        params: {
          atr_min: 0.6,
          volz_min: 0.5,
          bbw_min: 0.005,
          confirm_window: 6,
          breakout_atr_mult: 0.5,
          vol_mult: 1.5,
          enable_micro_gate: false
        }
      });

      // Then run backtest
      const backtestRes = await axios.post(`${API}/api/backtest`, {
        initial_capital: parseFloat(config.initial_capital),
        risk_per_trade: parseFloat(config.risk_per_trade) / 100,
        tp1_r: parseFloat(config.tp1_r),
        tp2_r: parseFloat(config.tp2_r),
        tp3_r: parseFloat(config.tp3_r),
        tp1_scale: parseFloat(config.tp1_scale) / 100,
        tp2_scale: parseFloat(config.tp2_scale) / 100
      });
      
      if (backtestRes.data.success) {
        toast.success('✅ Backtest completed!');
        
        // Fetch full backtest details
        const detailsRes = await axios.get(`${API}/api/backtest/${backtestRes.data.backtest_id}`);
        setBacktestResult(detailsRes.data);
      }
    } catch (error) {
      console.error('Backtest error:', error);
      toast.error(error.response?.data?.detail || '❌ Backtest failed');
      setBacktestResult(null);
    } finally {
      setBacktesting(false);
    }
  };

  const updateConfig = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const resetToDefaults = () => {
    setConfig({
      initial_capital: '10000',
      risk_per_trade: '2',
      tp1_r: '1.0',
      tp2_r: '2.0',
      tp3_r: '3.5',
      tp1_scale: '50',
      tp2_scale: '30'
    });
    toast.info('🔄 Reset to default parameters');
  };

  const stats = backtestResult?.statistics;
  const trades = backtestResult?.trades || [];

  return (
    <div className="min-h-screen" style={{ background: theme.utils.gradientBg() }}>
      {/* Header */}
      <div className="sticky top-0 z-40 bg-black/80 backdrop-blur-2xl border-b border-cyan-500/10">
        <div className="px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-gray-200 flex items-center gap-3">
              <span className="text-3xl">📈</span>
              STRATEGY BACKTESTER
            </h1>
            <p className="text-sm text-gray-500 mt-1 font-mono">Performance testing with TP/SL ladder simulation</p>
          </div>
          
          <div className="flex items-center gap-4">
            {dataLoaded ? (
              <Badge variant="success" size="lg">
                ✓ DATA READY
              </Badge>
            ) : (
              <Badge variant="error" size="lg">
                ⚠ NO DATA
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="p-8 space-y-6">
        {/* Configuration Panel */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Risk Management */}
          <Card variant="elevated">
            <h2 className="text-xl font-bold text-cyan-400 mb-2 flex items-center gap-2">
              <span>💰</span> CAPITAL & RISK
            </h2>
            <p className="text-sm text-gray-500 mb-6">Portfolio configuration and position sizing</p>

            <div className="space-y-4">
              <Input
                label="Initial Capital ($)"
                value={config.initial_capital}
                onChange={(e) => updateConfig('initial_capital', e.target.value)}
                type="number"
                placeholder="10000"
                helperText="Starting portfolio value in USD"
                leftIcon="💵"
              />

              <Input
                label="Risk Per Trade (%)"
                value={config.risk_per_trade}
                onChange={(e) => updateConfig('risk_per_trade', e.target.value)}
                type="number"
                step="0.5"
                placeholder="2"
                helperText="Percentage of capital at risk per trade"
                leftIcon="🎯"
              />
            </div>

            <div className="mt-6 p-4 rounded-lg bg-black/30 border border-gray-800/50">
              <div className="text-xs text-gray-500 mb-2 font-semibold">POSITION SIZE CALC:</div>
              <div className="text-xs text-gray-400 space-y-1">
                <div>• Capital at Risk = ${parseFloat(config.initial_capital || 0) * parseFloat(config.risk_per_trade || 0) / 100}</div>
                <div>• Position Size = Risk ÷ (Entry - SL)</div>
                <div>• Dynamic sizing based on stop distance</div>
              </div>
            </div>
          </Card>

          {/* TP/SL Ladder */}
          <Card variant="elevated">
            <h2 className="text-xl font-bold text-emerald-400 mb-2 flex items-center gap-2">
              <span>🎯</span> TP/SL LADDER
            </h2>
            <p className="text-sm text-gray-500 mb-6">Take-profit levels and position scaling</p>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="TP1 (R Multiple)"
                  value={config.tp1_r}
                  onChange={(e) => updateConfig('tp1_r', e.target.value)}
                  type="number"
                  step="0.5"
                  placeholder="1.0"
                  leftIcon="🥇"
                />
                <Input
                  label="TP1 Scale (%)"
                  value={config.tp1_scale}
                  onChange={(e) => updateConfig('tp1_scale', e.target.value)}
                  type="number"
                  placeholder="50"
                  leftIcon="📊"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="TP2 (R Multiple)"
                  value={config.tp2_r}
                  onChange={(e) => updateConfig('tp2_r', e.target.value)}
                  type="number"
                  step="0.5"
                  placeholder="2.0"
                  leftIcon="🥈"
                />
                <Input
                  label="TP2 Scale (%)"
                  value={config.tp2_scale}
                  onChange={(e) => updateConfig('tp2_scale', e.target.value)}
                  type="number"
                  placeholder="30"
                  leftIcon="📊"
                />
              </div>

              <Input
                label="TP3 (R Multiple)"
                value={config.tp3_r}
                onChange={(e) => updateConfig('tp3_r', e.target.value)}
                type="number"
                step="0.5"
                placeholder="3.5"
                helperText="Final exit (remaining position)"
                leftIcon="🥉"
              />
            </div>

            <div className="mt-6 p-4 rounded-lg bg-black/30 border border-gray-800/50">
              <div className="text-xs text-gray-500 mb-2 font-semibold">LADDER LOGIC:</div>
              <div className="text-xs text-gray-400 space-y-1">
                <div>• TP1 @ {config.tp1_r}R → Exit {config.tp1_scale}% of position</div>
                <div>• TP2 @ {config.tp2_r}R → Exit {config.tp2_scale}% of position</div>
                <div>• TP3 @ {config.tp3_r}R → Exit remaining {100 - parseFloat(config.tp1_scale || 0) - parseFloat(config.tp2_scale || 0)}%</div>
              </div>
            </div>
          </Card>
        </div>

        {/* Action Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="primary"
              size="lg"
              onClick={handleBacktest}
              loading={backtesting}
              disabled={!dataLoaded}
              leftIcon="🚀"
            >
              {backtesting ? 'RUNNING...' : 'RUN BACKTEST'}
            </Button>
            
            <Button
              variant="ghost"
              size="lg"
              onClick={resetToDefaults}
              leftIcon="🔄"
            >
              RESET
            </Button>
          </div>

          {stats && (
            <Badge 
              variant={stats.profit_factor > 1.5 ? 'success' : stats.profit_factor > 1 ? 'tierB' : 'error'} 
              size="lg"
            >
              PF: {stats.profit_factor.toFixed(2)}
            </Badge>
          )}
        </div>

        {/* Results Section */}
        <AnimatePresence mode="wait">
          {backtesting && <BacktestingState key="backtesting" />}
          
          {!backtesting && backtestResult && stats && (
            <BacktestResults 
              key="results" 
              stats={stats} 
              trades={trades}
              config={config}
            />
          )}
          
          {!backtesting && !backtestResult && (
            <EmptyState key="empty" dataLoaded={dataLoaded} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ============================================================================
// STATE COMPONENTS
// ============================================================================

function BacktestingState() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => Math.min(prev + 3, 95));
    }, 150);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <Card>
        <div className="text-center py-12">
          <motion.div
            animate={{ 
              scale: [1, 1.1, 1],
              rotate: [0, 5, -5, 0]
            }}
            transition={{ duration: 2, repeat: Infinity }}
            className="text-6xl mb-6 inline-block"
          >
            📈
          </motion.div>
          
          <h3 className="text-2xl font-bold text-gray-200 mb-2">Running Backtest...</h3>
          <p className="text-gray-500 mb-6">Simulating trades with TP/SL ladder strategy</p>
          
          <div className="max-w-md mx-auto">
            <ProgressBar
              value={progress}
              max={100}
              color="emerald"
              animated={true}
            />
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function BacktestResults({ stats, trades, config }) {
  // Prepare equity curve data
  const equityCurve = trades.map((trade, idx) => ({
    index: idx + 1,
    equity: trade.balance || 0,
    drawdown: trade.drawdown || 0
  }));

  const winRate = (stats.win_rate * 100).toFixed(1);
  const isProfitable = stats.profit_factor > 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      {/* Performance Metrics */}
      <div className="grid md:grid-cols-5 gap-4">
        <MetricCard
          label="Final P/L"
          value={`$${stats.total_pnl.toFixed(2)}`}
          trend={stats.total_pnl > 0 ? 'up' : 'down'}
          size="sm"
          icon="💰"
        />
        
        <MetricCard
          label="Profit Factor"
          value={stats.profit_factor.toFixed(2)}
          color={stats.profit_factor > 1.5 ? 'emerald' : stats.profit_factor > 1 ? 'amber' : 'rose'}
          size="sm"
          icon="📊"
        />
        
        <MetricCard
          label="Win Rate"
          value={`${winRate}%`}
          color={parseFloat(winRate) >= 50 ? 'emerald' : 'amber'}
          size="sm"
          icon="🎯"
        />
        
        <MetricCard
          label="Max Drawdown"
          value={`${(stats.max_drawdown * 100).toFixed(1)}%`}
          color="rose"
          size="sm"
          icon="📉"
        />
        
        <MetricCard
          label="Total Trades"
          value={stats.total_trades}
          subValue={`${stats.winning_trades}W / ${stats.losing_trades}L`}
          size="sm"
          icon="🔢"
        />
      </div>

      {/* Equity Curve */}
      <Card variant="elevated">
        <h3 className="text-xl font-bold text-gray-200 mb-6 flex items-center gap-2">
          <span>📈</span> EQUITY CURVE
        </h3>
        
        {equityCurve.length > 0 ? (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityCurve}>
                <defs>
                  <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={theme.colors.accent.emerald} stopOpacity={0.4} />
                    <stop offset="100%" stopColor={theme.colors.accent.emerald} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border.default} />
                <XAxis 
                  dataKey="index" 
                  stroke={theme.colors.text.tertiary}
                  tick={{ fill: theme.colors.text.tertiary, fontSize: 12 }}
                />
                <YAxis 
                  stroke={theme.colors.text.tertiary}
                  tick={{ fill: theme.colors.text.tertiary, fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: theme.colors.bg.elevated,
                    border: `1px solid ${theme.colors.border.default}`,
                    borderRadius: '8px',
                    color: theme.colors.text.primary
                  }}
                  formatter={(value) => [`$${value.toFixed(2)}`, 'Equity']}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke={theme.colors.accent.emerald}
                  strokeWidth={2}
                  fill="url(#equityGradient)"
                  animationDuration={1000}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-80 flex items-center justify-center text-gray-500">
            No trade data available
          </div>
        )}
      </Card>

      {/* Trade Statistics */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card variant="elevated">
          <h3 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
            <span>📊</span> PERFORMANCE METRICS
          </h3>
          
          <div className="space-y-3">
            <MetricRow label="Average Win" value={`$${stats.avg_win.toFixed(2)}`} color="emerald" />
            <MetricRow label="Average Loss" value={`$${stats.avg_loss.toFixed(2)}`} color="rose" />
            <MetricRow label="Average R" value={`${stats.avg_r.toFixed(2)}R`} />
            <MetricRow label="Sharpe Ratio" value={stats.sharpe_ratio?.toFixed(2) || 'N/A'} />
            <MetricRow label="Return %" value={`${((stats.total_pnl / parseFloat(config.initial_capital)) * 100).toFixed(2)}%`} color={stats.total_pnl > 0 ? 'emerald' : 'rose'} />
          </div>
        </Card>

        <Card variant="elevated">
          <h3 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
            <span>🎯</span> RISK METRICS
          </h3>
          
          <div className="space-y-3">
            <MetricRow label="Max Consecutive Wins" value={stats.max_consecutive_wins || 0} />
            <MetricRow label="Max Consecutive Losses" value={stats.max_consecutive_losses || 0} />
            <MetricRow label="Risk/Reward" value={`1:${(stats.avg_win / Math.abs(stats.avg_loss)).toFixed(2)}`} />
            <MetricRow label="Recovery Factor" value={(stats.total_pnl / Math.abs(stats.max_drawdown * parseFloat(config.initial_capital))).toFixed(2)} />
          </div>
        </Card>
      </div>

      {/* Trade Ledger */}
      <Card variant="elevated">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-200 flex items-center gap-2">
            <span>📋</span> TRADE LEDGER
          </h3>
          <Badge variant="success" size="md">
            {trades.length} TRADES
          </Badge>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left py-3 px-4 text-gray-500 font-semibold">#</th>
                <th className="text-left py-3 px-4 text-gray-500 font-semibold">Side</th>
                <th className="text-right py-3 px-4 text-gray-500 font-semibold">Entry</th>
                <th className="text-right py-3 px-4 text-gray-500 font-semibold">Exit</th>
                <th className="text-right py-3 px-4 text-gray-500 font-semibold">P/L</th>
                <th className="text-right py-3 px-4 text-gray-500 font-semibold">R</th>
                <th className="text-right py-3 px-4 text-gray-500 font-semibold">Balance</th>
              </tr>
            </thead>
            <tbody>
              {trades.slice(0, 20).map((trade, idx) => (
                <motion.tr
                  key={idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.02 }}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                >
                  <td className="py-3 px-4 text-gray-400 font-mono">{idx + 1}</td>
                  <td className="py-3 px-4">
                    <Badge variant={trade.side === 'long' ? 'success' : 'error'} size="sm">
                      {trade.side?.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-gray-300">${trade.entry?.toFixed(2)}</td>
                  <td className="py-3 px-4 text-right font-mono text-gray-300">${trade.exit_price?.toFixed(2)}</td>
                  <td className="py-3 px-4 text-right font-mono font-bold" style={{ color: trade.pnl > 0 ? theme.colors.accent.emerald : theme.colors.accent.rose }}>
                    ${trade.pnl?.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-gray-400">{trade.r_multiple?.toFixed(2)}R</td>
                  <td className="py-3 px-4 text-right font-mono font-semibold text-cyan-400">${trade.balance?.toFixed(2)}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
          
          {trades.length > 20 && (
            <div className="text-center py-4 text-gray-600 text-xs">
              Showing 20 of {trades.length} trades
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  );
}

function EmptyState({ dataLoaded }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <Card>
        <div className="text-center py-16">
          <motion.div
            animate={{ 
              y: [0, -10, 0],
              rotate: [0, 5, -5, 0]
            }}
            transition={{ duration: 3, repeat: Infinity }}
            className="text-6xl mb-4"
          >
            📈
          </motion.div>
          
          <h3 className="text-xl font-bold text-gray-300 mb-2">
            {dataLoaded ? 'Ready to Backtest' : 'No Data Available'}
          </h3>
          <p className="text-gray-500 mb-6">
            {dataLoaded 
              ? 'Configure your risk parameters and TP/SL ladder, then run the backtest'
              : 'Please upload historical data before running backtest'}
          </p>
          
          <div className="max-w-md mx-auto text-left space-y-2 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <span className="text-emerald-400">•</span>
              <span>Simulates trades with dynamic position sizing</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-cyan-400">•</span>
              <span>Implements 3-tier TP/SL ladder for optimal exits</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-amber-400">•</span>
              <span>Provides comprehensive performance metrics</span>
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

// ============================================================================
// UTILITY COMPONENTS
// ============================================================================

function MetricRow({ label, value, color = 'default' }) {
  const colors = {
    emerald: theme.colors.accent.emerald,
    rose: theme.colors.accent.rose,
    cyan: theme.colors.accent.cyan,
    amber: theme.colors.accent.amber,
    default: theme.colors.text.primary,
  };

  return (
    <div className="flex items-center justify-between p-3 bg-black/20 rounded-lg border border-gray-800/30">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="font-mono font-bold" style={{ color: colors[color] }}>
        {value}
      </span>
    </div>
  );
}
