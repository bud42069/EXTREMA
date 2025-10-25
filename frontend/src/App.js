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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Sidebar Navigation Component
const Sidebar = () => {
  return (
    <div className="w-64 bg-gray-900 text-white min-h-screen p-4 fixed left-0 top-0">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-blue-400">Swing Detector</h1>
        <p className="text-xs text-gray-400 mt-1">SOLUSDT Trading Analysis</p>
      </div>
      
      <nav className="space-y-2">
        <Link
          to="/"
          className="block px-4 py-3 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">📊</span>
            <span>Dashboard</span>
          </div>
        </Link>
        
        <Link
          to="/upload"
          className="block px-4 py-3 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">📁</span>
            <span>Upload Data</span>
          </div>
        </Link>
        
        <Link
          to="/analysis"
          className="block px-4 py-3 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">🔍</span>
            <span>Signal Analysis</span>
          </div>
        </Link>
        
        <Link
          to="/backtest"
          className="block px-4 py-3 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl">📈</span>
            <span>Backtest</span>
          </div>
        </Link>
      </nav>
      
      <div className="absolute bottom-4 left-4 right-4">
        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-400">Trading Strategy</p>
          <p className="text-sm font-semibold mt-1">Two-Stage Detection</p>
          <p className="text-xs text-gray-500 mt-2">Target: &gt;10% swings</p>
        </div>
      </div>
    </div>
  );
};

// Main Layout Component
const Layout = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-gray-950">
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
