import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Outlet } from 'react-router-dom';
import { Activity, Share2, PlayCircle, Trophy, Box } from 'lucide-react';
import useWebSocket from './hooks/useWebSocket';
import useStore from './store';
import Dashboard from './Dashboard';
import Clusters from './Clusters';
import Leaderboard from './Leaderboard';
import Model from './Model';
import StatusBanner from './StatusBanner';

const Layout = () => {
  const wsStatus = useStore(state => state.wsStatus);
  const alerts = useStore(state => state.alerts);
  const activeAlertCount = alerts.filter(a => a.status === 'unreviewed').length;
  
  // Calculate avg risk across all nodes
  const nodes = useStore(state => state.nodes);
  const avgRisk = nodes.length > 0 
    ? Math.round((nodes.reduce((acc, n) => acc + (n.risk || 0), 0) / nodes.length) * 100) 
    : 0;

  const navItems = [
    { name: 'Live Graph', path: '/', icon: Activity },
    { name: 'Clusters', path: '/clusters', icon: Share2 },
    { name: 'Leaderboard', path: '/leaderboard', icon: Trophy },
    { name: 'Model', path: '/model', icon: Box },
  ];

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0D1117] text-[#E6EDF3] font-['Inter']">
      <StatusBanner />
      
      {/* Header (48px) */}
      <header className="h-[48px] flex-shrink-0 bg-[#161B22] border-b border-[#30363D] flex items-center justify-between px-6 z-40">
        <div className="flex items-center">
          <span className="font-bold text-lg text-[#E6EDF3] tracking-wide">FraudGraph</span>
        </div>
        
        {/* Live Stat Pills */}
        <div className="flex items-center space-x-4 font-['JetBrains_Mono'] text-sm">
          <div className="bg-[#0D1117] border border-[#30363D] px-4 py-1 rounded-[20px] flex items-center space-x-2 shadow-sm">
            <span className="text-[#8B949E]">Avg Risk:</span>
            <span className="text-[#EF9F27] font-medium">{avgRisk}%</span>
          </div>
          
          <div className="bg-[#0D1117] border border-[#30363D] px-4 py-1 rounded-[20px] flex items-center space-x-2 shadow-sm">
            <span className="text-[#8B949E]">Active Alerts:</span>
            <span className="text-[#E24B4A] font-bold drop-shadow-[0_0_6px_rgba(226,75,74,0.6)]">{activeAlertCount}</span>
          </div>

          <div className="bg-[#0D1117] border border-[#30363D] px-4 py-1 rounded-[20px] flex items-center space-x-2 shadow-sm">
            <span className="text-[#8B949E]">WS:</span>
            <span className="flex items-center space-x-2">
              <span className={`w-2 h-2 rounded-full ${wsStatus === 'connected' ? 'bg-[#1D9E75]' : 'bg-[#E24B4A]'}`}></span>
              <span className={wsStatus === 'connected' ? 'text-[#1D9E75] font-medium' : 'text-[#E24B4A] font-medium'}>
                {wsStatus === 'connected' ? 'Connected' : 'Disconnected'}
              </span>
            </span>
          </div>
        </div>
      </header>

      {/* Main Area */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Sidebar (240px) */}
        <aside className="w-[240px] flex-shrink-0 bg-[#161B22] border-r border-[#30363D] flex flex-col py-4 z-40">
          <nav className="flex flex-col space-y-2 px-4">
            {navItems.map(item => (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-2 rounded-[8px] transition-colors ${
                    isActive 
                      ? 'bg-[#388ADD]/10 text-[#388ADD]' 
                      : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#30363D]/50'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.name}</span>
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 bg-[#0D1117] overflow-hidden relative">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

const AppRoot = () => {
  // Wire websocket globally
  useWebSocket();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="clusters" element={<Clusters />} />
          <Route path="leaderboard" element={<Leaderboard />} />
          <Route path="model" element={<Model />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default AppRoot;
