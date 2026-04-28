import React, { useState, useEffect } from 'react';
import useStore from './store';
import ForceGraph from './ForceGraph';
import AlertQueue from './AlertQueue';
import NodePanel from './NodePanel';
import ReplayBar from './ReplayBar';
import apiClient from './api/client';
import { Zap, AlertCircle } from 'lucide-react';

export default function Dashboard() {
  const nodes = useStore(state => state.nodes);
  const edges = useStore(state => state.edges);
  const selectedNodeId = useStore(state => state.selectedNodeId);
  const setSelectedNode = useStore(state => state.setSelectedNode);

  const [isInjecting, setIsInjecting] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const handleNodeClick = (node) => {
    setSelectedNode(node.id);
  };

  const handleClosePanel = () => {
    setSelectedNode(null);
  };

  const handleInject = async () => {
    if (cooldown > 0) return;
    
    try {
      setIsInjecting(true);
      await apiClient.post('/demo/inject');
      setShowToast(true);
      setCooldown(15);
      setTimeout(() => setShowToast(false), 5000);
    } catch (err) {
      console.error('Injection failed:', err);
    } finally {
      setIsInjecting(false);
    }
  };

  useEffect(() => {
    if (cooldown > 0) {
      const timer = setInterval(() => setCooldown(c => c - 1), 1000);
      return () => clearInterval(timer);
    }
  }, [cooldown]);

  return (
    <div className="relative w-full h-full flex overflow-hidden">
      
      {/* Main Graph Area */}
      <div className="flex-1 relative bg-[#0D1117] h-full">
        {/* Graph Control Bar */}
        <div className="absolute top-6 left-6 z-10 flex items-center space-x-3">
          <button
            onClick={handleInject}
            disabled={cooldown > 0 || isInjecting}
            className={`
              flex items-center space-x-2 px-4 py-2.5 rounded-full font-bold text-sm tracking-wide transition-all duration-300
              ${cooldown > 0 
                ? 'bg-[#30363D] text-[#8B949E] cursor-not-allowed opacity-70' 
                : 'bg-[#FF3B30] text-white hover:bg-[#FF453A] shadow-[0_0_20px_rgba(255,59,48,0.4)] hover:shadow-[0_0_30px_rgba(255,59,48,0.6)] animate-pulse-subtle'
              }
            `}
          >
            <Zap className={`w-4 h-4 ${cooldown === 0 ? 'fill-current' : ''}`} />
            <span>{cooldown > 0 ? `RECHARGING (${cooldown}s)` : 'INJECT FRAUD RING'}</span>
          </button>
        </div>

        {/* Toast Notification */}
        <div 
          className={`
            absolute top-6 left-1/2 -translate-x-1/2 z-40 transition-all duration-500 transform
            ${showToast ? 'translate-y-0 opacity-100' : '-translate-y-12 opacity-0 pointer-events-none'}
          `}
        >
          <div className="bg-[#1D9E75] text-white px-6 py-3 rounded-full shadow-2xl flex items-center space-x-3 border border-white/20">
            <AlertCircle className="w-5 h-5" />
            <span className="font-bold tracking-tight">Fraud ring injected — watch the graph evolve</span>
          </div>
        </div>

        <ForceGraph 
          nodes={nodes} 
          edges={edges} 
          onNodeClick={handleNodeClick} 
          selectedNodeId={selectedNodeId} 
        />
        
        {/* Replay Toolbar anchored to bottom of graph area */}
        <ReplayBar />
      </div>

      <div 
        className={`absolute top-0 right-[320px] h-full w-[320px] z-20`}
        style={{ pointerEvents: selectedNodeId !== null ? 'auto' : 'none' }}
      >
        <NodePanel 
          node={nodes.find(n => n.id === selectedNodeId) || null} 
          isOpen={selectedNodeId !== null} 
          onClose={handleClosePanel} 
        />
      </div>

      {/* Alert Queue - Fixed Right Sidebar (320px) */}
      <div className="w-[320px] h-full flex-shrink-0 bg-[#161B22] border-l border-[#30363D] z-30">
        <AlertQueue />
      </div>
      
    </div>
  );
}
