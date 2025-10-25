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
      {analysisResult && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="bg-gray-900 rounded-lg p-8">
            <h2 className="text-2xl font-bold text-white mb-6">Analysis Results</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Total Extrema</p>
                <p className="text-3xl font-bold text-white">{analysisResult.summary.total_extrema}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Candidates</p>
                <p className="text-3xl font-bold text-yellow-400">{analysisResult.summary.total_candidates}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Confirmed Signals</p>
                <p className="text-3xl font-bold text-green-400">{analysisResult.summary.total_confirmed_signals}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Confirmation Rate</p>
                <p className="text-3xl font-bold text-blue-400">
                  {analysisResult.summary.total_candidates > 0 
                    ? ((analysisResult.summary.total_confirmed_signals / analysisResult.summary.total_candidates) * 100).toFixed(1)
                    : 0}%
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-green-900/30 to-green-800/30 border border-green-700 rounded-lg p-4">
                <p className="text-green-400 font-semibold mb-2">Long Signals</p>
                <p className="text-2xl font-bold text-white">{analysisResult.summary.long_signals}</p>
              </div>
              
              <div className="bg-gradient-to-br from-red-900/30 to-red-800/30 border border-red-700 rounded-lg p-4">
                <p className="text-red-400 font-semibold mb-2">Short Signals</p>
                <p className="text-2xl font-bold text-white">{analysisResult.summary.short_signals}</p>
              </div>
            </div>
          </div>

          {/* Next Step */}
          <div className="bg-gray-900 rounded-lg p-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white mb-2">Ready for Backtesting</h3>
                <p className="text-gray-400">Test these signals with your trading strategy parameters</p>
              </div>
              <button
                onClick={() => navigate('/backtest', { state: { analysisId: analysisResult.analysis_id } })}
                className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 transition-colors font-semibold"
              >
                Run Backtest →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisPage;