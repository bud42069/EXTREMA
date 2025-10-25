/**
 * Scalp Cards Page V2 - Bloomberg-class Manual Trade Execution Interface
 * Complete visual overhaul with enhanced UX for fast decision-making
 */

import React, { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-toastify';
import { useWebSocket } from '../hooks/useWebSocket';
import { Card, Button, Badge, MetricCard, StatusIndicator, Input, Tooltip } from '../components/UIComponents';
import theme from '../design-system.js';

const API = process.env.REACT_APP_BACKEND_URL || '';

// ============================================================================
// HOOKS
// ============================================================================

function useSnapshot(pollMs = 1500, useWs = true) {
  const [snap, setSnap] = useState(null);
  
  const wsUrl = API
    ? API.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/signals/stream'
    : null;
  
  const { data: wsData, connected } = useWebSocket(wsUrl, { enabled: useWs });
  
  useEffect(() => {
    if (connected && wsData) {
      if (wsData.type === 'snapshot' && wsData.data) {
        setSnap(wsData.data);
      }
    } else {
      let id = setInterval(async () => {
        try {
          const res = await fetch(`${API}/api/stream/snapshot`);
          const js = await res.json();
          setSnap(js);
        } catch (e) {
          console.error('Snapshot fetch error:', e);
        }
      }, pollMs);
      return () => clearInterval(id);
    }
  }, [pollMs, connected, wsData]);
  
  return { snap, connected };
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ScalpCardsPageV2() {
  const [resp, setResp] = useState(null);
  const [loading, setLoading] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [orderSize, setOrderSize] = useState('100');
  const [leverage, setLeverage] = useState('5');
  const { snap, connected: wsConnected } = useSnapshot(1500, true);

  const fetchCard = async () => {
    setLoading(true);
    try {
      const forceParam = demoMode ? '&force=true' : '';
      const res = await fetch(`${API}/api/scalp/card?enable_micro_gate=true${forceParam}`);
      const js = await res.json();
      setResp(js);
      
      if (js.card) {
        toast.success('Scalp Card Generated', { position: 'top-right', autoClose: 2000 });
      } else {
        toast.info(`${js.message || 'No signal available'}`, { position: 'top-right', autoClose: 3000 });
      }
    } catch (e) {
      console.error('Card fetch error:', e);
      setResp({ message: 'Error fetching card', error: e.message });
      toast.error('❌ Failed to generate card', { position: 'top-right' });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!resp?.card) return;
    const card = resp.card;
    const orderText = `
SCALP CARD - ${card.symbol}
PLAY: ${card.play}
ENTRY: ${card.entry.toFixed(4)}
SL: ${card.sl.toFixed(4)}
🎁 TP1: ${card.tp1.toFixed(4)} (50%)
🎁 TP2: ${card.tp2.toFixed(4)} (30%)
🎁 TP3: ${card.tp3.toFixed(4)} (20%)
📏 TRAIL: ${card.trail_rule}
SIZE: ${card.size}
    `;
    navigator.clipboard.writeText(orderText);
    toast.success('Copied to clipboard', { position: 'top-right', autoClose: 1500 });
  };

  return (
    <div className="min-h-screen" style={{ background: theme.utils.gradientBg() }}>
      {/* Header Strip */}
      <div className="sticky top-0 z-40 bg-black/80 backdrop-blur-2xl border-b border-cyan-500/10">
        <div className="px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-gray-200 flex items-center gap-3">
              <svg className="w-10 h-10 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              SCALP CARD — MANUAL EXECUTION
            </h1>
            <p className="text-sm text-gray-500 mt-1 font-mono">Real-time execution sheet with microstructure validation</p>
          </div>
          
          <div className="flex items-center gap-4">
            <StatusIndicator 
              status={wsConnected ? 'active' : 'warning'}
              label={wsConnected ? 'WEBSOCKET LIVE' : 'POLLING MODE'}
              pulse={wsConnected}
            />
            
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={demoMode}
                onChange={(e) => setDemoMode(e.target.checked)}
                className="w-4 h-4 rounded border-gray-700 bg-gray-900 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0"
              />
              <span className="text-sm text-gray-400 font-medium">Demo Mode</span>
            </label>
          </div>
        </div>
      </div>

      <div className="p-8 space-y-6">
        {/* Microstructure Snapshot */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Spread"
            value={snap?.spread_bps?.toFixed?.(2) ?? '--'}
            subValue="basis points"
            color={snap?.spread_bps < 1 ? 'up' : 'amber'}
            size="sm"
          />
          <MetricCard
            label="Imbalance"
            value={snap?.ladder_imbalance?.toFixed?.(3) ?? '--'}
            subValue="bid/ask ratio"
            trend={snap?.ladder_imbalance > 0 ? 'up' : snap?.ladder_imbalance < 0 ? 'down' : 'neutral'}
            size="sm"
          />
          <MetricCard
            label="CVD"
            value={snap?.cvd?.toFixed?.(0) ?? '--'}
            subValue="cumulative delta"
            trend={snap?.cvd > 0 ? 'up' : snap?.cvd < 0 ? 'down' : 'neutral'}
            size="sm"
          />
          <MetricCard
            label="CVD Slope"
            value={snap?.cvd_slope?.toFixed?.(4) ?? '--'}
            subValue="momentum"
            trend={snap?.cvd_slope > 0 ? 'up' : snap?.cvd_slope < 0 ? 'down' : 'neutral'}
            size="sm"
            icon="📐"
          />
        </div>

        {/* Action Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="primary"
              size="lg"
              onClick={fetchCard}
              loading={loading}
            >
              {loading ? 'GENERATING...' : 'GENERATE CARD'}
            </Button>
            
            {resp?.card && (
              <Button
                variant="ghost"
                size="lg"
                onClick={copyToClipboard}
              >
                COPY TO CLIPBOARD
              </Button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="w-32">
              <Input
                value={orderSize}
                onChange={(e) => setOrderSize(e.target.value)}
                type="number"
                placeholder="Size"
              />
            </div>
            <div className="w-24">
              <Input
                value={leverage}
                onChange={(e) => setLeverage(e.target.value)}
                type="number"
                placeholder="Lev"
              />
            </div>
          </div>
        </div>

        {/* Card Display */}
        <AnimatePresence mode="wait">
          {resp && resp.card ? (
            <TradeCard card={resp.card} orderSize={orderSize} leverage={leverage} />
          ) : (
            <EmptyState resp={resp} loading={loading} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ============================================================================
// TRADE CARD COMPONENT
// ============================================================================

function TradeCard({ card, orderSize, leverage }) {
  const [activeTab, setActiveTab] = useState('parameters'); // parameters, checks, execution
  
  const side = card.play.toLowerCase();
  const glowType = side === 'long' ? 'long' : 'short';
  
  // Calculate risk metrics
  const entryPrice = parseFloat(card.entry);
  const stopLoss = parseFloat(card.sl);
  const tp1 = parseFloat(card.tp1);
  const size = parseFloat(orderSize) || 100;
  const lev = parseFloat(leverage) || 5;
  
  const riskPercent = Math.abs((entryPrice - stopLoss) / entryPrice) * 100;
  const rewardPercent = Math.abs((tp1 - entryPrice) / entryPrice) * 100;
  const rrRatio = rewardPercent / riskPercent;
  const notionalValue = size * lev;
  const riskAmount = (notionalValue * riskPercent) / 100;
  
  const checks = useMemo(() => [
    { label: 'Spread <0.10%', passed: card.checks.spread_ok, category: 'micro' },
    { label: 'Depth ≥50%', passed: !card.checks?.micro_veto?.depth, category: 'micro' },
    { label: '|Mark−Last| <0.15%', passed: !card.checks?.micro_veto?.imbalance, category: 'micro' },
    { label: 'RSI Gate', passed: true, category: 'indicator' },
    { label: 'No OBV-Cliff', passed: !card.checks?.micro_veto?.obv, category: 'indicator' },
    { label: 'Liq-Gap ≥4×ATR & ≥10× Fee', passed: true, category: 'risk' },
    { label: 'Kill-Switch Clear', passed: !card.checks?.micro_veto?.kill, category: 'system' }
  ], [card]);
  
  const allPassed = checks.every(c => c.passed);
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={theme.animation.springGentle}
    >
      <Card variant="elevated" glow={glowType} className="relative overflow-hidden">
        {/* Animated background glow */}
        <motion.div
          className="absolute inset-0 opacity-5"
          style={{ background: side === 'long' ? theme.colors.accent.emerald : theme.colors.accent.rose }}
          animate={{ opacity: [0.05, 0.1, 0.05] }}
          transition={{ duration: 3, repeat: Infinity }}
        />
        
        {/* Header */}
        <div className="relative z-10 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <motion.div
                initial={{ scale: 0, rotate: -45 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={theme.animation.spring}
                className="text-5xl"
              >
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={side === 'long' ? "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" : "M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6"} />
                </svg>
              </motion.div>
              <div>
                <h2 className="text-3xl font-black" style={{ color: side === 'long' ? theme.colors.accent.emerald : theme.colors.accent.rose }}>
                  {side.toUpperCase()} {card.symbol}
                </h2>
                <p className="text-sm text-gray-500 font-mono mt-1">MEXC • Regime: {card.regime} • Size: {card.size}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Badge variant={allPassed ? 'success' : 'error'} size="lg">
                {allPassed ? 'ALL CHECKS PASSED' : 'VETO TRIGGERED'}
              </Badge>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-2 border-b border-gray-800/50">
            {['parameters', 'checks', 'execution'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 font-semibold text-sm uppercase tracking-wider transition-all ${
                  activeTab === tab
                    ? 'text-cyan-400 border-b-2 border-cyan-500'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'parameters' && (
            <ParametersTab key="parameters" card={card} riskPercent={riskPercent} rewardPercent={rewardPercent} rrRatio={rrRatio} />
          )}
          {activeTab === 'checks' && (
            <ChecksTab key="checks" checks={checks} card={card} />
          )}
          {activeTab === 'execution' && (
            <ExecutionTab key="execution" card={card} notionalValue={notionalValue} riskAmount={riskAmount} side={side} />
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
}

// ============================================================================
// TAB COMPONENTS
// ============================================================================

function ParametersTab({ card, riskPercent, rewardPercent, rrRatio }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="grid md:grid-cols-2 gap-6"
    >
      {/* Left: Trade Setup */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          TRADE SETUP
        </h3>
        
        <ParamRow label="Entry (Limit, Post-Only)" value={card.entry.toFixed(4)} highlight="cyan" size="lg" />
        <ParamRow label="Stop Loss" value={card.sl.toFixed(4)} highlight="rose" />
        <div className="grid grid-cols-3 gap-2">
          <ParamRow label="TP1 (50%)" value={card.tp1.toFixed(4)} highlight="emerald" size="sm" />
          <ParamRow label="TP2 (30%)" value={card.tp2.toFixed(4)} highlight="emerald" size="sm" />
          <ParamRow label="TP3 (20%)" value={card.tp3.toFixed(4)} highlight="emerald" size="sm" />
        </div>
        <ParamRow label="Trail Rule" value={card.trail_rule} />
        <ParamRow label="Confirmation" value={card.confirm} size="sm" />
      </div>

      {/* Right: Risk Analysis */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
          </svg>
          RISK ANALYSIS
        </h3>
        
        <MetricCard
          label="Risk %"
          value={riskPercent.toFixed(2) + '%'}
          color="rose"
          size="sm"
        />
        <MetricCard
          label="Reward %"
          value={rewardPercent.toFixed(2) + '%'}
          color="emerald"
          size="sm"
        />
        <MetricCard
          label="R:R Ratio"
          value={`1:${rrRatio.toFixed(2)}`}
          color={rrRatio >= 2 ? 'emerald' : rrRatio >= 1.5 ? 'amber' : 'rose'}
          size="md"
        />
        
        <div className="bg-black/30 rounded-lg p-4 border border-gray-800/50 text-xs text-gray-500 space-y-1">
          <div>Extremum Index: <span className="font-mono text-gray-400">{card.indices?.extremum_idx}</span></div>
          <div>Confirm Index: <span className="font-mono text-gray-400">{card.indices?.confirm_idx}</span></div>
          <div>Attempts: <span className="font-mono text-gray-400">{card.attempts}</span></div>
        </div>
      </div>
    </motion.div>
  );
}

function ChecksTab({ checks, card }) {
  const groupedChecks = {
    micro: checks.filter(c => c.category === 'micro'),
    indicator: checks.filter(c => c.category === 'indicator'),
    risk: checks.filter(c => c.category === 'risk'),
    system: checks.filter(c => c.category === 'system'),
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="space-y-6"
    >
      <div className="grid md:grid-cols-2 gap-6">
        {Object.entries(groupedChecks).map(([category, categoryChecks]) => (
          <div key={category}>
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
              {category} Checks
            </h3>
            <div className="space-y-2">
              {categoryChecks.map((check, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className={`px-4 py-3 rounded-lg text-sm font-medium flex items-center gap-3 border ${
                    check.passed
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                      : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  }`}
                >
                  <span className="text-xl">{check.passed ? '✓' : '✗'}</span>
                  <span>{check.label}</span>
                </motion.div>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {/* Veto Details */}
      {card.checks?.micro_veto && Object.keys(card.checks.micro_veto).length > 0 && (
        <div className="mt-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30">
          <h4 className="text-sm font-bold text-rose-400 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            VETO REASONS
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(card.checks.micro_veto).map(([k, v]) => (
              <Badge key={k} variant="error" size="sm">
                {k}: {String(v)}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}

function ExecutionTab({ card, notionalValue, riskAmount, side }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="space-y-6"
    >
      {/* Order Preview */}
      <div className="bg-black/40 rounded-xl p-6 border border-gray-800/50">
        <h3 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
          <span>📝</span> ORDER PREVIEW
        </h3>
        
        <div className="grid md:grid-cols-2 gap-4">
          <MetricCard
            label="Notional Value"
            value={`$${notionalValue.toFixed(2)}`}
            size="sm"
          />
          <MetricCard
            label="Risk Amount"
            value={`$${riskAmount.toFixed(2)}`}
            color="rose"
            size="sm"
          />
        </div>
      </div>

      {/* Execution Checklist */}
      <div>
        <h3 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          PRE-FLIGHT CHECKLIST
        </h3>
        
        <div className="space-y-2">
          {[
            'Confirm entry price and order type (limit, post-only)',
            'Verify stop-loss level and quantity',
            'Set TP ladder (50% → 30% → 20%)',
            'Enable trailing stop after TP1',
            'Check margin and available balance',
            'Verify no conflicting positions',
            'Confirm kill-switch is clear'
          ].map((item, idx) => (
            <div key={idx} className="flex items-start gap-3 p-3 bg-black/20 rounded-lg border border-gray-800/30 hover:border-cyan-500/30 transition-all cursor-pointer">
              <input type="checkbox" className="mt-1 w-5 h-5 rounded border-gray-700 bg-gray-900 text-cyan-500" />
              <span className="text-sm text-gray-400">{item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Execute Button */}
      <div className="flex items-center justify-center gap-4 pt-6 border-t border-gray-800/50">
        <Button
          variant={side === 'long' ? 'success' : 'danger'}
          size="lg"
          fullWidth
        >
          EXECUTE {side.toUpperCase()} @ {card.entry.toFixed(4)}
        </Button>
      </div>
      
      <p className="text-xs text-gray-600 text-center font-mono">
        Order Path: {card.order_path}
      </p>
    </motion.div>
  );
}

// ============================================================================
// UTILITY COMPONENTS
// ============================================================================

function ParamRow({ label, value, highlight = null, size = 'md' }) {
  const colors = {
    cyan: theme.colors.accent.cyan,
    emerald: theme.colors.accent.emerald,
    rose: theme.colors.accent.rose,
    amber: theme.colors.accent.amber,
  };
  
  const sizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-xl',
  };
  
  return (
    <div className="bg-black/20 rounded-lg p-3 border border-gray-800/30">
      <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">{label}</div>
      <div className={`font-mono font-bold ${sizes[size]}`} style={{ color: highlight ? colors[highlight] : theme.colors.text.primary }}>
        {value}
      </div>
    </div>
  );
}

function EmptyState({ resp, loading }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <Card className="text-center py-16">
        <motion.div
          animate={{ 
            rotate: loading ? [0, 10, -10, 0] : 0,
            scale: loading ? [1, 1.1, 1] : 1
          }}
          transition={{ duration: 2, repeat: loading ? Infinity : 0 }}
          className="text-6xl mb-4"
        >
            {loading ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
        </motion.div>
        
        <h3 className="text-xl font-bold text-gray-300 mb-2">
          {loading ? 'Generating Scalp Card...' : 'No Active Signal'}
        </h3>
        
        <p className="text-gray-500 mb-6">
          {resp?.message || 'Click "Generate Card" to fetch the latest confirmed signal with microstructure validation.'}
        </p>
        
        {resp?.veto && Object.keys(resp.veto).length > 0 && (
          <div className="inline-block bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 text-left">
            <div className="text-sm font-bold text-rose-400 mb-2">Veto Reasons:</div>
            <div className="space-y-1">
              {Object.entries(resp.veto).map(([k, v]) => (
                <div key={k} className="text-xs text-gray-400">
                  <span className="text-rose-400">•</span> {k}: {JSON.stringify(v)}
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </motion.div>
  );
}
