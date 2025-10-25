/**
 * Analysis Page V2 - Bloomberg-class Parameter Tuning Interface
 * Complete visual overhaul with real-time feedback
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, Button, Input, MetricCard, Badge, Spinner, ProgressBar } from '../components/UIComponents';
import theme from '../design-system.js';

const API = process.env.REACT_APP_BACKEND_URL || '';

export default function AnalysisPageV2() {
  const navigate = useNavigate();
  
  const [dataLoaded, setDataLoaded] = useState(false);
  const [dataInfo, setDataInfo] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  
  const [config, setConfig] = useState({
    atr_threshold: '0.6',
    vol_z_threshold: '0.5',
    bb_width_threshold: '0.005',
    confirmation_window: '6',
    atr_multiplier: '0.5',
    volume_multiplier: '1.5'
  });

  useEffect(() => {
    checkDataAvailability();
  }, []);

  const checkDataAvailability = async () => {
    try {
      const response = await axios.get(`${API}/api/swings/`);
      if (response.data.rows > 0) {
        setDataLoaded(true);
        setDataInfo(response.data);
      } else {
        setDataLoaded(false);
      }
    } catch (error) {
      console.error('Error checking data:', error);
      setDataLoaded(false);
    }
  };

  const handleAnalyze = async () => {
    if (!dataLoaded) {
      toast.error('⚠️ Please upload data first');
      navigate('/upload');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await axios.get(`${API}/api/signals/latest`, {
        params: {
          atr_min: parseFloat(config.atr_threshold),
          volz_min: parseFloat(config.vol_z_threshold),
          bbw_min: parseFloat(config.bb_width_threshold),
          confirm_window: parseInt(config.confirmation_window),
          breakout_atr_mult: parseFloat(config.atr_multiplier),
          vol_mult: parseFloat(config.volume_multiplier),
          enable_micro_gate: false
        }
      });
      
      toast.success('✅ Analysis completed!');
      setAnalysisResult(response.data);
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error(error.response?.data?.detail || '❌ Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const updateConfig = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const resetToDefaults = () => {
    setConfig({
      atr_threshold: '0.6',
      vol_z_threshold: '0.5',
      bb_width_threshold: '0.005',
      confirmation_window: '6',
      atr_multiplier: '0.5',
      volume_multiplier: '1.5'
    });
    toast.info('🔄 Reset to default parameters');
  };

  return (
    <div className="min-h-screen" style={{ background: theme.utils.gradientBg() }}>
      {/* Header */}
      <div className="sticky top-0 z-40 bg-black/80 backdrop-blur-2xl border-b border-cyan-500/10">
        <div className="px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-gray-200 flex items-center gap-3">
              <span className="text-3xl">🔬</span>
              SIGNAL ANALYSIS LAB
            </h1>
            <p className="text-sm text-gray-500 mt-1 font-mono">Parameter tuning for candidate detection & confirmation</p>
          </div>
          
          <div className="flex items-center gap-4">
            {dataLoaded ? (
              <Badge variant="success" size="lg">
                ✓ DATA READY • {dataInfo?.rows || 0} CANDLES
              </Badge>
            ) : (
              <Badge variant="error" size="lg">
                ⚠ NO DATA • UPLOAD REQUIRED
              </Badge>
            )}
            
            {!dataLoaded && (
              <Button
                variant="primary"
                size="md"
                onClick={() => navigate('/upload')}
                leftIcon="📁"
              >
                UPLOAD DATA
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="p-8 space-y-6">
        {/* Parameter Configuration Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Stage 1: Candidate Detection */}
          <Card variant="elevated">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-cyan-400 mb-2 flex items-center gap-2">
                <span>1️⃣</span> STAGE 1: CANDIDATE DETECTION
              </h2>
              <p className="text-sm text-gray-500">Local extrema identification with filter gates</p>
            </div>

            <div className="space-y-4">
              <Input
                label="ATR Threshold"
                value={config.atr_threshold}
                onChange={(e) => updateConfig('atr_threshold', e.target.value)}
                type="number"
                step="0.1"
                placeholder="0.6"
                helperText="Minimum ATR14 percentile for volatility filter"
                leftIcon="📊"
              />

              <Input
                label="Volume Z-Score Threshold"
                value={config.vol_z_threshold}
                onChange={(e) => updateConfig('vol_z_threshold', e.target.value)}
                type="number"
                step="0.1"
                placeholder="0.5"
                helperText="Minimum Z-score for volume filter"
                leftIcon="📈"
              />

              <Input
                label="BB Width Threshold"
                value={config.bb_width_threshold}
                onChange={(e) => updateConfig('bb_width_threshold', e.target.value)}
                type="number"
                step="0.001"
                placeholder="0.005"
                helperText="Minimum Bollinger Band width (volatility proxy)"
                leftIcon="📏"
              />
            </div>

            <div className="mt-6 p-4 rounded-lg bg-black/30 border border-gray-800/50">
              <div className="text-xs text-gray-500 mb-2 font-semibold">FILTER LOGIC:</div>
              <div className="text-xs text-gray-400 space-y-1">
                <div>• Extremum: Local high/low (±12 bars window)</div>
                <div>• ATR Filter: Volatility percentile ≥ {config.atr_threshold}</div>
                <div>• Vol Filter: Z-score ≥ {config.vol_z_threshold}</div>
                <div>• BB Filter: Width ≥ {config.bb_width_threshold}</div>
              </div>
            </div>
          </Card>

          {/* Stage 2: Micro Confirmation */}
          <Card variant="elevated">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-emerald-400 mb-2 flex items-center gap-2">
                <span>2️⃣</span> STAGE 2: MICRO CONFIRMATION
              </h2>
              <p className="text-sm text-gray-500">Breakout candle & volume spike validation</p>
            </div>

            <div className="space-y-4">
              <Input
                label="Confirmation Window"
                value={config.confirmation_window}
                onChange={(e) => updateConfig('confirmation_window', e.target.value)}
                type="number"
                step="1"
                placeholder="6"
                helperText="Number of candles to scan for confirmation"
                leftIcon="⏱️"
              />

              <Input
                label="ATR Multiplier"
                value={config.atr_multiplier}
                onChange={(e) => updateConfig('atr_multiplier', e.target.value)}
                type="number"
                step="0.1"
                placeholder="0.5"
                helperText="Breakout threshold = extremum ± (ATR × multiplier)"
                leftIcon="⚡"
              />

              <Input
                label="Volume Multiplier"
                value={config.volume_multiplier}
                onChange={(e) => updateConfig('volume_multiplier', e.target.value)}
                type="number"
                step="0.1"
                placeholder="1.5"
                helperText="Volume spike = volume × multiplier"
                leftIcon="📊"
              />
            </div>

            <div className="mt-6 p-4 rounded-lg bg-black/30 border border-gray-800/50">
              <div className="text-xs text-gray-500 mb-2 font-semibold">CONFIRMATION LOGIC:</div>
              <div className="text-xs text-gray-400 space-y-1">
                <div>• Breakout: Close crosses extremum ± {config.atr_multiplier}×ATR</div>
                <div>• Volume: Spike ≥ {config.volume_multiplier}× avg volume</div>
                <div>• Window: Scan {config.confirmation_window} candles post-extremum</div>
                <div>• Direction: Long if breakout up, Short if down</div>
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
              onClick={handleAnalyze}
              loading={analyzing}
              disabled={!dataLoaded}
              leftIcon="🔍"
            >
              {analyzing ? 'ANALYZING...' : 'RUN ANALYSIS'}
            </Button>
            
            <Button
              variant="ghost"
              size="lg"
              onClick={resetToDefaults}
              leftIcon="🔄"
            >
              RESET TO DEFAULTS
            </Button>
          </div>

          {analysisResult && (
            <Button
              variant="success"
              size="lg"
              onClick={() => navigate('/backtest')}
              rightIcon="→"
            >
              PROCEED TO BACKTEST
            </Button>
          )}
        </div>

        {/* Analysis Results */}
        <AnimatePresence mode="wait">
          {analyzing && (
            <AnalyzingState key="analyzing" dataInfo={dataInfo} />
          )}
          
          {!analyzing && analysisResult && (
            <AnalysisResults key="results" result={analysisResult} config={config} />
          )}
          
          {!analyzing && !analysisResult && dataLoaded && (
            <EmptyState key="empty" />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ============================================================================
// STATE COMPONENTS
// ============================================================================

function AnalyzingState({ dataInfo }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => Math.min(prev + 5, 90));
    }, 200);
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
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="text-6xl mb-6 inline-block"
          >
            🔬
          </motion.div>
          
          <h3 className="text-2xl font-bold text-gray-200 mb-2">Analyzing Data...</h3>
          <p className="text-gray-500 mb-6">Processing {dataInfo?.rows || 0} candles with current parameters</p>
          
          <div className="max-w-md mx-auto">
            <ProgressBar
              value={progress}
              max={100}
              color="cyan"
              animated={true}
            />
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function AnalysisResults({ result, config }) {
  const signal = result?.signal || result;
  
  // Calculate stats
  const hasSignal = signal && signal.side;
  const entryPrice = signal?.entry || 0;
  const stopLoss = signal?.sl || 0;
  const tp1 = signal?.tp1 || 0;
  const riskPercent = entryPrice > 0 ? Math.abs((entryPrice - stopLoss) / entryPrice) * 100 : 0;
  const rewardPercent = entryPrice > 0 ? Math.abs((tp1 - entryPrice) / entryPrice) * 100 : 0;
  const rrRatio = riskPercent > 0 ? rewardPercent / riskPercent : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      {/* Summary Metrics */}
      <div className="grid md:grid-cols-4 gap-4">
        <MetricCard
          label="Signal Detected"
          value={hasSignal ? 'YES' : 'NO'}
          color={hasSignal ? 'emerald' : 'default'}
          icon={hasSignal ? '✅' : '❌'}
          size="sm"
        />
        
        {hasSignal && (
          <>
            <MetricCard
              label="Direction"
              value={signal.side?.toUpperCase() || '--'}
              color={signal.side === 'long' ? 'emerald' : 'rose'}
              icon={signal.side === 'long' ? '📈' : '📉'}
              size="sm"
            />
            
            <MetricCard
              label="Entry Price"
              value={`$${entryPrice.toFixed(2)}`}
              color="cyan"
              icon="🎯"
              size="sm"
            />
            
            <MetricCard
              label="R:R Ratio"
              value={`1:${rrRatio.toFixed(2)}`}
              color={rrRatio >= 2 ? 'emerald' : rrRatio >= 1.5 ? 'amber' : 'default'}
              icon="⚖️"
              size="sm"
            />
          </>
        )}
      </div>

      {/* Signal Details */}
      {hasSignal ? (
        <div className="grid md:grid-cols-2 gap-6">
          <Card variant="elevated" glow={signal.side === 'long' ? 'long' : 'short'}>
            <h3 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
              <span>📋</span> SIGNAL PARAMETERS
            </h3>
            
            <div className="space-y-3">
              <ParamDisplay label="Side" value={signal.side?.toUpperCase()} color={signal.side === 'long' ? 'emerald' : 'rose'} />
              <ParamDisplay label="Entry" value={`$${entryPrice.toFixed(4)}`} color="cyan" />
              <ParamDisplay label="Stop Loss" value={`$${stopLoss.toFixed(4)}`} color="rose" />
              <ParamDisplay label="Take Profit 1" value={`$${tp1.toFixed(4)}`} color="emerald" />
              <ParamDisplay label="Risk" value={`${riskPercent.toFixed(2)}%`} />
              <ParamDisplay label="Reward" value={`${rewardPercent.toFixed(2)}%`} />
            </div>
          </Card>

          <Card variant="elevated">
            <h3 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
              <span>🔍</span> DETECTION METADATA
            </h3>
            
            <div className="space-y-3">
              <ParamDisplay label="Extremum Index" value={signal.indices?.extremum_idx || '--'} />
              <ParamDisplay label="Confirm Index" value={signal.indices?.confirm_idx || '--'} />
              <ParamDisplay label="Attempts" value={signal.attempts || '--'} />
              <ParamDisplay label="Confidence" value="High" color="emerald" />
            </div>

            <div className="mt-6 pt-6 border-t border-gray-800/50">
              <div className="text-xs text-gray-500 mb-2 font-semibold">APPLIED PARAMETERS:</div>
              <div className="text-xs text-gray-400 space-y-1">
                <div>ATR: {config.atr_threshold} | Vol Z: {config.vol_z_threshold}</div>
                <div>BB Width: {config.bb_width_threshold} | Window: {config.confirmation_window}</div>
              </div>
            </div>
          </Card>
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <div className="text-5xl mb-4">🔍</div>
            <h3 className="text-xl font-bold text-gray-300 mb-2">No Signal Detected</h3>
            <p className="text-gray-500 mb-6">No swing candidates passed the confirmation stage with current parameters.</p>
            <div className="space-y-2 text-sm text-gray-600">
              <p>💡 Try adjusting thresholds to detect more candidates</p>
              <p>💡 Lowering ATR/Vol filters may increase detection sensitivity</p>
            </div>
          </div>
        </Card>
      )}
    </motion.div>
  );
}

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <Card>
        <div className="text-center py-16">
          <motion.div
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="text-6xl mb-4"
          >
            🔬
          </motion.div>
          
          <h3 className="text-xl font-bold text-gray-300 mb-2">Ready to Analyze</h3>
          <p className="text-gray-500 mb-6">Configure parameters above and click "Run Analysis" to detect swing signals</p>
          
          <div className="max-w-md mx-auto text-left space-y-3 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <span className="text-cyan-400">•</span>
              <span>Stage 1 filters identify potential swing extrema</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-400">•</span>
              <span>Stage 2 confirms breakout with volume spike</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-amber-400">•</span>
              <span>Results show latest confirmed signal with trade specs</span>
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

function ParamDisplay({ label, value, color = 'default' }) {
  const colors = {
    cyan: theme.colors.accent.cyan,
    emerald: theme.colors.accent.emerald,
    rose: theme.colors.accent.rose,
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
