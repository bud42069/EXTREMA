import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Scalp Card Component - Matrix Theme
const ScalpCard = ({ signal }) => {
  const tierColor = signal.tier === 'A' ? 'from-green-500/20 to-emerald-600/20 border-green-500' : 'from-blue-500/20 to-cyan-600/20 border-blue-500';
  const biasColor = signal.bias === 'LONG' ? 'text-green-400' : 'text-red-400';
  const biasGlow = signal.bias === 'LONG' ? 'shadow-green-500/50' : 'shadow-red-500/50';

  return (
    <div className={`bg-gradient-to-br ${tierColor} border-2 rounded-lg p-6 font-mono text-sm hover:scale-[1.02] transition-transform duration-300 shadow-lg ${biasGlow}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-700">
        <div>
          <div className="text-xs text-gray-400">SWING CAPTURE SCALP CARD</div>
          <div className="text-lg font-bold text-white">{signal.symbol} <span className="text-gray-500 text-xs">({signal.exchange})</span></div>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${biasColor} animate-pulse`}>{signal.bias}</div>
          <div className="text-xs text-gray-400">TIER-{signal.tier}</div>
        </div>
      </div>

      {/* Play Info */}
      <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
        <div>
          <span className="text-gray-500">PLAY:</span>
          <div className="text-cyan-300 font-semibold">{signal.play_type}</div>
        </div>
        <div>
          <span className="text-gray-500">REGIME:</span>
          <div className="text-purple-300 font-bold">{signal.regime}</div>
        </div>
        <div>
          <span className="text-gray-500">CONFLUENCE:</span>
          <div className="text-yellow-300 font-bold">{signal.confluence_score.toFixed(0)}%</div>
        </div>
      </div>

      {/* Entry Plan */}
      <div className="mb-4 p-3 bg-black/40 rounded border border-gray-800">
        <div className="text-xs text-cyan-400 mb-2 font-bold">ENTRY PLAN</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-gray-500">Trigger Zone:</span>
            <div className="text-white font-bold">${signal.trigger_zone.toFixed(2)}</div>
          </div>
          <div>
            <span className="text-gray-500">Entry:</span>
            <div className="text-green-300 font-bold">${signal.entry_price.toFixed(2)}</div>
          </div>
          <div className="col-span-2">
            <span className="text-gray-500">Stop Loss:</span>
            <div className="text-red-300 font-bold">${signal.sl_placement.toFixed(2)}</div>
          </div>
        </div>
      </div>

      {/* Target Ladder */}
      <div className="mb-4 p-3 bg-black/40 rounded border border-gray-800">
        <div className="text-xs text-cyan-400 mb-2 font-bold">TARGET LADDER</div>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-500">TP1 ({signal.tp1_allocation}%)</span>
            <span className="text-green-300 font-bold">${signal.tp1_price.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">TP2 ({signal.tp2_allocation}%)</span>
            <span className="text-green-400 font-bold">${signal.tp2_price.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">TP3 ({signal.tp3_allocation}%)</span>
            <span className="text-green-500 font-bold">${signal.tp3_price.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Confluence Checks */}
      <div className="mb-4 p-3 bg-black/40 rounded border border-gray-800">
        <div className="text-xs text-cyan-400 mb-2 font-bold">STRUCTURE & CONFLUENCE</div>
        <div className="grid grid-cols-2 gap-1 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">EMA Align</span>
            <span>{signal.ema_alignment ? '✅' : '❌'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Oscillator</span>
            <span>{signal.oscillator_agreement ? '✅' : '❌'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">S/D Zone</span>
            <span>{signal.supply_demand_valid ? '✅' : '❌'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Volume</span>
            <span>{signal.volume_behavior ? '✅' : '❌'}</span>
          </div>
        </div>
        
        {/* MTF Confirmation (NEW) */}
        {(signal.mtf_1h_aligned || signal.mtf_4h_aligned) && (
          <div className="mt-2 pt-2 border-t border-gray-700">
            <div className="text-xs text-purple-400 mb-1 font-bold">MULTI-TIMEFRAME ⚡</div>
            <div className="grid grid-cols-2 gap-1 text-xs">
              {signal.mtf_1h_aligned && (
                <div className="text-purple-300">✅ 1H Aligned</div>
              )}
              {signal.mtf_4h_aligned && (
                <div className="text-purple-300">✅ 4H Aligned</div>
              )}
            </div>
          </div>
        )}
        
        {/* On-chain Confluence (NEW) */}
        {signal.onchain_aligned && (
          <div className="mt-2 pt-2 border-t border-gray-700">
            <div className="text-xs text-green-400 mb-1 font-bold">ON-CHAIN FLOW 🔗</div>
            <div className="text-xs text-green-300">
              ✅ On-chain aligned ({signal.onchain_signals_count} signals)
            </div>
          </div>
        )}
      </div>

      {/* Indicators */}
      <div className="grid grid-cols-3 gap-2 text-xs mb-3">
        <div>
          <span className="text-gray-500">ATR14:</span>
          <div className="text-purple-300">{signal.atr14.toFixed(3)}</div>
        </div>
        <div>
          <span className="text-gray-500">RSI14:</span>
          <div className="text-yellow-300">{signal.rsi14.toFixed(1)}</div>
        </div>
        <div>
          <span className="text-gray-500">Vol Z:</span>
          <div className="text-cyan-300">{signal.volume_zscore.toFixed(2)}</div>
        </div>
      </div>

      {/* Footer */}
      <div className="pt-3 border-t border-gray-800 flex items-center justify-between text-xs">
        <div className="text-gray-500">ID: {signal.signal_id}</div>
        <div className={`px-2 py-1 rounded ${signal.status === 'ACTIVE' ? 'bg-green-500/20 text-green-300' : 'bg-gray-700 text-gray-400'}`}>
          {signal.status}
        </div>
      </div>
    </div>
  );
};

const LiveSignalsPage = () => {
  const [signals, setSignals] = useState([]);
  const [monitorStatus, setMonitorStatus] = useState({ running: false, candles_count: 0 });
  const [loading, setLoading] = useState(true);
  const wsRef = useRef(null);

  useEffect(() => {
    fetchInitialData();
    connectWebSocket();
    
    // Poll monitor status
    const statusInterval = setInterval(fetchMonitorStatus, 5000);
    
    return () => {
      clearInterval(statusInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const fetchInitialData = async () => {
    try {
      const [statusRes, signalsRes] = await Promise.all([
        axios.get(`${API}/live/status`),
        axios.get(`${API}/live/signals`)
      ]);
      
      setMonitorStatus(statusRes.data);
      setSignals(signalsRes.data.signals || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
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

  const connectWebSocket = () => {
    const wsUrl = `${BACKEND_URL.replace('https', 'wss').replace('http', 'ws')}/ws/signals`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'init') {
        setSignals(message.data.signals || []);
      } else if (message.type === 'new_signal') {
        setSignals(prev => [message.data, ...prev]);
        toast.success(`New ${message.data.bias} signal detected!`, {
          className: 'matrix-toast'
        });
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket closed, reconnecting...');
      setTimeout(connectWebSocket, 5000);
    };

    wsRef.current = ws;
  };

  const handleStartMonitor = async () => {
    try {
      const response = await axios.post(`${API}/live/start`);
      if (response.data.success) {
        toast.success('Live monitor started!');
        fetchMonitorStatus();
      }
    } catch (error) {
      console.error('Error starting monitor:', error);
      toast.error('Failed to start monitor');
    }
  };

  const handleStopMonitor = async () => {
    try {
      const response = await axios.post(`${API}/live/stop`);
      if (response.data.success) {
        toast.info('Monitor stopped');
        fetchMonitorStatus();
      }
    } catch (error) {
      console.error('Error stopping monitor:', error);
      toast.error('Failed to stop monitor');
    }
  };

  return (
    <div className="max-w-[1800px] relative">
      {/* Matrix background effect */}
      <div className="fixed inset-0 bg-black opacity-90 -z-10"></div>
      <div className="fixed inset-0 bg-gradient-to-b from-green-500/5 via-transparent to-cyan-500/5 -z-10"></div>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 via-cyan-400 to-blue-400 mb-2 font-mono">
              LIVE SIGNAL MATRIX
            </h1>
            <p className="text-gray-400 font-mono">Real-time swing detection • SOL/USD • Pyth Network</p>
          </div>
          
          <div className="flex items-center space-x-4">
            {monitorStatus.running ? (
              <button
                onClick={handleStopMonitor}
                className="bg-red-500/20 border-2 border-red-500 text-red-300 px-6 py-3 rounded-lg hover:bg-red-500/30 transition-colors font-mono"
              >
                STOP MONITOR
              </button>
            ) : (
              <button
                onClick={handleStartMonitor}
                className="bg-green-500/20 border-2 border-green-500 text-green-300 px-6 py-3 rounded-lg hover:bg-green-500/30 transition-colors font-mono animate-pulse"
              >
                START MONITOR
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Status Panel */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gradient-to-br from-gray-900 to-black border-2 border-green-500/30 rounded-lg p-4">
          <div className="text-gray-400 text-xs mb-1 font-mono">MONITOR STATUS</div>
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-2 ${monitorStatus.running ? 'bg-green-500 animate-pulse' : 'bg-gray-600'}`}></div>
            <div className="text-lg font-bold text-white font-mono">
              {monitorStatus.running ? 'ACTIVE' : 'OFFLINE'}
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-gray-900 to-black border-2 border-cyan-500/30 rounded-lg p-4">
          <div className="text-gray-400 text-xs mb-1 font-mono">CANDLES LOADED</div>
          <div className="text-2xl font-bold text-cyan-300 font-mono">{monitorStatus.candles_count || 0}</div>
        </div>
        
        <div className="bg-gradient-to-br from-gray-900 to-black border-2 border-purple-500/30 rounded-lg p-4">
          <div className="text-gray-400 text-xs mb-1 font-mono">ACTIVE SIGNALS</div>
          <div className="text-2xl font-bold text-purple-300 font-mono">{signals.length}</div>
        </div>
        
        <div className="bg-gradient-to-br from-gray-900 to-black border-2 border-yellow-500/30 rounded-lg p-4">
          <div className="text-gray-400 text-xs mb-1 font-mono">LAST PRICE</div>
          <div className="text-2xl font-bold text-yellow-300 font-mono">
            ${monitorStatus.last_price ? monitorStatus.last_price.toFixed(2) : '---'}
          </div>
        </div>
      </div>

      {/* Signals Grid */}
      {loading ? (
        <div className="text-center py-20">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-green-500"></div>
          <p className="text-gray-400 mt-4 font-mono">INITIALIZING MATRIX...</p>
        </div>
      ) : signals.length === 0 ? (
        <div className="text-center py-20 bg-gradient-to-br from-gray-900/50 to-black/50 rounded-lg border-2 border-gray-800">
          <div className="text-6xl mb-4">📡</div>
          <p className="text-gray-400 mb-2 font-mono text-xl">AWAITING SIGNAL...</p>
          <p className="text-gray-600 text-sm font-mono">
            {monitorStatus.running ? 'Monitor active. Signals will appear here when detected.' : 'Start the monitor to begin signal generation.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {signals.map((signal, idx) => (
            <ScalpCard key={signal.signal_id || idx} signal={signal} />
          ))}
        </div>
      )}

      {/* Matrix rain effect (optional) */}
      <div className="fixed bottom-0 right-0 text-green-500/10 text-xs font-mono pointer-events-none select-none overflow-hidden h-screen w-full -z-10">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="absolute animate-matrix-rain"
            style={{
              left: `${i * 5}%`,
              animationDelay: `${i * 0.2}s`,
              animationDuration: `${3 + Math.random() * 2}s`
            }}
          >
            {Array.from({ length: 30 }).map((_, j) => (
              <div key={j}>{String.fromCharCode(33 + Math.random() * 94)}</div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default LiveSignalsPage;