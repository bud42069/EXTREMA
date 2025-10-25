/**
 * Data Analysis Page - Combined Upload, Analysis & Backtest
 * Professional trading dashboard with 3-tab interface
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import theme from '../design-system.js';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function DataAnalysisPage() {
  const [activeTab, setActiveTab] = useState('upload'); // upload, analysis, backtest
  const [uploadedFile, setUploadedFile] = useState(null);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Analysis state
  const [analysisParams, setAnalysisParams] = useState({
    atr_min: 0.6,
    volz_min: 0.5
  });
  const [analysisResult, setAnalysisResult] = useState(null);
  
  // Backtest state
  const [backtestParams, setBacktestParams] = useState({
    atr_min: 0.6,
    volz_min: 0.5,
    initial_capital: 10000
  });
  const [backtestResult, setBacktestResult] = useState(null);

  // Check if data is loaded on mount
  useEffect(() => {
    checkDataStatus();
  }, []);

  const checkDataStatus = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/data/status`);
      if (res.ok) {
        const data = await res.json();
        setDataLoaded(data.loaded);
      }
    } catch (err) {
      console.error('Error checking data status:', err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadedFile(file);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${BACKEND_URL}/api/data/upload`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setDataLoaded(true);
        alert(`Data uploaded successfully: ${data.count} rows`);
        setActiveTab('analysis'); // Auto-switch to analysis tab
      } else {
        alert('Upload failed');
      }
    } catch (err) {
      alert('Upload error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    if (!dataLoaded) {
      alert('Please upload data first');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/signals/latest?` + new URLSearchParams(analysisParams));
      if (res.ok) {
        const data = await res.json();
        setAnalysisResult(data);
      } else {
        alert('Analysis failed');
      }
    } catch (err) {
      alert('Analysis error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const runBacktest = async () => {
    if (!dataLoaded) {
      alert('Please upload data first');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/backtest/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(backtestParams)
      });
      
      if (res.ok) {
        const data = await res.json();
        setBacktestResult(data);
      } else {
        alert('Backtest failed');
      }
    } catch (err) {
      alert('Backtest error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'upload', label: 'UPLOAD DATA', icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    )},
    { id: 'analysis', label: 'ANALYSIS', icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    )},
    { id: 'backtest', label: 'BACKTEST', icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    )}
  ];

  return (
    <div className="min-h-screen p-8" style={{ background: theme.utils.gradientBg() }}>
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black text-gray-200 mb-2">Data Analysis Suite</h1>
            <p className="text-gray-500">Upload historical data, run signal analysis, and backtest strategies</p>
          </div>
          
          {/* Data Status Indicator */}
          <div className="flex items-center gap-3 px-6 py-3 rounded-xl border backdrop-blur-xl"
            style={{
              background: dataLoaded ? `${theme.colors.accent.emerald}10` : `${theme.colors.bg.elevated}80`,
              borderColor: dataLoaded ? theme.colors.accent.emerald : theme.colors.border.default
            }}
          >
            <div className={`w-2 h-2 rounded-full ${dataLoaded ? 'bg-emerald-500' : 'bg-gray-500'}`} />
            <span className="text-sm font-semibold" style={{ 
              color: dataLoaded ? theme.colors.accent.emerald : theme.colors.text.secondary 
            }}>
              {dataLoaded ? 'DATA LOADED' : 'NO DATA'}
            </span>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex gap-2 p-2 rounded-xl border backdrop-blur-xl"
          style={{
            background: `${theme.colors.bg.elevated}60`,
            borderColor: theme.colors.border.default
          }}
        >
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm transition-all"
              style={{
                background: activeTab === tab.id ? theme.colors.accent.cyan : 'transparent',
                color: activeTab === tab.id ? theme.colors.text.inverse : theme.colors.text.secondary
              }}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto">
        <AnimatePresence mode="wait">
          {activeTab === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="p-8 rounded-2xl border backdrop-blur-xl"
              style={{
                background: `${theme.colors.bg.elevated}80`,
                borderColor: theme.colors.border.default
              }}
            >
              <h2 className="text-2xl font-bold text-gray-200 mb-6">Upload Historical Data</h2>
              
              <div className="border-2 border-dashed rounded-xl p-12 text-center"
                style={{ borderColor: theme.colors.border.default }}
              >
                <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                
                <h3 className="text-xl font-semibold text-gray-300 mb-2">Drop CSV file here</h3>
                <p className="text-gray-500 mb-6">or click to browse</p>
                
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                  disabled={loading}
                />
                <label
                  htmlFor="file-upload"
                  className="inline-block px-8 py-3 rounded-xl font-semibold cursor-pointer transition-all"
                  style={{
                    background: theme.colors.accent.cyan,
                    color: theme.colors.text.inverse
                  }}
                >
                  {loading ? 'UPLOADING...' : 'SELECT FILE'}
                </label>
                
                {uploadedFile && (
                  <p className="mt-4 text-sm text-gray-400">
                    Selected: {uploadedFile.name}
                  </p>
                )}
              </div>

              <div className="mt-6 p-4 rounded-lg" style={{ background: `${theme.colors.bg.secondary}80` }}>
                <h4 className="font-semibold text-gray-300 mb-2">CSV Format Requirements:</h4>
                <ul className="text-sm text-gray-500 space-y-1">
                  <li>• Required columns: timestamp, open, high, low, close, volume</li>
                  <li>• Timestamp should be Unix epoch (seconds)</li>
                  <li>• Minimum 1000 rows recommended for analysis</li>
                  <li>• 5-minute OHLCV data for SOL/USD</li>
                </ul>
              </div>
            </motion.div>
          )}

          {activeTab === 'analysis' && (
            <motion.div
              key="analysis"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="grid md:grid-cols-2 gap-6">
                {/* Parameters */}
                <div className="p-8 rounded-2xl border backdrop-blur-xl"
                  style={{
                    background: `${theme.colors.bg.elevated}80`,
                    borderColor: theme.colors.border.default
                  }}
                >
                  <h2 className="text-2xl font-bold text-gray-200 mb-6">Analysis Parameters</h2>
                  
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-400 mb-2">
                        ATR Minimum
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={analysisParams.atr_min}
                        onChange={(e) => setAnalysisParams({...analysisParams, atr_min: parseFloat(e.target.value)})}
                        className="w-full px-4 py-3 rounded-lg border bg-black/40 text-gray-200 font-mono"
                        style={{ borderColor: theme.colors.border.default }}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-400 mb-2">
                        Volume Z-Score Minimum
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={analysisParams.volz_min}
                        onChange={(e) => setAnalysisParams({...analysisParams, volz_min: parseFloat(e.target.value)})}
                        className="w-full px-4 py-3 rounded-lg border bg-black/40 text-gray-200 font-mono"
                        style={{ borderColor: theme.colors.border.default }}
                      />
                    </div>

                    <button
                      onClick={runAnalysis}
                      disabled={!dataLoaded || loading}
                      className="w-full px-8 py-4 rounded-xl font-bold text-lg transition-all disabled:opacity-50"
                      style={{
                        background: theme.colors.accent.emerald,
                        color: theme.colors.text.inverse
                      }}
                    >
                      {loading ? 'ANALYZING...' : 'RUN ANALYSIS'}
                    </button>
                  </div>
                </div>

                {/* Results */}
                <div className="p-8 rounded-2xl border backdrop-blur-xl"
                  style={{
                    background: `${theme.colors.bg.elevated}80`,
                    borderColor: theme.colors.border.default
                  }}
                >
                  <h2 className="text-2xl font-bold text-gray-200 mb-6">Latest Signal</h2>
                  
                  {analysisResult ? (
                    analysisResult.message ? (
                      <div className="text-center py-12">
                        <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p className="text-gray-500">No confirmed signals found</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500">Direction</span>
                          <span className={`px-3 py-1 rounded-lg font-bold ${
                            analysisResult.side === 'long' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                          }`}>
                            {analysisResult.side?.toUpperCase()}
                          </span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500">Entry</span>
                          <span className="font-mono text-gray-200">${analysisResult.entry?.toFixed(2)}</span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500">Stop Loss</span>
                          <span className="font-mono text-gray-200">${analysisResult.sl?.toFixed(2)}</span>
                        </div>

                        <div className="border-t pt-4" style={{ borderColor: theme.colors.border.default }}>
                          <div className="grid grid-cols-3 gap-2 text-center">
                            <div>
                              <div className="text-xs text-gray-500 mb-1">TP1</div>
                              <div className="font-mono text-sm text-emerald-400">${analysisResult.tp1?.toFixed(2)}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500 mb-1">TP2</div>
                              <div className="font-mono text-sm text-emerald-400">${analysisResult.tp2?.toFixed(2)}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500 mb-1">TP3</div>
                              <div className="font-mono text-sm text-emerald-400">${analysisResult.tp3?.toFixed(2)}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  ) : (
                    <div className="text-center py-12">
                      <p className="text-gray-500">Run analysis to see results</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'backtest' && (
            <motion.div
              key="backtest"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="grid md:grid-cols-2 gap-6">
                {/* Parameters */}
                <div className="p-8 rounded-2xl border backdrop-blur-xl"
                  style={{
                    background: `${theme.colors.bg.elevated}80`,
                    borderColor: theme.colors.border.default
                  }}
                >
                  <h2 className="text-2xl font-bold text-gray-200 mb-6">Backtest Parameters</h2>
                  
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-400 mb-2">
                        ATR Minimum
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={backtestParams.atr_min}
                        onChange={(e) => setBacktestParams({...backtestParams, atr_min: parseFloat(e.target.value)})}
                        className="w-full px-4 py-3 rounded-lg border bg-black/40 text-gray-200 font-mono"
                        style={{ borderColor: theme.colors.border.default }}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-400 mb-2">
                        Volume Z-Score Minimum
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={backtestParams.volz_min}
                        onChange={(e) => setBacktestParams({...backtestParams, volz_min: parseFloat(e.target.value)})}
                        className="w-full px-4 py-3 rounded-lg border bg-black/40 text-gray-200 font-mono"
                        style={{ borderColor: theme.colors.border.default }}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-400 mb-2">
                        Initial Capital ($)
                      </label>
                      <input
                        type="number"
                        step="1000"
                        value={backtestParams.initial_capital}
                        onChange={(e) => setBacktestParams({...backtestParams, initial_capital: parseInt(e.target.value)})}
                        className="w-full px-4 py-3 rounded-lg border bg-black/40 text-gray-200 font-mono"
                        style={{ borderColor: theme.colors.border.default }}
                      />
                    </div>

                    <button
                      onClick={runBacktest}
                      disabled={!dataLoaded || loading}
                      className="w-full px-8 py-4 rounded-xl font-bold text-lg transition-all disabled:opacity-50"
                      style={{
                        background: theme.colors.accent.cyan,
                        color: theme.colors.text.inverse
                      }}
                    >
                      {loading ? 'RUNNING...' : 'RUN BACKTEST'}
                    </button>
                  </div>
                </div>

                {/* Results */}
                <div className="p-8 rounded-2xl border backdrop-blur-xl"
                  style={{
                    background: `${theme.colors.bg.elevated}80`,
                    borderColor: theme.colors.border.default
                  }}
                >
                  <h2 className="text-2xl font-bold text-gray-200 mb-6">Performance Metrics</h2>
                  
                  {backtestResult ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 rounded-lg" style={{ background: theme.colors.bg.secondary }}>
                          <div className="text-xs text-gray-500 mb-1">Total Trades</div>
                          <div className="text-2xl font-bold text-gray-200">{backtestResult.total_trades || 0}</div>
                        </div>

                        <div className="p-4 rounded-lg" style={{ background: theme.colors.bg.secondary }}>
                          <div className="text-xs text-gray-500 mb-1">Win Rate</div>
                          <div className="text-2xl font-bold text-emerald-400">
                            {backtestResult.win_rate ? `${backtestResult.win_rate.toFixed(1)}%` : '0%'}
                          </div>
                        </div>

                        <div className="p-4 rounded-lg" style={{ background: theme.colors.bg.secondary }}>
                          <div className="text-xs text-gray-500 mb-1">Total PnL</div>
                          <div className={`text-2xl font-bold ${
                            (backtestResult.total_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}>
                            ${backtestResult.total_pnl?.toFixed(2) || '0.00'}
                          </div>
                        </div>

                        <div className="p-4 rounded-lg" style={{ background: theme.colors.bg.secondary }}>
                          <div className="text-xs text-gray-500 mb-1">Sharpe Ratio</div>
                          <div className="text-2xl font-bold text-gray-200">
                            {backtestResult.sharpe_ratio?.toFixed(2) || '0.00'}
                          </div>
                        </div>
                      </div>

                      <div className="mt-6 p-4 rounded-lg" style={{ background: theme.colors.bg.secondary }}>
                        <div className="text-xs text-gray-500 mb-2">Final Balance</div>
                        <div className="text-3xl font-black text-cyan-400">
                          ${backtestResult.final_balance?.toFixed(2) || '0.00'}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <p className="text-gray-500">Run backtest to see results</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
