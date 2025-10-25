import React, { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import pages
import UploadPage from "./pages/UploadPage";
import AnalysisPage from "./pages/AnalysisPage";
import BacktestPage from "./pages/BacktestPage";
import DashboardPage from "./pages/DashboardPage";
import LiveSignalsPage from "./pages/LiveSignalsPage";
import ScalpCardsPage from "./pages/ScalpCardsPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Sidebar Navigation Component
const Sidebar = () => {
  return (
    <div className="w-64 bg-gray-900 text-white min-h-screen p-4 fixed left-0 top-0 border-r border-green-500/20">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-cyan-400 font-mono">
          SWING MATRIX
        </h1>
        <p className="text-xs text-gray-400 mt-1 font-mono">SOL Trading System</p>
      </div>
      
      <nav className="space-y-2">
        <Link
          to="/live"
          className="block px-4 py-3 rounded-lg hover:bg-green-500/10 transition-colors border border-transparent hover:border-green-500/50"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">📡</span>
            <span className="font-mono">Live Signals</span>
          </div>
        </Link>
        
        <Link
          to="/scalp-cards"
          className="block px-4 py-3 rounded-lg hover:bg-green-500/10 transition-colors border border-transparent hover:border-green-500/50"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">🎯</span>
            <span className="font-mono">Scalp Cards</span>
          </div>
        </Link>
        
        <Link
          to="/"
          className="block px-4 py-3 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">📊</span>
            <span className="font-mono">Dashboard</span>
          </div>
        </Link>
        
        <Link
          to="/upload"
          className="block px-4 py-3 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">📁</span>
            <span className="font-mono">Upload Data</span>
          </div>
        </Link>
        
        <Link
          to="/analysis"
          className="block px-4 py-3 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">🔍</span>
            <span className="font-mono">Analysis</span>
          </div>
        </Link>
        
        <Link
          to="/backtest"
          className="block px-4 py-3 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">📈</span>
            <span className="font-mono">Backtest</span>
          </div>
        </Link>
      </nav>
      
      <div className="absolute bottom-4 left-4 right-4">
        <div className="bg-gradient-to-br from-green-900/30 to-cyan-900/30 rounded-lg p-4 border border-green-500/30">
          <p className="text-xs text-gray-400 font-mono">METHODOLOGY</p>
          <p className="text-sm font-semibold mt-1 text-green-300 font-mono">Two-Stage Detection</p>
          <p className="text-xs text-gray-500 mt-2 font-mono">Target: &gt;10% swings</p>
        </div>
      </div>
    </div>
  );
};

// Main Layout Component
const Layout = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-black">
      <Sidebar />
      <div className="ml-64 flex-1 p-8">
        {children}
      </div>
      <ToastContainer 
        position="top-right"
        theme="dark"
        autoClose={3000}
      />
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/live" element={<LiveSignalsPage />} />
            <Route path="/scalp-cards" element={<ScalpCardsPage />} />
            <Route path="/" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/backtest" element={<BacktestPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </div>
  );
}

export default App;
