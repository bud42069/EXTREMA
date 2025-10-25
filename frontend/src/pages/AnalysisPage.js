import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useLocation, useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AnalysisPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(location.state?.datasetId || '');
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
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const response = await axios.get(`${API}/datasets`);
      setDatasets(response.data.datasets || []);
    } catch (error) {
      console.error('Error fetching datasets:', error);
      toast.error('Failed to load datasets');
    }
  };

  const handleAnalyze = async () => {
    if (!selectedDataset) {
      toast.error('Please select a dataset');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await axios.post(`${API}/analyze?dataset_id=${selectedDataset}`, config);
      
      if (response.data.success) {
        toast.success('Analysis completed!');
        setAnalysisResult(response.data);
      }
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error(error.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">Signal Analysis</h1>
        <p className="text-gray-400">Run two-stage detection to identify swing trading signals</p>
      </div>

      {/* Configuration Panel */}
      <div className="bg-gray-900 rounded-lg p-8 mb-6">
        <h2 className="text-2xl font-bold text-white mb-6">Analysis Configuration</h2>
        
        {/* Dataset Selection */}
        <div className="mb-6">
          <label className="block text-gray-300 mb-2">Select Dataset</label>
          <select
            value={selectedDataset}
            onChange={(e) => setSelectedDataset(e.target.value)}
            className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:border-blue-500"
          >
            <option value="">Choose a dataset...</option>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.filename} ({dataset.total_bars} bars)
              </option>
            ))}
          </select>
        </div>

        {/* Stage 1: Candidate Detection */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-blue-400 mb-4">Stage 1: Candidate Detection</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-gray-300 text-sm mb-2">ATR14 Threshold</label>
              <input
                type="number"
                step="0.1"
                value={config.atr_threshold}
                onChange={(e) => setConfig({...config, atr_threshold: parseFloat(e.target.value)})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 text-sm mb-2">Volume Z-Score Threshold</label>
              <input
                type="number"
                step="0.1"
                value={config.vol_z_threshold}
                onChange={(e) => setConfig({...config, vol_z_threshold: parseFloat(e.target.value)})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 text-sm mb-2">BB Width Threshold</label>
              <input
                type="number"
                step="0.001"
                value={config.bb_width_threshold}
                onChange={(e) => setConfig({...config, bb_width_threshold: parseFloat(e.target.value)})}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Stage 2: Micro Confirmation */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-blue-400 mb-4">Stage 2: Micro Confirmation</h3>
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
                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={analyzing || !selectedDataset}
          className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
        >
          {analyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>
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