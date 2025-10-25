import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import pages
import LandingPageV2 from './pages/LandingPageV2';
import OverviewPageV2 from './pages/OverviewPageV2';
import LiveSignalsDashboardV2 from './pages/LiveSignalsDashboardV2';
import ScalpCardsPageV2 from './pages/ScalpCardsPageV2';
import DataAnalysisPage from './pages/DataAnalysisPage';

// Modern Sidebar Component
const Sidebar = () => {
  const location = useLocation();
  
  const navItems = [
    { 
      path: '/dashboard', 
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      label: 'Overview',
      badge: null
    },
    { 
      path: '/live', 
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      label: 'Live Signals',
      badge: 'LIVE'
    },
    { 
      path: '/scalp-cards', 
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
      label: 'Scalp Cards',
      badge: null
    },
    { 
      path: '/data-analysis', 
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      label: 'Data Analysis',
      badge: null
    }
  ];

  return (
    <div className="w-72 bg-gradient-to-b from-slate-900 to-slate-950 border-r border-slate-800 min-h-screen p-6 fixed left-0 top-0 z-50">
      {/* Logo */}
      <Link to="/" className="flex items-center space-x-3 mb-12 group">
        <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg shadow-emerald-500/25">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
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
                <div className={isActive ? 'text-emerald-400' : 'text-slate-400 group-hover:text-white'}>
                  {item.icon}
                </div>
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
            <Route path="/" element={<LandingPageV2 />} />
            <Route path="/dashboard" element={<OverviewPageV2 />} />
            <Route path="/live" element={<LiveSignalsDashboardV2 />} />
            <Route path="/scalp-cards" element={<ScalpCardsPageV2 />} />
            <Route path="/data-analysis" element={<DataAnalysisPage />} />
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
