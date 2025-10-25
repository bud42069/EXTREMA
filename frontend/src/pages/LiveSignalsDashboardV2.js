import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || '';

// Audio notification system
const playNotificationSound = (type = 'success') => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();
  
  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);
  
  if (type === 'long') {
    oscillator.frequency.value = 800; // Higher pitch for long
  } else if (type === 'short') {
    oscillator.frequency.value = 400; // Lower pitch for short
  } else {
    oscillator.frequency.value = 600; // Neutral
  }
  
  gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
  
  oscillator.start(audioContext.currentTime);
  oscillator.stop(audioContext.currentTime + 0.3);
};

// Command Palette Component
const CommandPalette = ({ isOpen, onClose, onCommand }) => {
  const [query, setQuery] = useState('');
  const inputRef = useRef(null);
  
  const commands = [
    { id: 'start', label: 'Start Monitor', hotkey: 'S' },
    { id: 'stop', label: 'Stop Monitor', hotkey: 'X' },
    { id: 'toggle-log', label: 'Toggle Trade Log', hotkey: 'L' },
    { id: 'scalp-card', label: 'Generate Scalp Card', hotkey: 'C' },
    { id: 'clear-signals', label: 'Clear Signal Stack', hotkey: '' },
  ];
  
  const filteredCommands = commands.filter(cmd => 
    cmd.label.toLowerCase().includes(query.toLowerCase())
  );
  
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);
  
  if (!isOpen) return null;
  
  return (
    <div 
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-start justify-center pt-32"
      onClick={onClose}
    >
      <div 
        className="bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-700 rounded-2xl w-full max-w-2xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="p-4 border-b border-gray-800">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search..."
            className="w-full bg-transparent text-white text-lg placeholder-gray-500 outline-none"
          />
        </div>
        
        {/* Command List */}
        <div className="max-h-96 overflow-y-auto">
          {filteredCommands.map((cmd) => (
            <button
              key={cmd.id}
              onClick={() => {
                onCommand(cmd.id);
                onClose();
              }}
              className="w-full px-6 py-3 flex items-center justify-between hover:bg-gray-800/50 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <span className="text-gray-300">{cmd.label}</span>
              </div>
              {cmd.hotkey && (
                <kbd className="px-2 py-1 bg-gray-800 text-gray-400 text-xs rounded font-mono">
                  {cmd.hotkey}
                </kbd>
              )}
            </button>
          ))}
        </div>
        
        <div className="p-3 border-t border-gray-800 text-xs text-gray-500 flex items-center justify-between">
          <span>Navigate with ↑↓ • Execute with ↵</span>
          <span>ESC to close</span>
        </div>
      </div>
    </div>
  );
};

// CVD Slope Chart Component (Enhanced with Recharts)
const CVDSlopeChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-32 flex items-center justify-center text-gray-600 text-xs">
        Awaiting data...
      </div>
    );
  }
  
  const chartData = data.map((value, index) => ({
    index,
    value: value || 0
  }));
  
  return (
    <ResponsiveContainer width="100%" height={128}>
      <AreaChart data={chartData} margin={{ top: 5, right: 0, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="cvdGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
          </linearGradient>
        </defs>
        <YAxis hide domain={['auto', 'auto']} />
        <Area
          type="monotone"
          dataKey="value"
          stroke="#06b6d4"
          strokeWidth={2}
          fill="url(#cvdGradient)"
          animationDuration={300}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

// Trade Log Component (Enhanced with Animation)
const TradeLog = ({ signals, isOpen, onToggle }) => {
  if (!isOpen) {
    return (
      <motion.button
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        onClick={onToggle}
        className="fixed bottom-6 left-1/2 -translate-x-1/2 px-6 py-3 bg-gray-900/95 backdrop-blur-xl border border-cyan-500/30 rounded-full text-sm font-semibold text-gray-300 hover:bg-gray-800 hover:border-cyan-500/50 transition-all flex items-center gap-3 shadow-lg shadow-cyan-500/10 group"
      >
        <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span>Trade Log</span>
        <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded-full text-xs font-bold">
          {signals.length}
        </span>
        <span className="text-xs text-gray-500 group-hover:text-cyan-400 transition-colors">↑</span>
      </motion.button>
    );
  }
  
  return (
    <motion.div 
      initial={{ y: "100%" }}
      animate={{ y: 0 }}
      exit={{ y: "100%" }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-gray-950 via-gray-900/98 to-gray-900/95 backdrop-blur-2xl border-t border-cyan-500/20 z-40 shadow-2xl shadow-cyan-500/10"
    >
      <div className="flex items-center justify-between px-8 py-4 border-b border-gray-800/50">
        <div className="flex items-center gap-3">
          <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider">Trade Execution Log</h3>
          <span className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded text-xs font-mono">
            {signals.length} SIGNALS
          </span>
        </div>
        <button
          onClick={onToggle}
          className="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-700 text-gray-400 hover:text-white hover:bg-gray-800 hover:border-gray-600 transition-all"
        >
          ↓
        </button>
      </div>
      
      <div className="max-h-72 overflow-y-auto p-6">
        {signals.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-3 opacity-40">📭</div>
            <div className="text-gray-500 text-sm font-medium">No signals logged yet</div>
            <div className="text-gray-600 text-xs mt-1">Confirmed signals will appear here</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence>
              {signals.map((signal, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.2 }}
                  className={`relative rounded-xl p-4 border-2 ${
                    signal.side === 'long'
                      ? 'bg-gradient-to-br from-cyan-500/10 to-transparent border-cyan-500/40 hover:border-cyan-500/60'
                      : 'bg-gradient-to-br from-pink-500/10 to-transparent border-pink-500/40 hover:border-pink-500/60'
                  } transition-all hover:scale-[1.02] cursor-pointer group`}
                >
                  {/* Tier Badge */}
                  <div className="absolute top-3 right-3">
                    <div className={`px-2 py-1 rounded-lg text-xs font-bold border ${
                      signal.tier === 'A'
                        ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
                        : 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                    }`}>
                      TIER {signal.tier || 'B'}
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3 mb-3">
                    <div className={`${signal.side === 'long' ? 'text-cyan-400' : 'text-pink-400'}`}>
                      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={signal.side === 'long' ? "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" : "M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6"} />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <div className={`text-lg font-bold uppercase mb-1 ${
                        signal.side === 'long' ? 'text-cyan-300' : 'text-pink-300'
                      }`}>
                        {signal.side}
                      </div>
                      <div className="text-xs text-gray-500 font-mono">
                        @ {signal.entry ? `$${signal.entry.toFixed(2)}` : '--'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-black/20 rounded-lg p-2 border border-gray-800/50">
                      <div className="text-gray-500 mb-1">Stop Loss</div>
                      <div className="font-mono text-rose-400">${signal.sl?.toFixed(2) || '--'}</div>
                    </div>
                    <div className="bg-black/20 rounded-lg p-2 border border-gray-800/50">
                      <div className="text-gray-500 mb-1">Target (TP1)</div>
                      <div className="font-mono text-emerald-400">${signal.tp1?.toFixed(2) || '--'}</div>
                    </div>
                  </div>
                  
                  <div className="mt-3 pt-3 border-t border-gray-800/50 flex items-center justify-between">
                    <div>
                      <div className="text-xs text-gray-500">R:R Ratio</div>
                      <div className="text-sm font-bold text-gray-300">
                        1:{signal.tp1 && signal.entry && signal.sl 
                          ? ((signal.tp1 - signal.entry) / (signal.entry - signal.sl)).toFixed(1)
                          : '--'}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Confluence</div>
                      <div className="text-sm font-bold text-cyan-400">
                        {signal.confluence_score?.toFixed(0) || '--'}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default function LiveSignalsDashboardV2() {
  const [monitorStatus, setMonitorStatus] = useState({ running: false, last_price: 0, candles_count: 0 });
  const [signals, setSignals] = useState([]);
  const [microSnap, setMicroSnap] = useState(null);
  const [mtfStatus, setMtfStatus] = useState(null);
  const [mtfConfluence, setMtfConfluence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cvdHistory, setCvdHistory] = useState([]);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [tradeLogOpen, setTradeLogOpen] = useState(false);
  const previousSignalsCount = useRef(0);

  useEffect(() => {
    fetchInitialData();
    
    const statusInterval = setInterval(fetchMonitorStatus, 3000);
    const snapInterval = setInterval(fetchMicroSnapshot, 2000);
    const mtfInterval = setInterval(fetchMtfData, 5000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(snapInterval);
      clearInterval(mtfInterval);
    };
  }, []);

  // Hotkey listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Command Palette: Cmd+K or Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
      
      // ESC to close command palette
      if (e.key === 'Escape' && commandPaletteOpen) {
        setCommandPaletteOpen(false);
      }
      
      // Hotkeys (only when command palette is closed)
      if (!commandPaletteOpen) {
        if (e.key.toLowerCase() === 's' && !e.metaKey && !e.ctrlKey) {
          handleStartMonitor();
        } else if (e.key.toLowerCase() === 'x' && !e.metaKey && !e.ctrlKey) {
          handleStopMonitor();
        } else if (e.key.toLowerCase() === 'l' && !e.metaKey && !e.ctrlKey) {
          setTradeLogOpen(prev => !prev);
        } else if (e.key.toLowerCase() === 'c' && !e.metaKey && !e.ctrlKey) {
          window.location.href = '/scalp-cards';
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen]);

  // Check for new signals and play sound
  useEffect(() => {
    if (signals.length > previousSignalsCount.current && previousSignalsCount.current > 0) {
      const newSignal = signals[signals.length - 1];
      playNotificationSound(newSignal.side);
      
      // Visual flash
      document.body.style.transition = 'background-color 0.2s';
      document.body.style.backgroundColor = newSignal.side === 'long' ? 'rgba(6, 182, 212, 0.1)' : 'rgba(236, 72, 153, 0.1)';
      setTimeout(() => {
        document.body.style.backgroundColor = '';
      }, 200);
    }
    previousSignalsCount.current = signals.length;
  }, [signals]);

  // Update CVD history for chart
  useEffect(() => {
    if (microSnap?.cvd_slope !== undefined) {
      setCvdHistory(prev => {
        const newHistory = [...prev, microSnap.cvd_slope];
        return newHistory.slice(-30); // Keep last 30 data points (60 seconds)
      });
    }
  }, [microSnap]);

  const fetchInitialData = async () => {
    try {
      const [statusRes, signalsRes, mtfRes] = await Promise.all([
        axios.get(`${API}/api/live/status`),
        axios.get(`${API}/api/live/signals`),
        axios.get(`${API}/api/mtf/status`)
      ]);
      
      setMonitorStatus(statusRes.data);
      setSignals(signalsRes.data.signals || []);
      setMtfStatus(mtfRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMonitorStatus = async () => {
    try {
      const response = await axios.get(`${API}/api/live/status`);
      setMonitorStatus(response.data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const fetchMicroSnapshot = async () => {
    try {
      const response = await axios.get(`${API}/api/stream/snapshot`);
      setMicroSnap(response.data);
    } catch (error) {
      console.error('Error fetching micro snapshot:', error);
    }
  };

  const fetchMtfData = async () => {
    try {
      const [statusRes, confluenceRes] = await Promise.all([
        axios.get(`${API}/api/mtf/status`),
        axios.get(`${API}/api/mtf/confluence`)
      ]);
      setMtfStatus(statusRes.data);
      setMtfConfluence(confluenceRes.data);
    } catch (error) {
      console.error('Error fetching MTF data:', error);
    }
  };

  const handleStartMonitor = async () => {
    try {
      const [liveRes, mtfRes, streamRes] = await Promise.all([
        axios.post(`${API}/api/live/start`),
        axios.post(`${API}/api/mtf/start`),
        axios.post(`${API}/api/stream/start`)
      ]);
      
      if (liveRes.data.success && mtfRes.data.success && streamRes.data.success) {
        toast.success('System online', { position: 'top-right', autoClose: 2000 });
        playNotificationSound('success');
        fetchMonitorStatus();
        fetchMtfData();
      }
    } catch (error) {
      console.error('Error starting monitor:', error);
      toast.error('System start failed');
    }
  };

  const handleStopMonitor = async () => {
    try {
      const results = { live: { success: false }, mtf: { success: false }, stream: { success: false } };
      
      try { const res = await axios.post(`${API}/api/live/stop`); results.live = res.data; } catch (e) {}
      try { const res = await axios.post(`${API}/api/mtf/stop`); results.mtf = res.data; } catch (e) {}
      try { const res = await axios.post(`${API}/api/stream/stop`); results.stream = res.data; } catch (e) {}
      
      const stopped = [];
      if (results.live.success) stopped.push('Monitor');
      if (results.mtf.success) stopped.push('MTF');
      if (results.stream.success) stopped.push('Stream');
      
      if (stopped.length > 0) {
        toast.info(`${stopped.join(' • ')} stopped`, { position: 'top-right', autoClose: 2000 });
      }
      
      fetchMonitorStatus();
      fetchMtfData();
    } catch (error) {
      console.error('Error stopping monitor:', error);
    }
  };

  const handleCommand = (commandId) => {
    switch (commandId) {
      case 'start':
        handleStartMonitor();
        break;
      case 'stop':
        handleStopMonitor();
        break;
      case 'toggle-log':
        setTradeLogOpen(prev => !prev);
        break;
      case 'scalp-card':
        window.location.href = '/scalp-cards';
        break;
      case 'clear-signals':
        setSignals([]);
        toast.info('Signal stack cleared');
        break;
      default:
        break;
    }
  };

  const formatPrice = (price) => {
    return price ? `$${price.toFixed(2)}` : '--';
  };

  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined) return '--';
    return typeof num === 'number' ? num.toFixed(decimals) : num;
  };

  const getConfluenceTierColor = (tier) => {
    if (tier === 'A') return 'from-cyan-500/20 to-cyan-600/10 border-cyan-500/40 text-cyan-300';
    if (tier === 'B') return 'from-amber-500/20 to-amber-600/10 border-amber-500/40 text-amber-300';
    return 'from-gray-700/20 to-gray-800/10 border-gray-600/30 text-gray-500';
  };

  const getSideGlow = (side) => {
    return side === 'long' 
      ? 'shadow-lg shadow-cyan-500/20 border-cyan-500/40' 
      : 'shadow-lg shadow-pink-500/20 border-pink-500/40';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-radial from-[#0B0E14] to-[#141921] flex items-center justify-center">
        <div className="text-gray-400 text-lg">Initializing...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-radial from-[#0B0E14] to-[#141921] text-gray-100">
      {/* Command Palette */}
      <CommandPalette 
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onCommand={handleCommand}
      />

      {/* Hotkey Hint */}
      <div className="fixed top-4 right-4 z-30 flex items-center gap-2 px-3 py-2 bg-gray-900/80 backdrop-blur-xl border border-gray-800/50 rounded-lg shadow-lg">
        <kbd className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs font-mono text-gray-400">⌘K</kbd>
        <span className="text-xs text-gray-500 font-medium">Command Palette</span>
      </div>

      {/* Top Status Strip */}
      <div className="sticky top-0 z-50 bg-black/80 backdrop-blur-2xl border-b border-cyan-500/10 shadow-lg shadow-cyan-500/5">
        <div className="px-8 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-6 text-sm font-mono">
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-semibold">SOL/USD</span>
              <motion.span 
                key={monitorStatus.last_price}
                initial={{ scale: 1.1, color: '#00F6FF' }}
                animate={{ scale: 1, color: '#ffffff' }}
                transition={{ duration: 0.3 }}
                className="text-white font-black text-xl"
              >
                {formatPrice(monitorStatus.last_price)}
              </motion.span>
            </div>
            <span className="text-gray-700">|</span>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">CVD</span>
              <motion.span
                key={microSnap?.cvd}
                initial={{ scale: 1.1 }}
                animate={{ scale: 1 }}
                className={`font-bold ${microSnap?.cvd ? (microSnap.cvd > 0 ? 'text-emerald-400' : 'text-rose-400') : 'text-gray-600'}`}
              >
                {microSnap?.cvd ? formatNumber(microSnap.cvd, 0) : '--'}
              </motion.span>
            </div>
            <span className="text-gray-700">|</span>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Spread</span>
              <span className={`font-bold ${microSnap?.spread_bps ? (microSnap.spread_bps < 1 ? 'text-emerald-400' : 'text-amber-400') : 'text-gray-600'}`}>
                {microSnap?.spread_bps ? `${formatNumber(microSnap.spread_bps, 1)}bps` : '--'}
              </span>
            </div>
            <span className="text-gray-700">|</span>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Imb</span>
              <span className="text-gray-300 font-bold">{microSnap?.ladder_imbalance ? formatNumber(microSnap.ladder_imbalance, 3) : '--'}</span>
            </div>
            <span className="text-gray-700">|</span>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Depth</span>
              <span className="text-blue-400 font-bold">{microSnap?.bid_depth ? formatNumber(microSnap.bid_depth / 1000, 0) : '--'}k</span>
              <span className="text-gray-700">/</span>
              <span className="text-rose-400 font-bold">{microSnap?.ask_depth ? formatNumber(microSnap.ask_depth / 1000, 0) : '--'}k</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-900/50 rounded-lg border border-gray-800/50">
              <motion.div 
                animate={{ 
                  scale: monitorStatus.running ? [1, 1.2, 1] : 1,
                  opacity: monitorStatus.running ? [1, 0.5, 1] : 1
                }}
                transition={{ duration: 2, repeat: Infinity }}
                className={`w-2 h-2 rounded-full ${monitorStatus.running ? 'bg-emerald-500' : 'bg-gray-600'}`}
              />
              <span className="text-xs font-mono font-bold text-gray-400">
                {monitorStatus.running ? 'ACTIVE' : 'OFFLINE'}
              </span>
            </div>
            
            {monitorStatus.running ? (
              <button
                onClick={handleStopMonitor}
                className="px-5 py-2 bg-gray-800/70 hover:bg-gray-700/70 border border-gray-700/70 hover:border-rose-500/40 rounded-lg text-xs font-bold transition-all flex items-center gap-2 group"
              >
                <span className="text-gray-300 group-hover:text-rose-400 transition-colors">STOP</span>
                <kbd className="px-1.5 py-0.5 bg-gray-900/50 text-gray-600 group-hover:text-rose-500 rounded text-xs font-mono">X</kbd>
              </button>
            ) : (
              <button
                onClick={handleStartMonitor}
                className="px-5 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 hover:border-emerald-500/60 text-emerald-300 hover:text-emerald-200 rounded-lg text-xs font-bold transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/10"
              >
                <span>START</span>
                <kbd className="px-1.5 py-0.5 bg-emerald-900/30 text-emerald-600 rounded text-xs font-mono">S</kbd>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Split View */}
      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 pb-32">
        
        {/* LEFT: Signal Stack */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* MTF Confluence Engine */}
          {mtfStatus && mtfConfluence && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className={`relative rounded-2xl p-6 border-2 transition-all backdrop-blur-xl ${
                mtfStatus.running 
                  ? 'bg-gradient-to-br ' + getConfluenceTierColor(mtfConfluence.confluence?.final?.tier || 'SKIP')
                  : 'bg-gray-900/40 border-gray-800/60'
              }`}
            >
              {/* Animated pulse ring for active state */}
              {mtfStatus.running && mtfConfluence.confluence?.final?.tier === 'A' && (
                <motion.div
                  className="absolute inset-0 rounded-2xl border-2 border-cyan-500/40"
                  animate={{
                    scale: [1, 1.02, 1],
                    opacity: [0.5, 0.8, 0.5]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
              )}
              
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-5">
                  <div className="flex items-center gap-3">
                    <motion.div 
                      animate={{ rotate: [0, 360] }}
                      transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                      className="text-cyan-400"
                    >
                      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </motion.div>
                    <div>
                      <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wider">MTF Confluence Engine</h3>
                      <p className="text-xs text-gray-500 font-mono mt-0.5">
                        <span className={`inline-block w-2 h-2 rounded-full mr-1.5 ${
                          mtfStatus.running ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'
                        }`}></span>
                        {mtfStatus.state_machine?.state?.toUpperCase() || 'IDLE'}
                      </p>
                    </div>
                  </div>
                  
                  {mtfConfluence.confluence && (
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <motion.div 
                          key={mtfConfluence.confluence.final.final_score}
                          initial={{ scale: 1.3, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          transition={{ type: "spring", stiffness: 300 }}
                          className="text-4xl font-black"
                        >
                          {formatNumber(mtfConfluence.confluence.final.final_score, 0)}
                        </motion.div>
                        <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Score</div>
                      </div>
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ type: "spring", stiffness: 300 }}
                        className={`px-5 py-2.5 rounded-xl border-2 text-xl font-black shadow-lg ${
                          mtfConfluence.confluence.final.tier === 'A' ? 'border-cyan-500/70 text-cyan-300 bg-cyan-500/20 shadow-cyan-500/30' :
                          mtfConfluence.confluence.final.tier === 'B' ? 'border-amber-500/70 text-amber-300 bg-amber-500/20 shadow-amber-500/30' :
                          'border-gray-600/70 text-gray-500 bg-gray-800/20 shadow-gray-500/20'
                        }`}
                      >
                        TIER {mtfConfluence.confluence.final.tier}
                      </motion.div>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    className="bg-black/30 rounded-xl p-4 border border-gray-800/50 backdrop-blur-sm"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Context</div>
                      <span className="text-xs text-gray-600 font-mono">HTF</span>
                    </div>
                    <div className="text-3xl font-black text-blue-400 mb-1">
                      {mtfConfluence.confluence ? formatNumber(mtfConfluence.confluence.context.total, 0) : '--'}
                    </div>
                    <div className="text-xs text-gray-600 font-mono">15m • 1h • 4h • 1D</div>
                  </motion.div>
                  
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    className="bg-black/30 rounded-xl p-4 border border-gray-800/50 backdrop-blur-sm"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Micro</div>
                      <span className="text-xs text-gray-600 font-mono">LTF</span>
                    </div>
                    <div className="text-3xl font-black text-purple-400 mb-1">
                      {mtfConfluence.confluence ? formatNumber(mtfConfluence.confluence.micro.total, 0) : '--'}
                    </div>
                    <div className="text-xs text-gray-600 font-mono">1s → 1m → 5m</div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Signal Stack */}
          <div className="bg-gradient-to-br from-gray-900/50 to-gray-950/50 rounded-2xl border border-gray-800/50 overflow-hidden backdrop-blur-xl">
            <div className="px-6 py-4 border-b border-gray-800/50 flex items-center justify-between bg-black/20">
              <div>
                <h3 className="text-lg font-bold text-gray-200">Signal Stack</h3>
                <p className="text-xs text-gray-500 mt-0.5 font-mono">Chronological detection feed • Real-time</p>
              </div>
              <button
                onClick={() => setTradeLogOpen(prev => !prev)}
                className="px-4 py-2 bg-gray-800/50 hover:bg-gray-700/70 border border-gray-700/50 hover:border-cyan-500/40 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 group"
              >
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-gray-300 group-hover:text-cyan-400 transition-colors">Log</span>
                <kbd className="px-1.5 py-0.5 bg-gray-900/50 text-gray-600 group-hover:text-cyan-500 rounded text-xs font-mono">L</kbd>
              </button>
            </div>
            
            <div className="p-6">
              {signals.length === 0 ? (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-16"
                >
                  <motion.div
                    animate={{ 
                      rotate: [0, 10, -10, 0],
                      scale: [1, 1.1, 1]
                    }}
                    transition={{ 
                      duration: 2,
                      repeat: Infinity,
                      repeatDelay: 1
                    }}
                    className="text-gray-600 mb-4"
                  >
                    <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" />
                    </svg>
                  </motion.div>
                  <div className="text-gray-500 text-sm font-medium">Awaiting signals...</div>
                  <div className="text-gray-600 text-xs mt-2 font-mono">
                    <span className="text-cyan-400">{monitorStatus.candles_count}</span> candles processed • {monitorStatus.running ? (
                      <span className="text-emerald-400">● Active scan</span>
                    ) : (
                      <span className="text-gray-600">○ Monitor offline</span>
                    )}
                  </div>
                </motion.div>
              ) : (
                <div className="space-y-3">
                  <AnimatePresence mode="popLayout">
                    {signals.slice(-5).reverse().map((signal, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -20, scale: 0.95 }}
                        animate={{ opacity: 1, x: 0, scale: 1 }}
                        exit={{ opacity: 0, x: 20, scale: 0.95 }}
                        transition={{ 
                          type: "spring",
                          stiffness: 500,
                          damping: 30,
                          delay: idx * 0.05
                        }}
                        whileHover={{ scale: 1.02, y: -2 }}
                        className={`relative rounded-xl p-5 border-2 ${getSideGlow(signal.side)} bg-gradient-to-br ${
                          signal.side === 'long'
                            ? 'from-cyan-950/30 via-gray-900/30 to-gray-950/30'
                            : 'from-pink-950/30 via-gray-900/30 to-gray-950/30'
                        } transition-all cursor-pointer group backdrop-blur-sm`}
                      >
                        {/* Absolute positioned glow effect */}
                        <div className={`absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity blur-xl ${
                          signal.side === 'long' ? 'bg-cyan-500/10' : 'bg-pink-500/10'
                        }`}></div>
                        
                        <div className="relative z-10">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-4">
                              <motion.div 
                                initial={{ rotate: -45, scale: 0 }}
                                animate={{ rotate: 0, scale: 1 }}
                                transition={{ type: "spring", stiffness: 300 }}
                                className={signal.side === 'long' ? 'text-cyan-400' : 'text-pink-400'}
                              >
                                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={signal.side === 'long' ? "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" : "M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6"} />
                                </svg>
                              </motion.div>
                              <div>
                                <div className={`text-base font-bold uppercase tracking-wide ${
                                  signal.side === 'long' ? 'text-cyan-300' : 'text-pink-300'
                                }`}>
                                  {signal.side} SIGNAL
                                </div>
                                <div className="text-xs text-gray-500 font-mono mt-1">
                                  Entry @ <span className="text-gray-300 font-semibold">{formatPrice(signal.entry)}</span>
                                </div>
                              </div>
                            </div>
                            
                            {/* Tier Badge */}
                            <div className={`px-3 py-1.5 rounded-lg text-xs font-bold border-2 ${
                              signal.tier === 'A'
                                ? 'bg-cyan-500/20 border-cyan-500/60 text-cyan-300 shadow-lg shadow-cyan-500/20'
                                : 'bg-amber-500/20 border-amber-500/60 text-amber-300 shadow-lg shadow-amber-500/20'
                            }`}>
                              TIER {signal.tier || 'B'}
                            </div>
                          </div>
                          
                          {/* Metrics Grid */}
                          <div className="grid grid-cols-3 gap-2 mt-4">
                            <div className="bg-black/30 rounded-lg p-2 border border-gray-800/50">
                              <div className="text-xs text-gray-500 mb-1">R:R</div>
                              <div className="text-sm font-mono font-bold text-gray-200">
                                1:{formatNumber((signal.tp1 - signal.entry) / (signal.entry - signal.sl), 1)}
                              </div>
                            </div>
                            <div className="bg-black/30 rounded-lg p-2 border border-gray-800/50">
                              <div className="text-xs text-gray-500 mb-1">Stop Loss</div>
                              <div className="text-sm font-mono font-bold text-rose-400">
                                {formatPrice(signal.sl)}
                              </div>
                            </div>
                            <div className="bg-black/30 rounded-lg p-2 border border-gray-800/50">
                              <div className="text-xs text-gray-500 mb-1">Target TP1</div>
                              <div className="text-sm font-mono font-bold text-emerald-400">
                                {formatPrice(signal.tp1)}
                              </div>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT: Microstructure Grid */}
        <div className="space-y-4">
          
          {/* CVD Slope Chart */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-gradient-to-br from-gray-900/50 to-gray-950/50 rounded-2xl border border-gray-800/50 p-6 backdrop-blur-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wider">CVD Slope</h4>
              <span className="text-xs text-gray-600 font-mono bg-gray-800/50 px-2 py-1 rounded">30s Rolling</span>
            </div>
            <div className="h-32 bg-black/40 rounded-xl overflow-hidden border border-gray-800/30">
              <CVDSlopeChart data={cvdHistory} />
            </div>
          </motion.div>

          {/* CVD Gauge */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="bg-gradient-to-br from-gray-900/50 to-gray-950/50 rounded-2xl border border-gray-800/50 p-6 backdrop-blur-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wider">CVD</h4>
              <span className={`text-xs font-mono px-2 py-1 rounded border ${
                microSnap?.available 
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                  : 'bg-gray-800/50 border-gray-700 text-gray-600'
              }`}>
                {microSnap?.available ? '● LIVE' : '○ OFFLINE'}
              </span>
            </div>
            <motion.div 
              key={microSnap?.cvd}
              initial={{ scale: 1.1 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 300 }}
              className={`text-5xl font-black mb-3 ${
                microSnap?.cvd 
                  ? microSnap.cvd > 0 ? 'text-emerald-400' : 'text-rose-400'
                  : 'text-gray-600'
              }`}
            >
              {microSnap?.cvd ? formatNumber(microSnap.cvd, 0) : '--'}
            </motion.div>
            <div className="flex items-center gap-3 text-xs bg-black/30 rounded-lg p-2 border border-gray-800/30">
              <span className="text-gray-500 font-semibold">Slope</span>
              <span className={`font-mono font-bold ${
                microSnap?.cvd_slope
                  ? microSnap.cvd_slope > 0 ? 'text-emerald-400' : 'text-rose-400'
                  : 'text-gray-600'
              }`}>
                {microSnap?.cvd_slope ? formatNumber(microSnap.cvd_slope, 4) : '--'}
              </span>
            </div>
          </motion.div>

          {/* Spread Dial */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="bg-gradient-to-br from-gray-900/50 to-gray-950/50 rounded-2xl border border-gray-800/50 p-6 backdrop-blur-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wider">Spread</h4>
              <span className={`text-xs font-mono font-bold px-2 py-1 rounded border ${
                microSnap?.spread_bps 
                  ? microSnap.spread_bps < 1 
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                    : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                  : 'bg-gray-800/50 border-gray-700 text-gray-600'
              }`}>
                {microSnap?.spread_bps ? `${formatNumber(microSnap.spread_bps, 2)} bps` : '-- bps'}
              </span>
            </div>
            <div className="relative h-4 bg-gray-800/50 rounded-full overflow-hidden border border-gray-800/30">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ 
                  width: microSnap?.spread_bps ? `${Math.min((microSnap.spread_bps / 10) * 100, 100)}%` : '0%'
                }}
                transition={{ type: "spring", stiffness: 100, damping: 20 }}
                className={`absolute left-0 top-0 h-full rounded-full ${
                  microSnap?.spread_bps
                    ? microSnap.spread_bps < 1 ? 'bg-emerald-500' : 'bg-amber-500'
                    : 'bg-gray-700'
                }`}
              />
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-gray-600 font-mono">
              <span>0 bps</span>
              <span>10+ bps</span>
            </div>
          </motion.div>

          {/* Depth Imbalance */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="bg-gradient-to-br from-gray-900/50 to-gray-950/50 rounded-2xl border border-gray-800/50 p-6 backdrop-blur-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wider">Depth Imbalance</h4>
              <span className="text-xs text-gray-500 font-mono bg-gray-800/50 px-2 py-1 rounded border border-gray-800/30">
                {microSnap?.ladder_imbalance ? formatNumber(microSnap.ladder_imbalance, 3) : '--'}
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="text-xs text-blue-400 font-bold w-12">BID</div>
                <div className="flex-1 h-4 bg-gray-800/50 rounded-full overflow-hidden border border-gray-800/30">
                  <motion.div 
                    initial={{ width: '50%' }}
                    animate={{ 
                      width: microSnap?.bid_depth 
                        ? `${Math.min((microSnap.bid_depth / (microSnap.bid_depth + microSnap.ask_depth)) * 100, 100)}%` 
                        : '50%'
                    }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                    className="h-full bg-gradient-to-r from-blue-600 to-blue-500 rounded-full"
                  />
                </div>
                <div className="text-xs text-gray-400 font-mono font-bold w-16 text-right">
                  {microSnap?.bid_depth ? formatNumber(microSnap.bid_depth / 1000, 0) + 'k' : '--'}
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="text-xs text-rose-400 font-bold w-12">ASK</div>
                <div className="flex-1 h-4 bg-gray-800/50 rounded-full overflow-hidden border border-gray-800/30">
                  <motion.div 
                    initial={{ width: '50%' }}
                    animate={{ 
                      width: microSnap?.ask_depth 
                        ? `${Math.min((microSnap.ask_depth / (microSnap.bid_depth + microSnap.ask_depth)) * 100, 100)}%` 
                        : '50%'
                    }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                    className="h-full bg-gradient-to-r from-rose-600 to-rose-500 rounded-full"
                  />
                </div>
                <div className="text-xs text-gray-400 font-mono font-bold w-16 text-right">
                  {microSnap?.ask_depth ? formatNumber(microSnap.ask_depth / 1000, 0) + 'k' : '--'}
                </div>
              </div>
            </div>
          </motion.div>

          {/* System Health */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="bg-gradient-to-br from-gray-900/50 to-gray-950/50 rounded-2xl border border-gray-800/50 p-6 backdrop-blur-xl"
          >
            <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-4">System Health</h4>
            <div className="space-y-3 text-xs font-mono">
              <div className="flex justify-between items-center p-2 bg-black/20 rounded-lg border border-gray-800/30">
                <span className="text-gray-500 font-semibold">API</span>
                <span className="text-emerald-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
                  OK
                </span>
              </div>
              <div className="flex justify-between items-center p-2 bg-black/20 rounded-lg border border-gray-800/30">
                <span className="text-gray-500 font-semibold">WebSocket</span>
                <span className={`flex items-center gap-1.5 ${microSnap?.available ? 'text-emerald-400' : 'text-gray-600'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${microSnap?.available ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'}`}></span>
                  {microSnap?.available ? 'OK' : 'OFFLINE'}
                </span>
              </div>
              <div className="flex justify-between items-center p-2 bg-black/20 rounded-lg border border-gray-800/30">
                <span className="text-gray-500 font-semibold">MTF Engine</span>
                <span className={`flex items-center gap-1.5 ${mtfStatus?.running ? 'text-emerald-400' : 'text-gray-600'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${mtfStatus?.running ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'}`}></span>
                  {mtfStatus?.running ? 'OK' : 'OFFLINE'}
                </span>
              </div>
              <div className="flex justify-between items-center p-2 bg-black/20 rounded-lg border border-gray-800/30">
                <span className="text-gray-500 font-semibold">Candles</span>
                <span className="text-cyan-400 font-bold">{monitorStatus.candles_count}</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Trade Log Drawer */}
      <TradeLog 
        signals={signals}
        isOpen={tradeLogOpen}
        onToggle={() => setTradeLogOpen(prev => !prev)}
      />
    </div>
  );
}
