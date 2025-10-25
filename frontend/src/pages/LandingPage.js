import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        </div>

        {/* Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 py-20">
          {/* Header */}
          <nav className="flex items-center justify-between mb-20">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center">
                <span className="text-2xl">⚡</span>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                SWING MATRIX
              </span>
            </div>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-2.5 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-emerald-400 font-medium transition-all backdrop-blur-sm"
            >
              Launch App
            </button>
          </nav>

          {/* Hero Content */}
          <div className="text-center max-w-5xl mx-auto mb-20">
            <div className="inline-block mb-6 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-sm font-medium backdrop-blur-sm">
              ⚡ Live Signal Detection • Powered by AI
            </div>
            
            <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight">
              <span className="bg-gradient-to-r from-white via-emerald-100 to-white bg-clip-text text-transparent">
                Capture Every Swing
              </span>
              <br />
              <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                Before It Happens
              </span>
            </h1>

            <p className="text-xl text-slate-400 mb-10 max-w-3xl mx-auto leading-relaxed">
              Real-time swing detection system for SOL/USD trading. 
              Two-stage methodology with microstructure gates. 
              Manual execution cards with 7 pre-flight checks.
            </p>

            <div className="flex items-center justify-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="group px-8 py-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 rounded-xl text-white font-semibold text-lg transition-all shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:scale-105"
              >
                <span className="flex items-center space-x-2">
                  <span>Start Trading</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </span>
              </button>
              
              <button
                onClick={() => navigate('/live')}
                className="px-8 py-4 bg-slate-800/50 hover:bg-slate-800/70 border border-slate-700 rounded-xl text-white font-semibold text-lg transition-all backdrop-blur-sm"
              >
                View Live Signals
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 max-w-4xl mx-auto mb-20">
            {[
              { label: 'Success Rate', value: '67.2%', icon: '📈' },
              { label: 'Avg. R-Multiple', value: '2.1R', icon: '💰' },
              { label: 'Signals Today', value: '12', icon: '⚡' }
            ].map((stat, i) => (
              <div key={i} className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="relative p-6 bg-slate-900/60 backdrop-blur-xl border border-slate-800 rounded-2xl text-center hover:border-emerald-500/30 transition-all">
                  <div className="text-3xl mb-2">{stat.icon}</div>
                  <div className="text-3xl font-bold text-emerald-400 mb-1">{stat.value}</div>
                  <div className="text-sm text-slate-400">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="relative max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">
            Everything You Need to Trade <span className="text-emerald-400">Smarter</span>
          </h2>
          <p className="text-slate-400 text-lg">
            Professional-grade tools for manual swing trading
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: '🎯',
              title: 'Two-Stage Detection',
              description: 'Candidate screening + micro-confirmation with 7 pre-flight checks',
              color: 'emerald'
            },
            {
              icon: '📊',
              title: 'Microstructure Gates',
              description: 'Orderbook depth, spread, CVD, imbalance analysis in real-time',
              color: 'cyan'
            },
            {
              icon: '🎴',
              title: 'Scalp Cards',
              description: 'Complete trade specs with entry, SL, TP ladder, and trail rules',
              color: 'emerald'
            },
            {
              icon: '⚡',
              title: 'Live Monitoring',
              description: 'Real-time SOL/USD price feeds from Pyth Network',
              color: 'cyan'
            },
            {
              icon: '🔬',
              title: 'Deep Analytics',
              description: 'Backtest, analyze swings, optimize parameters',
              color: 'emerald'
            },
            {
              icon: '📡',
              title: 'WebSocket Streaming',
              description: 'Instant signal updates with auto-reconnect resilience',
              color: 'cyan'
            }
          ].map((feature, i) => (
            <div key={i} className="group relative">
              <div className={`absolute inset-0 bg-gradient-to-br from-${feature.color}-500/10 to-transparent rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity`}></div>
              <div className="relative p-8 bg-slate-900/40 backdrop-blur-xl border border-slate-800 rounded-2xl hover:border-emerald-500/30 transition-all">
                <div className="text-5xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-slate-400 leading-relaxed">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative max-w-7xl mx-auto px-6 py-20">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-900/40 to-slate-900/40 backdrop-blur-xl border border-emerald-500/20 p-12 text-center">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgxNiwxODUsMTI5LDAuMSkiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-20"></div>
          
          <div className="relative z-10">
            <h2 className="text-4xl font-bold text-white mb-4">
              Ready to Start Capturing Swings?
            </h2>
            <p className="text-slate-300 text-lg mb-8 max-w-2xl mx-auto">
              Join traders using data-driven methodology for manual execution
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-10 py-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 rounded-xl text-white font-bold text-lg transition-all shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50 hover:scale-105"
            >
              Launch Dashboard →
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-800 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center text-slate-500 text-sm">
          <p>EXTREMA v1.0 • Production-Grade Swing Detection System</p>
          <p className="mt-2">⚠️ Manual execution only • Not financial advice</p>
        </div>
      </div>
    </div>
  );
}
