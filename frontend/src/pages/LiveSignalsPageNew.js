import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LiveSignalsPage() {
  const [monitorStatus, setMonitorStatus] = useState({ running: false, last_price: 0, candles_count: 0 });
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [microSnap, setMicroSnap] = useState(null);
  const [mtfStatus, setMtfStatus] = useState(null);
  const [mtfConfluence, setMtfConfluence] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    fetchInitialData();
    
    const statusInterval = setInterval(fetchMonitorStatus, 3000);
    const snapInterval = setInterval(fetchMicroSnapshot, 2000);
    const mtfInterval = setInterval(fetchMtfData, 5000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(snapInterval);
      clearInterval(mtfInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const fetchInitialData = async () => {
    try {
      const [statusRes, signalsRes, mtfRes] = await Promise.all([
        axios.get(`${API}/live/status`),
        axios.get(`${API}/live/signals`),
        axios.get(`${API}/mtf/status`)
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
      const response = await axios.get(`${API}/live/status`);
      setMonitorStatus(response.data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const fetchMicroSnapshot = async () => {
    try {
      const response = await axios.get(`${API}/stream/snapshot`);
      setMicroSnap(response.data);
    } catch (error) {
      console.error('Error fetching micro snapshot:', error);
    }
  };

  const fetchMtfData = async () => {
    try {
      const [statusRes, confluenceRes] = await Promise.all([
        axios.get(`${API}/mtf/status`),
        axios.get(`${API}/mtf/confluence`)
      ]);
      setMtfStatus(statusRes.data);
      setMtfConfluence(confluenceRes.data);
    } catch (error) {
      console.error('Error fetching MTF data:', error);
    }
  };

  const handleStartMonitor = async () => {
    try {
      // Start live monitor, MTF system, AND microstructure stream
      const [liveRes, mtfRes, streamRes] = await Promise.all([
        axios.post(`${API}/live/start`),
        axios.post(`${API}/mtf/start`),
        axios.post(`${API}/stream/start`)
      ]);
      
      if (liveRes.data.success && mtfRes.data.success && streamRes.data.success) {
        toast.success('🚀 Live monitor + MTF + Microstructure started!', { position: 'top-right' });
        fetchMonitorStatus();
        fetchMtfData();
      }
    } catch (error) {
      console.error('Error starting monitor:', error);
      toast.error('Failed to start monitor');
    }
  };

  const handleStopMonitor = async () => {
    try {
      // Stop each system independently (don't use Promise.all to avoid stopping on first error)
      const results = {
        live: { success: false },
        mtf: { success: false },
        stream: { success: false }
      };
      
      try {
        const liveRes = await axios.post(`${API}/live/stop`);
        results.live = liveRes.data;
      } catch (e) {
        console.error('Error stopping live monitor:', e);
      }
      
      try {
        const mtfRes = await axios.post(`${API}/mtf/stop`);
        results.mtf = mtfRes.data;
      } catch (e) {
        console.error('Error stopping MTF:', e);
      }
      
      try {
        const streamRes = await axios.post(`${API}/stream/stop`);
        results.stream = streamRes.data;
      } catch (e) {
        console.error('Error stopping stream:', e);
      }
      
      // Check what was stopped
      const stopped = [];
      if (results.live.success) stopped.push('Live Monitor');
      if (results.mtf.success) stopped.push('MTF System');
      if (results.stream.success) stopped.push('Microstructure Stream');
      
      if (stopped.length > 0) {
        toast.info(`⏸️ Stopped: ${stopped.join(', ')}`, { position: 'top-right' });
      } else {
        toast.warning('Nothing was running to stop', { position: 'top-right' });
      }
      
      // Always refresh status
      fetchMonitorStatus();
      fetchMtfData();
      
    } catch (error) {
      console.error('Error stopping monitor:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/20 p-6">
      <div className="max-w-[1920px] mx-auto">
        {/* Header - Compact */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              LIVE SIGNALS
            </h1>
            <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg backdrop-blur-xl text-sm ${
              monitorStatus.running 
                ? 'bg-emerald-500/10 border border-emerald-500/30' 
                : 'bg-slate-800/50 border border-slate-700'
            }`}>
              <div className={`w-1.5 h-1.5 rounded-full ${
                monitorStatus.running ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
              }`}></div>
              <span className={monitorStatus.running ? 'text-emerald-400 font-medium' : 'text-slate-400'}>
                {monitorStatus.running ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>
          </div>

          <button
            onClick={monitorStatus.running ? handleStopMonitor : handleStartMonitor}
            className={`px-6 py-2.5 rounded-lg font-medium transition-all ${
              monitorStatus.running
                ? 'bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400'
                : 'bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-white shadow-lg shadow-emerald-500/25'
            }`}
          >
            {monitorStatus.running ? 'STOP MONITOR' : 'START MONITOR'}
          </button>
        </div>

        {/* Data Grid - Dense Layout */}
        <div className="grid grid-cols-12 gap-4 mb-4">
          {/* Price Ticker */}
          <div className="col-span-3 relative overflow-hidden rounded-xl">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl"></div>
            <div className="absolute inset-0 border border-slate-700/50 rounded-xl"></div>
            <div className="relative p-4">
              <div className="text-xs text-slate-500 mb-1 font-mono">SOL/USD</div>
              <div className="text-3xl font-bold text-white mb-1">
                {monitorStatus.last_price > 0 ? `$${monitorStatus.last_price.toFixed(2)}` : '--'}
              </div>
              <div className="text-xs text-emerald-400 font-mono">Pyth Network</div>
            </div>
          </div>

          {/* Candles */}
          <div className="col-span-2 relative overflow-hidden rounded-xl">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl"></div>
            <div className="absolute inset-0 border border-slate-700/50 rounded-xl"></div>
            <div className="relative p-4">
              <div className="text-xs text-slate-500 mb-1 font-mono">CANDLES</div>
              <div className="text-2xl font-bold text-white">{monitorStatus.candles_count || 0}</div>
            </div>
          </div>

          {/* Active Signals */}
          <div className="col-span-2 relative overflow-hidden rounded-xl">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl"></div>
            <div className="absolute inset-0 border border-slate-700/50 rounded-xl"></div>
            <div className="relative p-4">
              <div className="text-xs text-slate-500 mb-1 font-mono">SIGNALS</div>
              <div className="text-2xl font-bold text-emerald-400">{signals.length}</div>
            </div>
          </div>

          {/* Spread */}
          <div className="col-span-2 relative overflow-hidden rounded-xl">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl"></div>
            <div className="absolute inset-0 border border-slate-700/50 rounded-xl"></div>
            <div className="relative p-4">
              <div className="text-xs text-slate-500 mb-1 font-mono">SPREAD (bps)</div>
              <div className="text-2xl font-bold text-cyan-400">
                {microSnap?.spread_bps ? microSnap.spread_bps.toFixed(1) : '--'}
              </div>
            </div>
          </div>

          {/* Imbalance */}
          <div className="col-span-3 relative overflow-hidden rounded-xl">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl"></div>
            <div className="absolute inset-0 border border-slate-700/50 rounded-xl"></div>
            <div className="relative p-4">
              <div className="text-xs text-slate-500 mb-1 font-mono">LADDER IMBALANCE</div>
              <div className={`text-2xl font-bold ${
                microSnap?.ladder_imbalance > 0 ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {microSnap?.ladder_imbalance ? microSnap.ladder_imbalance.toFixed(3) : '--'}
              </div>
            </div>
          </div>
        </div>

        {/* Microstructure Panel - Compact */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: 'CVD', value: microSnap?.cvd?.toFixed(0) || '--', color: 'text-blue-400' },
            { label: 'CVD Slope', value: microSnap?.cvd_slope?.toFixed(4) || '--', color: 'text-purple-400' },
            { label: 'Bid Depth', value: microSnap?.bid_depth?.toFixed(1) || '--', color: 'text-emerald-400' },
            { label: 'Ask Depth', value: microSnap?.ask_depth?.toFixed(1) || '--', color: 'text-red-400' }
          ].map((metric, i) => (
            <div key={i} className="relative overflow-hidden rounded-lg">
              <div className="absolute inset-0 bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl"></div>
              <div className="absolute inset-0 border border-slate-700/50 rounded-lg"></div>
              <div className="relative p-3">
                <div className="text-xs text-slate-500 font-mono mb-0.5">{metric.label}</div>
                <div className={`text-lg font-bold ${metric.color}`}>{metric.value}</div>
              </div>
            </div>
          ))}
        </div>

        {/* MTF Status Panel - NEW */}
        {mtfStatus && (
          <div className="mb-6">
            <div className="relative overflow-hidden rounded-xl">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/20 to-purple-900/20 backdrop-blur-xl"></div>
              <div className="absolute inset-0 border border-indigo-500/30 rounded-xl"></div>
              <div className="relative p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="text-sm font-semibold text-indigo-300 uppercase tracking-wider">
                      📊 MTF Confluence Engine
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-mono ${
                      mtfStatus.running ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-700/50 text-slate-400'
                    }`}>
                      {mtfStatus.running ? 'ACTIVE' : 'OFFLINE'}
                    </div>
                    {mtfStatus.state_machine && (
                      <div className="px-2 py-1 rounded text-xs font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        STATE: {mtfStatus.state_machine.state.toUpperCase()}
                      </div>
                    )}
                  </div>
                  
                  {mtfConfluence && mtfConfluence.confluence && (
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-xs text-slate-500 font-mono">FINAL SCORE</div>
                        <div className={`text-2xl font-bold ${
                          mtfConfluence.confluence.final.tier === 'A' ? 'text-emerald-400' :
                          mtfConfluence.confluence.final.tier === 'B' ? 'text-yellow-400' :
                          'text-slate-500'
                        }`}>
                          {mtfConfluence.confluence.final.final_score.toFixed(0)}
                        </div>
                      </div>
                      <div className={`px-3 py-2 rounded-lg text-xl font-bold ${
                        mtfConfluence.confluence.final.tier === 'A' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                        mtfConfluence.confluence.final.tier === 'B' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' :
                        'bg-slate-700/50 text-slate-400 border border-slate-600/30'
                      }`}>
                        TIER {mtfConfluence.confluence.final.tier}
                      </div>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-4">
                  {/* Context Confluence */}
                  <div className="relative overflow-hidden rounded-lg">
                    <div className="absolute inset-0 bg-slate-800/60 backdrop-blur-xl"></div>
                    <div className="absolute inset-0 border border-slate-700/50 rounded-lg"></div>
                    <div className="relative p-3">
                      <div className="text-xs text-slate-500 font-mono mb-2 uppercase">Context (15m/1h/4h/1D)</div>
                      {mtfConfluence?.confluence?.context ? (
                        <>
                          <div className="text-2xl font-bold text-blue-400 mb-2">
                            {mtfConfluence.confluence.context.total.toFixed(0)}
                          </div>
                          <div className="space-y-1 text-xs font-mono">
                            <div className="flex justify-between">
                              <span className="text-slate-500">EMA Align:</span>
                              <span className="text-slate-300">{mtfConfluence.confluence.context.scores.ema_alignment.toFixed(0)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Oscillator:</span>
                              <span className="text-slate-300">{mtfConfluence.confluence.context.scores.oscillator_agreement.toFixed(0)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Macro Gate:</span>
                              <span className="text-slate-300">{mtfConfluence.confluence.context.scores.macro_gate.toFixed(0)}</span>
                            </div>
                          </div>
                        </>
                      ) : <div className="text-slate-500">--</div>}
                    </div>
                  </div>

                  {/* Micro Confluence */}
                  <div className="relative overflow-hidden rounded-lg">
                    <div className="absolute inset-0 bg-slate-800/60 backdrop-blur-xl"></div>
                    <div className="absolute inset-0 border border-slate-700/50 rounded-lg"></div>
                    <div className="relative p-3">
                      <div className="text-xs text-slate-500 font-mono mb-2 uppercase">Micro (1s→1m→5m)</div>
                      {mtfConfluence?.confluence?.micro ? (
                        <>
                          <div className="text-2xl font-bold text-purple-400 mb-2">
                            {mtfConfluence.confluence.micro.total.toFixed(0)}
                          </div>
                          <div className="space-y-1 text-xs font-mono">
                            <div className="flex justify-between">
                              <span className="text-slate-500">5m Trigger:</span>
                              <span className="text-slate-300">{mtfConfluence.confluence.micro.scores.trigger_5m.toFixed(0)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">1m Impulse:</span>
                              <span className="text-slate-300">{mtfConfluence.confluence.micro.scores.impulse_1m.toFixed(0)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Tape (1s/5s):</span>
                              <span className="text-slate-300">{mtfConfluence.confluence.micro.scores.tape_micro.toFixed(0)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Veto Check:</span>
                              <span className="text-emerald-300">{mtfConfluence.confluence.micro.scores.veto_hygiene.toFixed(0)}</span>
                            </div>
                          </div>
                        </>
                      ) : <div className="text-slate-500">--</div>}
                    </div>
                  </div>

                  {/* Data Stores */}
                  <div className="relative overflow-hidden rounded-lg">
                    <div className="absolute inset-0 bg-slate-800/60 backdrop-blur-xl"></div>
                    <div className="absolute inset-0 border border-slate-700/50 rounded-lg"></div>
                    <div className="relative p-3">
                      <div className="text-xs text-slate-500 font-mono mb-2 uppercase">Timeframe Stores</div>
                      {mtfStatus.stores ? (
                        <div className="space-y-1 text-xs font-mono">
                          {Object.entries(mtfStatus.stores).filter(([tf, count]) => count > 0).map(([tf, count]) => (
                            <div key={tf} className="flex justify-between">
                              <span className="text-slate-500">{tf}:</span>
                              <span className="text-emerald-400">{count}</span>
                            </div>
                          ))}
                        </div>
                      ) : <div className="text-slate-500">--</div>}
                    </div>
                  </div>
                </div>

                {/* State Machine Stats */}
                {mtfStatus.state_machine && (
                  <div className="mt-3 pt-3 border-t border-slate-700/50">
                    <div className="grid grid-cols-6 gap-2 text-xs font-mono">
                      <div className="text-center">
                        <div className="text-slate-500">Candidates</div>
                        <div className="text-white font-bold">{mtfStatus.state_machine.stats.candidates_detected}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-slate-500">Expired</div>
                        <div className="text-orange-400 font-bold">{mtfStatus.state_machine.stats.candidates_expired}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-slate-500">Confirms</div>
                        <div className="text-emerald-400 font-bold">{mtfStatus.state_machine.stats.micro_confirms}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-slate-500">Rejects</div>
                        <div className="text-red-400 font-bold">{mtfStatus.state_machine.stats.micro_rejects}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-slate-500">Executions</div>
                        <div className="text-cyan-400 font-bold">{mtfStatus.state_machine.stats.executions}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-slate-500">Vetoes</div>
                        <div className="text-yellow-400 font-bold">{mtfStatus.state_machine.stats.vetoes}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Signals Table - Data Dense */}
        <div className="relative overflow-hidden rounded-xl">
          <div className="absolute inset-0 bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl"></div>
          <div className="absolute inset-0 border border-slate-700/50 rounded-xl"></div>
          <div className="relative">
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-4 p-4 border-b border-slate-700/50 text-xs text-slate-400 font-mono font-semibold uppercase">
              <div className="col-span-1">Time</div>
              <div className="col-span-1">Side</div>
              <div className="col-span-1">Entry</div>
              <div className="col-span-1">SL</div>
              <div className="col-span-1">TP1</div>
              <div className="col-span-1">TP2</div>
              <div className="col-span-1">TP3</div>
              <div className="col-span-1">R:R</div>
              <div className="col-span-1">Conf%</div>
              <div className="col-span-2">Status</div>
              <div className="col-span-1">Action</div>
            </div>

            {/* Table Body */}
            <div className="max-h-[600px] overflow-y-auto">
              {loading ? (
                <div className="p-8 text-center text-slate-500 font-mono text-sm">
                  Loading signals...
                </div>
              ) : signals.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="text-6xl mb-4">📡</div>
                  <div className="text-slate-400 font-mono text-sm">
                    {monitorStatus.running ? 'Awaiting signals...' : 'Start monitor to detect signals'}
                  </div>
                </div>
              ) : (
                signals.map((signal, i) => (
                  <div key={i} className="grid grid-cols-12 gap-4 p-4 border-b border-slate-800/30 hover:bg-emerald-500/5 transition-colors text-sm font-mono">
                    <div className="col-span-1 text-slate-400">
                      {new Date(signal.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="col-span-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                        signal.side === 'LONG' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {signal.side}
                      </span>
                    </div>
                    <div className="col-span-1 text-white font-semibold">${signal.entry.toFixed(2)}</div>
                    <div className="col-span-1 text-red-400">${signal.sl.toFixed(2)}</div>
                    <div className="col-span-1 text-emerald-400">${signal.tp1.toFixed(2)}</div>
                    <div className="col-span-1 text-emerald-400">${signal.tp2.toFixed(2)}</div>
                    <div className="col-span-1 text-emerald-400">${signal.tp3.toFixed(2)}</div>
                    <div className="col-span-1 text-cyan-400">1:{signal.rr.toFixed(1)}R</div>
                    <div className="col-span-1 text-yellow-400">{signal.conf}%</div>
                    <div className="col-span-2">
                      <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        Active
                      </span>
                    </div>
                    <div className="col-span-1">
                      <button className="text-emerald-400 hover:text-emerald-300 text-xs">
                        View Card →
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
