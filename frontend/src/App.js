import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import pages
import LandingPage from './pages/LandingPage';
import OverviewPage from './pages/OverviewPage';
import LiveSignalsPageNew from './pages/LiveSignalsPageNew';
import LiveSignalsDashboardV2 from './pages/LiveSignalsDashboardV2';
import ScalpCardsPage from './pages/ScalpCardsPage';
import UploadPage from './pages/UploadPage';
import AnalysisPage from './pages/AnalysisPage';
import BacktestPage from './pages/BacktestPage';

// Modern Sidebar Component
const Sidebar = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/dashboard', icon: '📊', label: 'Overview', badge: null },
    { path: '/live', icon: '📡', label: 'Live Signals', badge: 'LIVE' },
    { path: '/scalp-cards', icon: '🎯', label: 'Scalp Cards', badge: null },
    { path: '/upload', icon: '📁', label: 'Upload Data', badge: null },
    { path: '/analysis', icon: '🔬', label: 'Analysis', badge: null },
    { path: '/backtest', icon: '📈', label: 'Backtest', badge: null }
  ];

  return (
    <div className="w-72 bg-gradient-to-b from-slate-900 to-slate-950 border-r border-slate-800 min-h-screen p-6 fixed left-0 top-0 z-50">
      {/* Logo */}
      <Link to="/" className="flex items-center space-x-3 mb-12 group">
        <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg shadow-emerald-500/25">
          <span className="text-2xl">⚡</span>
        </div>
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            SWING MATRIX
          </h1>
          <p className="text-xs text-slate-500 font-mono">v1.0 Production</p>
        </div>
      </Link>

      {/* Navigation */}
      <nav className="space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`group relative flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-emerald-500/10 to-transparent border border-emerald-500/30'
                  : 'hover:bg-slate-800/50 border border-transparent hover:border-slate-700'
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{item.icon}</span>
                <span className={`font-medium ${
                  isActive ? 'text-emerald-400' : 'text-slate-400 group-hover:text-white'
                }`}>
                  {item.label}
                </span>
              </div>
              {item.badge && (
                <span className="px-2 py-0.5 text-xs font-bold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  {item.badge}
                </span>
              )}
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-r-full"></div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* System Status */}
      <div className="absolute bottom-6 left-6 right-6">
        <div className="p-4 bg-slate-800/50 backdrop-blur-xl border border-slate-700 rounded-xl">
          <div className="text-xs text-slate-500 mb-3 font-mono uppercase">System Status</div>
          <div className="space-y-2">
            {[
              { label: 'API', status: true },
              { label: 'WebSocket', status: true },
              { label: 'Data Pipeline', status: true }
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-sm text-slate-400">{item.label}</span>
                <div className="flex items-center space-x-1.5">
                  <div className={`w-1.5 h-1.5 rounded-full ${
                    item.status ? 'bg-emerald-400' : 'bg-slate-600'
                  }`}></div>
                  <span className={`text-xs ${
                    item.status ? 'text-emerald-400' : 'text-slate-600'
                  }`}>
                    {item.status ? 'OK' : 'OFF'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Layout with Sidebar
const Layout = ({ children }) => {
  const location = useLocation();
  const isLanding = location.pathname === '/';

  if (isLanding) {
    return <>{children}</>;
  }

  return (
    <div className="flex">
      <Sidebar />
      <div className="ml-72 flex-1">
        {children}
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<OverviewPage />} />
            <Route path="/live" element={<LiveSignalsPageNew />} />
            <Route path="/scalp-cards" element={<ScalpCardsPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/backtest" element={<BacktestPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
      <ToastContainer
        position="bottom-right"
        autoClose={3000}
        theme="dark"
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />
    </div>
  );
}

export default App;
