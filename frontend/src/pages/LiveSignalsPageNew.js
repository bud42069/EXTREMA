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
      // Start both live monitor and MTF system
      const [liveRes, mtfRes] = await Promise.all([
        axios.post(`${API}/live/start`),
        axios.post(`${API}/mtf/start`)
      ]);
      
      if (liveRes.data.success && mtfRes.data.success) {
        toast.success('🚀 Live monitor + MTF system started!', { position: 'top-right' });
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
      const [liveRes, mtfRes] = await Promise.all([
        axios.post(`${API}/live/stop`),
        axios.post(`${API}/mtf/stop`)
      ]);
      
      if (liveRes.data.success && mtfRes.data.success) {
        toast.info('Monitor stopped', { position: 'top-right' });
        fetchMonitorStatus();
      }
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
