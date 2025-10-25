import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

const API = process.env.REACT_APP_BACKEND_URL || '';

export default function LiveSignalsDashboard() {
  const [monitorStatus, setMonitorStatus] = useState({ running: false, last_price: 0, candles_count: 0 });
  const [signals, setSignals] = useState([]);
  const [microSnap, setMicroSnap] = useState(null);
  const [mtfStatus, setMtfStatus] = useState(null);
  const [mtfConfluence, setMtfConfluence] = useState(null);
  const [loading, setLoading] = useState(true);

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

  const getSideColor = (side) => {
    return side === 'long' ? 'cyan' : 'magenta';
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
                STOP
              </button>
            ) : (
              <button
                onClick={handleStartMonitor}
                className="px-4 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 rounded-lg text-xs font-semibold transition-all"
              >
                START
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Split View */}
      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT: Signal Stack */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* MTF Confluence Engine - Active State Tile */}
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
            <div className="px-6 py-4 border-b border-gray-800/50">
              <h3 className="text-lg font-semibold text-gray-300">Signal Stack</h3>
              <p className="text-xs text-gray-500 mt-1">Chronological detection feed</p>
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
                  {signals.map((signal, idx) => (
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

          {/* Depth Imbalance Gauge */}
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
    </div>
  );
}
