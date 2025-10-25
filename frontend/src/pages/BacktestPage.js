import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useLocation } from 'react-router-dom';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BacktestPage = () => {
  const location = useLocation();
  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState(location.state?.analysisId || '');
  const [backtesting, setBacktesting] = useState(false);
  const [backtestResult, setBacktestResult] = useState(null);
  
  const [config, setConfig] = useState({
    initial_capital: 10000,
    risk_per_trade: 0.02,
    tp1_r: 1.0,
    tp2_r: 2.0,
    tp3_r: 3.5,
    tp1_scale: 0.5,
    tp2_scale: 0.3
  });

  useEffect(() => {
    // For now, we'll need to manually input analysis ID
    // In production, you'd fetch available analyses
  }, []);

  const handleBacktest = async () => {
    if (!selectedAnalysis) {
      toast.error('Please enter an analysis ID');
      return;
    }

    setBacktesting(true);
    try {
      const response = await axios.post(`${API}/backtest`, {
        analysis_id: selectedAnalysis,
        ...config
      });
      
      if (response.data.success) {
        toast.success('Backtest completed!');
        
        // Fetch full backtest details
        const detailsResponse = await axios.get(`${API}/backtest/${response.data.backtest_id}`);
        setBacktestResult(detailsResponse.data);
      }
    } catch (error) {
      console.error('Backtest error:', error);
      toast.error(error.response?.data?.detail || 'Backtest failed');
    } finally {
      setBacktesting(false);
    }
  };

  const stats = backtestResult?.statistics;

  return (
    <div className="max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">Backtest Strategy</h1>
        <p className="text-gray-400">Test your trading strategy with TP/SL ladder and get performance metrics</p>
      </div>

      {/* Configuration Panel */}
      <div className="bg-gray-900 rounded-lg p-8 mb-6">
        <h2 className="text-2xl font-bold text-white mb-6">Backtest Configuration</h2>
        
        {/* Analysis ID Input */}
        <div className="mb-6">
          <label className="block text-gray-300 mb-2">Analysis ID</label>
          <input
            type="text"
            value={selectedAnalysis}
            onChange={(e) => setSelectedAnalysis(e.target.value)}
            placeholder="Enter analysis ID from previous step"
            className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Capital & Risk Management */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-blue-400 mb-4">Capital & Risk Management</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm mb-2">Initial Capital ($)</label>
              <input
                type="number"
                value={config.initial_capital}
                onChange={(e) => setConfig({...config, initial_capital: parseFloat(e.target.value)})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 text-sm mb-2">Risk Per Trade (%)</label>
              <input
                type="number"
                step="0.01"
                value={config.risk_per_trade * 100}
                onChange={(e) => setConfig({...config, risk_per_trade: parseFloat(e.target.value) / 100})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* TP/SL Ladder */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-blue-400 mb-4">Take Profit Ladder (R Multiples)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-gray-300 text-sm mb-2">TP1 (R)</label>
              <input
                type="number"
                step="0.1"
                value={config.tp1_r}
                onChange={(e) => setConfig({...config, tp1_r: parseFloat(e.target.value)})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 text-sm mb-2">TP2 (R)</label>
              <input
                type="number"
                step="0.1"
                value={config.tp2_r}
                onChange={(e) => setConfig({...config, tp2_r: parseFloat(e.target.value)})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 text-sm mb-2">TP3 (R)</label>
              <input
                type="number"
                step="0.1"
                value={config.tp3_r}
                onChange={(e) => setConfig({...config, tp3_r: parseFloat(e.target.value)})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div>
              <label className="block text-gray-300 text-sm mb-2">TP1 Scale (% of position)</label>
              <input
                type="number"
                step="0.1"
                value={config.tp1_scale * 100}
                onChange={(e) => setConfig({...config, tp1_scale: parseFloat(e.target.value) / 100})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 text-sm mb-2">TP2 Scale (% of position)</label>
              <input
                type="number"
                step="0.1"
                value={config.tp2_scale * 100}
                onChange={(e) => setConfig({...config, tp2_scale: parseFloat(e.target.value) / 100})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        <button
          onClick={handleBacktest}
          disabled={backtesting || !selectedAnalysis}
          className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
        >
          {backtesting ? 'Running Backtest...' : 'Run Backtest'}
        </button>
      </div>

      {/* Backtest Results */}
      {stats && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="bg-gray-900 rounded-lg p-8">
            <h2 className="text-2xl font-bold text-white mb-6">Performance Metrics</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Total Trades</p>
                <p className="text-3xl font-bold text-white">{stats.total_trades}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Win Rate</p>
                <p className="text-3xl font-bold text-green-400">{stats.win_rate.toFixed(1)}%</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Avg R</p>
                <p className={`text-3xl font-bold ${stats.avg_r >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {stats.avg_r.toFixed(2)}R
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Total P&L</p>
                <p className={`text-3xl font-bold ${stats.total_pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {stats.total_pnl_pct >= 0 ? '+' : ''}{stats.total_pnl_pct.toFixed(2)}%
                </p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Wins / Losses</p>
                <p className="text-xl font-bold text-white">{stats.wins} / {stats.losses}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Avg Win / Loss</p>
                <p className="text-xl font-bold text-white">
                  {stats.avg_win.toFixed(2)}% / {stats.avg_loss.toFixed(2)}%
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Profit Factor</p>
                <p className="text-xl font-bold text-white">{stats.profit_factor.toFixed(2)}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Avg Bars Held</p>
                <p className="text-xl font-bold text-white">{stats.avg_bars_held.toFixed(0)}</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Max Win</p>
                <p className="text-xl font-bold text-green-400">+{stats.max_pnl_pct.toFixed(2)}%</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Max Loss</p>
                <p className="text-xl font-bold text-red-400">{stats.min_pnl_pct.toFixed(2)}%</p>
              </div>
            </div>
          </div>

          {/* Trade List */}
          <div className="bg-gray-900 rounded-lg p-8">
            <h2 className="text-2xl font-bold text-white mb-6">Trade History</h2>
            
            {backtestResult.trades && backtestResult.trades.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left text-gray-400 pb-3 pr-4">Entry</th>
                      <th className="text-left text-gray-400 pb-3 pr-4">Exit</th>
                      <th className="text-center text-gray-400 pb-3 pr-4">Direction</th>
                      <th className="text-center text-gray-400 pb-3 pr-4">Exit Reason</th>
                      <th className="text-right text-gray-400 pb-3 pr-4">P&L %</th>
                      <th className="text-right text-gray-400 pb-3">P&L R</th>
                    </tr>
                  </thead>
                  <tbody>
                    {backtestResult.trades.map((trade, idx) => (
                      <tr key={idx} className="border-b border-gray-800 hover:bg-gray-800">
                        <td className="py-3 pr-4 text-gray-300 text-sm">
                          ${trade.entry_price.toFixed(2)}
                        </td>
                        <td className="py-3 pr-4 text-gray-300 text-sm">
                          ${trade.exit_price.toFixed(2)}
                        </td>
                        <td className="py-3 pr-4 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            trade.direction === 'long' 
                              ? 'bg-green-900 text-green-300' 
                              : 'bg-red-900 text-red-300'
                          }`}>
                            {trade.direction.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-center text-gray-400 text-sm">
                          {trade.exit_reason}
                        </td>
                        <td className={`py-3 pr-4 text-right font-semibold ${
                          trade.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%
                        </td>
                        <td className={`py-3 text-right font-semibold ${
                          trade.pnl_r >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {trade.pnl_r >= 0 ? '+' : ''}{trade.pnl_r.toFixed(2)}R
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center text-gray-400 py-8">No trades found</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BacktestPage;