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
    { id: 'start', label: 'Start Monitor', icon: '▶️', hotkey: 'S' },
    { id: 'stop', label: 'Stop Monitor', icon: '⏸️', hotkey: 'X' },
    { id: 'toggle-log', label: 'Toggle Trade Log', icon: '📋', hotkey: 'L' },
    { id: 'scalp-card', label: 'Generate Scalp Card', icon: '🎯', hotkey: 'C' },
    { id: 'clear-signals', label: 'Clear Signal Stack', icon: '🗑️', hotkey: '' },
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
                <span className="text-2xl">{cmd.icon}</span>
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

// CVD Slope Chart Component
const CVDSlopeChart = ({ data }) => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    if (!canvasRef.current || !data || data.length === 0) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw grid
    ctx.strokeStyle = '#1f2937';
    ctx.lineWidth = 1;
    
    // Horizontal lines
    for (let i = 0; i <= 4; i++) {
      const y = (height / 4) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    
    // Draw CVD line
    if (data.length > 1) {
      const max = Math.max(...data.map(d => Math.abs(d)));
      const scale = height / (max * 2);
      
      ctx.beginPath();
      ctx.strokeStyle = '#06b6d4'; // Cyan
      ctx.lineWidth = 2;
      
      data.forEach((value, index) => {
        const x = (width / (data.length - 1)) * index;
        const y = height / 2 - value * scale;
        
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      
      ctx.stroke();
      
      // Gradient fill
      ctx.lineTo(width, height / 2);
      ctx.lineTo(0, height / 2);
      ctx.closePath();
      
      const gradient = ctx.createLinearGradient(0, 0, 0, height);
      gradient.addColorStop(0, 'rgba(6, 182, 212, 0.2)');
      gradient.addColorStop(1, 'rgba(6, 182, 212, 0)');
      ctx.fillStyle = gradient;
      ctx.fill();
    }
  }, [data]);
  
  return (
    <canvas 
      ref={canvasRef} 
      width={400} 
      height={120}
      className="w-full h-full"
    />
  );
};

// Trade Log Component
const TradeLog = ({ signals, isOpen, onToggle }) => {
  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 bg-gray-900/90 backdrop-blur-xl border border-gray-700 rounded-full text-sm font-medium text-gray-300 hover:bg-gray-800 transition-all flex items-center gap-2"
      >
        <span>📋</span>
        <span>Trade Log ({signals.length})</span>
        <span>↑</span>
      </button>
    );
  }
  
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-xl border-t border-gray-800 z-40">
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Trade Log</h3>
        <button
          onClick={onToggle}
          className="text-gray-500 hover:text-gray-300 transition-colors"
        >
          ✕
        </button>
      </div>
      
      <div className="max-h-64 overflow-y-auto p-4">
        {signals.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">No signals yet</div>
        ) : (
          <div className="space-y-2">
            {signals.map((signal, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className={`text-2xl ${signal.side === 'long' ? 'text-cyan-400' : 'text-pink-400'}`}>
                    {signal.side === 'long' ? '✅' : '❌'}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-300">
                      {signal.side.toUpperCase()} @ ${signal.entry?.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500 font-mono">
                      SL: ${signal.sl?.toFixed(2)} • TP1: ${signal.tp1?.toFixed(2)}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-xs text-gray-500">Tier</div>
                    <div className={`text-sm font-bold ${
                      signal.tier === 'A' ? 'text-cyan-400' : 'text-amber-400'
                    }`}>
                      {signal.tier || 'B'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-500">Score</div>
                    <div className="text-sm font-mono text-gray-300">
                      {signal.confluence_score?.toFixed(0) || '--'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
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
        toast.success('🚀 System online', { position: 'top-right', autoClose: 2000 });
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
        toast.info(`⏸️ ${stopped.join(' • ')} stopped`, { position: 'top-right', autoClose: 2000 });
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
      <div className="fixed top-4 right-4 z-30 flex items-center gap-2 text-xs text-gray-500 font-mono">
        <kbd className="px-2 py-1 bg-gray-900 border border-gray-800 rounded">⌘K</kbd>
        <span>Command Palette</span>
      </div>

      {/* Top Status Strip */}
      <div className="sticky top-0 z-50 bg-black/60 backdrop-blur-xl border-b border-gray-800/50">
        <div className="px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6 text-sm font-mono">
            <span className="text-gray-500">SOL/USD</span>
            <span className="text-white font-semibold text-lg">{formatPrice(monitorStatus.last_price)}</span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-500">CVD</span>
            <span className={`${microSnap?.cvd ? (microSnap.cvd > 0 ? 'text-emerald-400' : 'text-rose-400') : 'text-gray-500'}`}>
              {microSnap?.cvd ? formatNumber(microSnap.cvd, 0) : '--'}
            </span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-500">Spread</span>
            <span className="text-gray-300">{microSnap?.spread_bps ? `${formatNumber(microSnap.spread_bps, 1)}bps` : '--'}</span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-500">Imb</span>
            <span className="text-gray-300">{microSnap?.ladder_imbalance ? formatNumber(microSnap.ladder_imbalance, 3) : '--'}</span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-500">Depth</span>
            <span className="text-blue-400">{microSnap?.bid_depth ? formatNumber(microSnap.bid_depth / 1000, 0) : '--'}k</span>
            <span className="text-gray-600">/</span>
            <span className="text-rose-400">{microSnap?.ask_depth ? formatNumber(microSnap.ask_depth / 1000, 0) : '--'}k</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${monitorStatus.running ? 'bg-emerald-500 animate-pulse' : 'bg-gray-600'}`}></div>
              <span className="text-xs font-mono text-gray-400">{monitorStatus.running ? 'ACTIVE' : 'OFFLINE'}</span>
            </div>
            
            {monitorStatus.running ? (
              <button
                onClick={handleStopMonitor}
                className="px-4 py-1.5 bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700/50 rounded-lg text-xs font-medium transition-all"
              >
                STOP <kbd className="ml-1 text-gray-600">X</kbd>
              </button>
            ) : (
              <button
                onClick={handleStartMonitor}
                className="px-4 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 rounded-lg text-xs font-semibold transition-all"
              >
                START <kbd className="ml-1 text-emerald-600">S</kbd>
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
            <div className={`relative rounded-2xl p-6 border transition-all ${
              mtfStatus.running 
                ? 'bg-gradient-to-br ' + getConfluenceTierColor(mtfConfluence.confluence?.final?.tier || 'SKIP')
                : 'bg-gray-900/30 border-gray-800/50'
            }`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">🧠</div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-300">MTF Confluence Engine</h3>
                    <p className="text-xs text-gray-500 font-mono">
                      {mtfStatus.state_machine?.state?.toUpperCase() || 'IDLE'}
                    </p>
                  </div>
                </div>
                
                {mtfConfluence.confluence && (
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-3xl font-bold">
                        {formatNumber(mtfConfluence.confluence.final.final_score, 0)}
                      </div>
                      <div className="text-xs text-gray-500">SCORE</div>
                    </div>
                    <div className={`px-4 py-2 rounded-xl border-2 text-lg font-bold ${
                      mtfConfluence.confluence.final.tier === 'A' ? 'border-cyan-500/60 text-cyan-300 bg-cyan-500/10' :
                      mtfConfluence.confluence.final.tier === 'B' ? 'border-amber-500/60 text-amber-300 bg-amber-500/10' :
                      'border-gray-600/60 text-gray-500 bg-gray-800/10'
                    }`}>
                      TIER {mtfConfluence.confluence.final.tier}
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-black/20 rounded-xl p-4 border border-gray-800/50">
                  <div className="text-xs text-gray-500 mb-2 uppercase tracking-wider">Context</div>
                  <div className="text-2xl font-bold text-blue-400">
                    {mtfConfluence.confluence ? formatNumber(mtfConfluence.confluence.context.total, 0) : '--'}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">15m/1h/4h/1D</div>
                </div>
                <div className="bg-black/20 rounded-xl p-4 border border-gray-800/50">
                  <div className="text-xs text-gray-500 mb-2 uppercase tracking-wider">Micro</div>
                  <div className="text-2xl font-bold text-purple-400">
                    {mtfConfluence.confluence ? formatNumber(mtfConfluence.confluence.micro.total, 0) : '--'}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">1s→1m→5m</div>
                </div>
              </div>
            </div>
          )}

          {/* Signal Stack */}
          <div className="bg-gray-900/30 rounded-2xl border border-gray-800/50 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-800/50 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-300">Signal Stack</h3>
                <p className="text-xs text-gray-500 mt-1">Chronological detection feed</p>
              </div>
              <button
                onClick={() => setTradeLogOpen(prev => !prev)}
                className="px-3 py-1.5 bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700 rounded-lg text-xs font-medium transition-all flex items-center gap-2"
              >
                <span>📋</span>
                <span>Log</span>
                <kbd className="text-gray-600">L</kbd>
              </button>
            </div>
            
            <div className="p-6">
              {signals.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-3">📡</div>
                  <div className="text-gray-500 text-sm">Awaiting signals...</div>
                  <div className="text-gray-600 text-xs mt-1">
                    {monitorStatus.candles_count} candles • {monitorStatus.running ? 'Scanning' : 'Monitor offline'}
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {signals.slice(-5).reverse().map((signal, idx) => (
                    <div
                      key={idx}
                      className={`relative rounded-xl p-4 border-2 ${getSideGlow(signal.side)} bg-gradient-to-br from-gray-900/50 to-gray-800/30 transition-all hover:scale-[1.02]`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`text-2xl ${signal.side === 'long' ? 'text-cyan-400' : 'text-pink-400'}`}>
                            {signal.side === 'long' ? '↗' : '↘'}
                          </div>
                          <div>
                            <div className={`text-sm font-bold uppercase ${signal.side === 'long' ? 'text-cyan-300' : 'text-pink-300'}`}>
                              {signal.side}
                            </div>
                            <div className="text-xs text-gray-500 font-mono">
                              Entry {formatPrice(signal.entry)}
                            </div>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <div className="text-xs text-gray-500">R:R</div>
                          <div className="text-sm font-mono text-gray-300">1:{formatNumber((signal.tp1 - signal.entry) / (signal.entry - signal.sl), 1)}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT: Microstructure Grid */}
        <div className="space-y-4">
          
          {/* CVD Slope Chart */}
          <div className="bg-gray-900/30 rounded-2xl border border-gray-800/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">CVD Slope</h4>
              <span className="text-xs text-gray-600 font-mono">30s Rolling</span>
            </div>
            <div className="h-32 bg-black/30 rounded-lg overflow-hidden">
              <CVDSlopeChart data={cvdHistory} />
            </div>
          </div>

          {/* CVD Gauge */}
          <div className="bg-gray-900/30 rounded-2xl border border-gray-800/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">CVD</h4>
              <span className="text-xs text-gray-600 font-mono">{microSnap?.available ? 'LIVE' : 'OFFLINE'}</span>
            </div>
            <div className={`text-4xl font-bold mb-2 ${
              microSnap?.cvd 
                ? microSnap.cvd > 0 ? 'text-emerald-400' : 'text-rose-400'
                : 'text-gray-600'
            }`}>
              {microSnap?.cvd ? formatNumber(microSnap.cvd, 0) : '--'}
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gray-500">Slope</span>
              <span className={`font-mono ${
                microSnap?.cvd_slope
                  ? microSnap.cvd_slope > 0 ? 'text-emerald-400' : 'text-rose-400'
                  : 'text-gray-600'
              }`}>
                {microSnap?.cvd_slope ? formatNumber(microSnap.cvd_slope, 4) : '--'}
              </span>
            </div>
          </div>

          {/* Spread Dial */}
          <div className="bg-gray-900/30 rounded-2xl border border-gray-800/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Spread</h4>
              <span className={`text-xs font-mono ${
                microSnap?.spread_bps 
                  ? microSnap.spread_bps < 1 ? 'text-emerald-500' : 'text-amber-500'
                  : 'text-gray-600'
              }`}>
                {microSnap?.spread_bps ? `${formatNumber(microSnap.spread_bps, 2)} bps` : '-- bps'}
              </span>
            </div>
            <div className="relative h-3 bg-gray-800/50 rounded-full overflow-hidden">
              <div 
                className={`absolute left-0 top-0 h-full rounded-full transition-all ${
                  microSnap?.spread_bps
                    ? microSnap.spread_bps < 1 ? 'bg-emerald-500' : 'bg-amber-500'
                    : 'bg-gray-700'
                }`}
                style={{ width: microSnap?.spread_bps ? `${Math.min((microSnap.spread_bps / 10) * 100, 100)}%` : '0%' }}
              ></div>
            </div>
          </div>

          {/* Depth Imbalance */}
          <div className="bg-gray-900/30 rounded-2xl border border-gray-800/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Depth Imbalance</h4>
              <span className="text-xs text-gray-600 font-mono">
                {microSnap?.ladder_imbalance ? formatNumber(microSnap.ladder_imbalance, 3) : '--'}
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="text-xs text-blue-400 w-12">BID</div>
                <div className="flex-1 h-3 bg-gray-800/50 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 rounded-full transition-all"
                    style={{ width: microSnap?.bid_depth ? `${Math.min((microSnap.bid_depth / (microSnap.bid_depth + microSnap.ask_depth)) * 100, 100)}%` : '50%' }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 font-mono w-16 text-right">
                  {microSnap?.bid_depth ? formatNumber(microSnap.bid_depth / 1000, 0) + 'k' : '--'}
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <div className="text-xs text-rose-400 w-12">ASK</div>
                <div className="flex-1 h-3 bg-gray-800/50 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-rose-500 rounded-full transition-all"
                    style={{ width: microSnap?.ask_depth ? `${Math.min((microSnap.ask_depth / (microSnap.bid_depth + microSnap.ask_depth)) * 100, 100)}%` : '50%' }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 font-mono w-16 text-right">
                  {microSnap?.ask_depth ? formatNumber(microSnap.ask_depth / 1000, 0) + 'k' : '--'}
                </div>
              </div>
            </div>
          </div>

          {/* System Health */}
          <div className="bg-gray-900/30 rounded-2xl border border-gray-800/50 p-6">
            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">System Health</h4>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-gray-500">API</span>
                <span className="text-emerald-400">✓ OK</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">WebSocket</span>
                <span className={microSnap?.available ? 'text-emerald-400' : 'text-gray-600'}>
                  {microSnap?.available ? '✓ OK' : '○ OFFLINE'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">MTF Engine</span>
                <span className={mtfStatus?.running ? 'text-emerald-400' : 'text-gray-600'}>
                  {mtfStatus?.running ? '✓ OK' : '○ OFFLINE'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Candles</span>
                <span className="text-gray-300">{monitorStatus.candles_count}</span>
              </div>
            </div>
          </div>
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
