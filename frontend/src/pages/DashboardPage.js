import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DashboardPage = () => {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const response = await axios.get(`${API}/datasets`);
      setDatasets(response.data.datasets || []);
    } catch (error) {
      console.error('Error fetching datasets:', error);
      toast.error('Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">Trading Dashboard</h1>
        <p className="text-gray-400">Two-stage swing detection for SOLUSDT</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 shadow-lg">
          <div className="text-blue-100 text-sm mb-1">Total Datasets</div>
          <div className="text-3xl font-bold text-white">{datasets.length}</div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-6 shadow-lg">
          <div className="text-purple-100 text-sm mb-1">Strategy</div>
          <div className="text-xl font-bold text-white">Two-Stage</div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-6 shadow-lg">
          <div className="text-green-100 text-sm mb-1">Target</div>
          <div className="text-xl font-bold text-white">&gt;10% Swings</div>
        </div>
        
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg p-6 shadow-lg">
          <div className="text-orange-100 text-sm mb-1">Timeframe</div>
          <div className="text-xl font-bold text-white">5 Minutes</div>
        </div>
      </div>

      {/* Getting Started */}
      <div className="bg-gray-900 rounded-lg p-8 mb-8">
        <h2 className="text-2xl font-bold text-white mb-4">Getting Started</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800 rounded-lg p-6 cursor-pointer hover:bg-gray-750 transition-colors"
               onClick={() => navigate('/upload')}>
            <div className="text-4xl mb-3">📁</div>
            <h3 className="text-lg font-semibold text-white mb-2">1. Upload Data</h3>
            <p className="text-gray-400 text-sm">Upload your SOLUSDT 5-minute OHLCV CSV file</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 cursor-pointer hover:bg-gray-750 transition-colors"
               onClick={() => navigate('/analysis')}>
            <div className="text-4xl mb-3">🔍</div>
            <h3 className="text-lg font-semibold text-white mb-2">2. Analyze Signals</h3>
            <p className="text-gray-400 text-sm">Run two-stage detection to find swing candidates</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 cursor-pointer hover:bg-gray-750 transition-colors"
               onClick={() => navigate('/backtest')}>
            <div className="text-4xl mb-3">📈</div>
            <h3 className="text-lg font-semibold text-white mb-2">3. Backtest</h3>
            <p className="text-gray-400 text-sm">Test strategy with TP/SL ladder and get metrics</p>
          </div>
        </div>
      </div>

      {/* Recent Datasets */}
      <div className="bg-gray-900 rounded-lg p-8">
        <h2 className="text-2xl font-bold text-white mb-4">Recent Datasets</h2>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-400 mt-4">Loading datasets...</p>
          </div>
        ) : datasets.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📊</div>
            <p className="text-gray-400 mb-4">No datasets uploaded yet</p>
            <button
              onClick={() => navigate('/upload')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Upload Your First Dataset
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left text-gray-400 pb-3 pr-4">Filename</th>
                  <th className="text-left text-gray-400 pb-3 pr-4">Uploaded</th>
                  <th className="text-right text-gray-400 pb-3 pr-4">Total Bars</th>
                  <th className="text-right text-gray-400 pb-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset) => (
                  <tr key={dataset.id} className="border-b border-gray-800 hover:bg-gray-800">
                    <td className="py-4 pr-4 text-white">{dataset.filename}</td>
                    <td className="py-4 pr-4 text-gray-400 text-sm">
                      {new Date(dataset.uploaded_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 pr-4 text-right text-gray-300">
                      {dataset.total_bars.toLocaleString()}
                    </td>
                    <td className="py-4 text-right">
                      <button
                        onClick={() => navigate('/analysis', { state: { datasetId: dataset.id } })}
                        className="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        Analyze →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Methodology Info */}
      <div className="bg-gray-900 rounded-lg p-8 mt-8">
        <h2 className="text-2xl font-bold text-white mb-4">Trading Methodology</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-blue-400 mb-2">Stage 1: Candidate Detection</h3>
            <ul className="space-y-2 text-gray-300 text-sm">
              <li>• Detect local extrema (±12 bars)</li>
              <li>• ATR14 ≥ 0.6 (volatility filter)</li>
              <li>• Volume z-score ≥ 0.5</li>
              <li>• BB Width ≥ 0.005 (expansion)</li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold text-blue-400 mb-2">Stage 2: Micro Confirmation</h3>
            <ul className="space-y-2 text-gray-300 text-sm">
              <li>• Breakout candle (close beyond extrema + 0.5×ATR5)</li>
              <li>• Volume spike (≥1.5× median)</li>
              <li>• Confirmation within 6 bars (30 min)</li>
              <li>• TP/SL ladder with trailing stop</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;