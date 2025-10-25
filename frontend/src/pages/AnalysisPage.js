import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AnalysisPage = () => {
  const navigate = useNavigate();
  
  const [dataLoaded, setDataLoaded] = useState(false);
  const [dataInfo, setDataInfo] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  
  const [config, setConfig] = useState({
    atr_threshold: 0.6,
    vol_z_threshold: 0.5,
    bb_width_threshold: 0.005,
    confirmation_window: 6,
    atr_multiplier: 0.5,
    volume_multiplier: 1.5
  });

  useEffect(() => {
    checkDataAvailability();
  }, []);

  const checkDataAvailability = async () => {
    try {
      const response = await axios.get(`${API}/swings/`);
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
      toast.error('Please upload data first');
      navigate('/upload');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await axios.get(`${API}/signals/latest`, {
        params: {
          atr_min: config.atr_threshold,
          volz_min: config.vol_z_threshold,
          bbw_min: config.bb_width_threshold,
          confirm_window: config.confirmation_window,
          breakout_atr_mult: config.atr_multiplier,
          vol_mult: config.volume_multiplier,
          enable_micro_gate: false
        }
      });
      
      toast.success('✅ Analysis completed!');
      setAnalysisResult(response.data);
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error(error.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/20 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-emerald-400 bg-clip-text text-transparent mb-2">
            Signal Analysis
          </h1>
          <p className="text-slate-400 text-lg">Run two-stage detection to identify swing trading signals</p>
        </div>

        {/* Data Status Card */}
        <div className="relative overflow-hidden rounded-2xl mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl"></div>
          <div className="absolute inset-0 border border-slate-700/50 rounded-2xl"></div>
          <div className="relative p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400 mb-1">Current Dataset</div>
                {dataLoaded ? (
                  <div>
                    <div className="text-2xl font-bold text-white mb-1">
                      {dataInfo?.rows?.toLocaleString() || 0} Candles Loaded
                    </div>
                    <div className="text-sm text-emerald-400">
                      {dataInfo?.swings_24h || 0} swings detected • Ready for analysis
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="text-2xl font-bold text-slate-500 mb-1">No Data Loaded</div>
                    <div className="text-sm text-slate-500">Upload CSV data first</div>
                  </div>
                )}
              </div>
              {!dataLoaded && (
                <button
                  onClick={() => navigate('/upload')}
                  className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 rounded-lg text-white font-medium transition-all"
                >
                  Upload Data
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Configuration Panel */}
        <div className="relative overflow-hidden rounded-2xl mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl"></div>
          <div className="absolute inset-0 border border-slate-700/50 rounded-2xl"></div>
          <div className="relative p-8">
            <h2 className="text-2xl font-bold text-white mb-6">Analysis Configuration</h2>

        {/* Stage 1: Candidate Detection */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-emerald-400 mb-4">Stage 1: Candidate Detection</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-slate-300 text-sm mb-2">ATR14 Threshold</label>
              <input
                type="number"
                step="0.1"
                value={config.atr_threshold}
                onChange={(e) => setConfig({...config, atr_threshold: parseFloat(e.target.value)})}
                className="w-full bg-slate-800 text-white border border-slate-700 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
              />
            </div>
            
            <div>
              <label className="block text-slate-300 text-sm mb-2">Volume Z-Score Threshold</label>
              <input
                type="number"
                step="0.1"
                value={config.vol_z_threshold}
                onChange={(e) => setConfig({...config, vol_z_threshold: parseFloat(e.target.value)})}
                className="w-full bg-slate-800 text-white border border-slate-700 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
              />
            </div>
            
            <div>
              <label className="block text-slate-300 text-sm mb-2">BB Width Threshold</label>
              <input
                type="number"
                step="0.001"
                value={config.bb_width_threshold}
                onChange={(e) => setConfig({...config, bb_width_threshold: parseFloat(e.target.value)})}
                className="w-full bg-slate-800 text-white border border-slate-700 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Stage 2: Micro Confirmation */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-emerald-400 mb-4">Stage 2: Micro Confirmation</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-gray-300 text-sm mb-2">Confirmation Window (bars)</label>
              <input
                type="number"
                value={config.confirmation_window}
                onChange={(e) => setConfig({...config, confirmation_window: parseInt(e.target.value)})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 text-sm mb-2">ATR Multiplier</label>
              <input
                type="number"
                step="0.1"
                value={config.atr_multiplier}
                onChange={(e) => setConfig({...config, atr_multiplier: parseFloat(e.target.value)})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 text-sm mb-2">Volume Multiplier</label>
              <input
                type="number"
                step="0.1"
                value={config.volume_multiplier}
                onChange={(e) => setConfig({...config, volume_multiplier: parseFloat(e.target.value)})}
                className="w-full bg-slate-800 text-white border border-slate-700 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Run Analysis Button */}
        <button
          onClick={handleAnalyze}
          disabled={analyzing || !dataLoaded}
          className={`w-full py-4 rounded-xl font-bold text-lg transition-all ${
            analyzing || !dataLoaded
              ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-white shadow-lg shadow-emerald-500/25'
          }`}
        >
          {analyzing ? '⏳ Analyzing...' : '🚀 Run Analysis'}
        </button>
      </div>
    </div>

      {/* Analysis Results */}
      {analysisResult && !analysisResult.message && (
        <div className="max-w-7xl mx-auto">
          <div className="relative overflow-hidden rounded-2xl">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl"></div>
            <div className="absolute inset-0 border border-slate-700/50 rounded-2xl"></div>
            <div className="relative p-8">
              <h2 className="text-2xl font-bold text-white mb-6">Latest Confirmed Signal</h2>
              
              {/* Signal Card */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Trade Details */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-3 mb-4">
                    <span className={`px-4 py-2 rounded-lg text-lg font-bold ${
                      analysisResult.side === 'long' 
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}>
                      {analysisResult.side?.toUpperCase() || 'N/A'}
                    </span>
                    <div className="text-sm text-slate-400">
                      Extremum: {analysisResult.extremum_index} • Confirm: {analysisResult.confirm_index}
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                      <span className="text-slate-400">Entry</span>
                      <span className="text-white font-bold text-lg">${analysisResult.entry?.toFixed(2)}</span>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-red-900/20 rounded-lg border border-red-500/20">
                      <span className="text-slate-400">Stop Loss</span>
                      <span className="text-red-400 font-bold">${analysisResult.sl?.toFixed(2)}</span>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-emerald-900/20 rounded-lg border border-emerald-500/20">
                      <span className="text-slate-400">TP1 (1R)</span>
                      <span className="text-emerald-400 font-bold">${analysisResult.tp1?.toFixed(2)}</span>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-emerald-900/20 rounded-lg border border-emerald-500/20">
                      <span className="text-slate-400">TP2 (2R)</span>
                      <span className="text-emerald-400 font-bold">${analysisResult.tp2?.toFixed(2)}</span>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-emerald-900/20 rounded-lg border border-emerald-500/20">
                      <span className="text-slate-400">TP3 (3R)</span>
                      <span className="text-emerald-400 font-bold">${analysisResult.tp3?.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
                
                {/* Risk Management */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-emerald-400">Risk Management</h3>
                  
                  <div className="p-4 bg-slate-800/50 rounded-lg space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Trail Rule</span>
                      <span className="text-white">{analysisResult.trail_atr_mult}× ATR</span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-slate-400">Position Sizing</span>
                      <span className="text-white">1% risk per trade</span>
                    </div>
                  </div>
                  
                  {analysisResult.veto && Object.keys(analysisResult.veto).length > 0 && (
                    <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
                      <div className="text-sm text-red-400 font-semibold mb-2">Veto Reasons</div>
                      {Object.entries(analysisResult.veto).map(([key, value]) => (
                        <div key={key} className="text-xs text-red-300">
                          • {key}: {JSON.stringify(value)}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  <button
                    onClick={() => navigate('/scalp-cards')}
                    className="w-full py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 rounded-lg text-white font-semibold transition-all"
                  >
                    Generate Scalp Card →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {analysisResult && analysisResult.message && (
        <div className="max-w-7xl mx-auto">
          <div className="relative overflow-hidden rounded-2xl">
            <div className="absolute inset-0 bg-gradient-to-br from-yellow-900/20 to-slate-900/40 backdrop-blur-xl"></div>
            <div className="absolute inset-0 border border-yellow-500/30 rounded-2xl"></div>
            <div className="relative p-12 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-2xl font-bold text-white mb-2">No Confirmed Signals</h3>
              <p className="text-slate-400 mb-6">{analysisResult.message}</p>
              <button
                onClick={() => navigate('/upload')}
                className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 rounded-lg text-white font-medium transition-all"
              >
                Try Different Data
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default AnalysisPage;