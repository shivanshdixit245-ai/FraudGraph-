import React, { useEffect, useRef } from 'react';
import useStore from './store'; 
import { CheckCircle2, AlertTriangle, XOctagon } from 'lucide-react';

const formatTime = (isoString) => {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

const AlertCard = ({ alert, updateAlertStatus }) => {
  const isHandled = alert.status !== 'unreviewed';
  const riskPct = Math.round((alert.risk || 0) * 100);
  
  let badgeColor = '#EF9F27';
  let badgeText = 'MEDIUM';
  if (alert.risk > 0.7) {
    badgeColor = '#E24B4A';
    badgeText = 'HIGH';
  }

  return (
    <div className={`p-4 border-b border-[#30363D] transition-opacity duration-300 animate-slide-down ${isHandled ? 'opacity-40' : 'opacity-100'}`}>
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center space-x-2">
          <span 
            className="px-2 py-0.5 rounded-[4px] text-[10px] font-bold text-[#E6EDF3] tracking-wide"
            style={{ backgroundColor: badgeColor }}
          >
            {badgeText}
          </span>
          <span className="text-[#8B949E] text-xs font-['Inter']">
            {formatTime(alert.timestamp)}
          </span>
        </div>
        <div className="text-right">
          <span className="font-['JetBrains_Mono'] font-bold" style={{ color: badgeColor }}>
            {riskPct}%
          </span>
        </div>
      </div>

      <div className="mb-3">
        <div className="text-[#8B949E] text-[10px] uppercase tracking-wider font-['Inter'] mb-0.5">Account</div>
        <div className="font-['JetBrains_Mono'] text-sm text-[#E6EDF3]">{alert.label || alert.nodeId}</div>
      </div>

      <div className="mb-4">
        <div className="text-[#8B949E] text-[10px] uppercase tracking-wider font-['Inter'] mb-0.5">Top Driver</div>
        <div className="font-['Inter'] text-sm text-[#E6EDF3]">{alert.topReason || 'Unknown'}</div>
      </div>

      {/* Action Buttons */}
      {!isHandled ? (
        <div className="flex space-x-2">
          <button 
            onClick={() => updateAlertStatus(alert.id, 'reviewed')}
            className="flex-1 flex items-center justify-center space-x-1 py-1.5 rounded-[4px] bg-[#1D9E75]/10 text-[#1D9E75] hover:bg-[#1D9E75]/20 transition-colors border border-[#1D9E75]/30 text-xs font-medium"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Reviewed</span>
          </button>
          
          <button 
            onClick={() => updateAlertStatus(alert.id, 'escalated')}
            className="flex-1 flex items-center justify-center space-x-1 py-1.5 rounded-[4px] bg-[#EF9F27]/10 text-[#EF9F27] hover:bg-[#EF9F27]/20 transition-colors border border-[#EF9F27]/30 text-xs font-medium"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Escalate</span>
          </button>

          <button 
            onClick={() => updateAlertStatus(alert.id, 'false_positive')}
            className="flex-1 flex items-center justify-center space-x-1 py-1.5 rounded-[4px] bg-[#8B949E]/10 text-[#8B949E] hover:bg-[#8B949E]/20 transition-colors border border-[#8B949E]/30 text-xs font-medium"
          >
            <XOctagon className="w-3.5 h-3.5" />
            <span>False +</span>
          </button>
        </div>
      ) : (
        <div className="text-xs text-[#8B949E] font-medium font-['Inter'] uppercase flex items-center">
          <span className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: alert.status === 'reviewed' ? '#1D9E75' : alert.status === 'escalated' ? '#EF9F27' : '#8B949E' }}></span>
          {alert.status.replace('_', ' ')}
        </div>
      )}
    </div>
  );
};

export default function AlertQueue() {
  const nodes = useStore((state) => state.nodes);
  const alerts = useStore((state) => state.alerts);
  const addAlert = useStore((state) => state.addAlert);
  const updateAlertStatus = useStore((state) => state.updateAlertStatus);

  const alertedNodeIds = useRef(new Set());

  // Auto-generate alerts when a node hits risk > 0.8
  useEffect(() => {
    nodes.forEach(node => {
      if (node.risk > 0.8 && !alertedNodeIds.current.has(node.id)) {
        alertedNodeIds.current.add(node.id);
        
        // Find top SHAP reason if available
        let topReason = 'Behavioral Anomaly';
        if (node.shap && node.shap.length > 0) {
          // Sort by absolute impact
          const sortedShap = [...node.shap].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
          topReason = sortedShap[0].feature;
        }

        const newAlert = {
          id: `alert-${Date.now()}-${node.id}`,
          nodeId: node.id,
          label: node.label || node.id,
          risk: node.risk,
          topReason: topReason,
          timestamp: new Date().toISOString(),
          status: 'unreviewed'
        };

        addAlert(newAlert);
      }
    });
  }, [nodes, addAlert]);

  const unreviewedCount = alerts.filter(a => a.status === 'unreviewed').length;

  const sortedAlerts = [...alerts].sort((a, b) => {
    // 1. Sort by Risk descending
    if (b.risk !== a.risk) {
      return b.risk - a.risk;
    }
    // 2. Fallback to newest first
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });

  return (
    <div className="w-[320px] h-full bg-[#161B22] border-l border-[#30363D] flex flex-col font-['Inter'] flex-shrink-0 z-40 shadow-2xl relative">
      <style>
        {`
          @keyframes slideDown {
            from { opacity: 0; transform: translateY(-15px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
          }
          .animate-slide-down {
            animation: slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          }
        `}
      </style>
      
      {/* Header */}
      <div className="h-[48px] px-4 flex items-center justify-between border-b border-[#30363D] bg-[#0D1117] flex-shrink-0">
        <span className="font-semibold text-[#E6EDF3]">Live Alerts</span>
        {unreviewedCount > 0 && (
          <span className="bg-[#E24B4A] text-[#E6EDF3] text-xs font-bold px-2 py-0.5 rounded-full drop-shadow-[0_0_4px_rgba(226,75,74,0.4)]">
            {unreviewedCount} New
          </span>
        )}
      </div>

      {/* Alert List */}
      <div className="flex-1 overflow-y-auto bg-[#161B22]">
        {sortedAlerts.length === 0 ? (
          <div className="p-6 flex flex-col items-center justify-center text-center h-full space-y-3">
            <div className="w-8 h-8 rounded-full bg-[#1D9E75]/20 flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-[#1D9E75] shadow-[0_0_8px_rgba(29,158,117,0.8)] animate-pulse"></div>
            </div>
            <p className="text-[#8B949E] text-sm">No alerts — system nominal</p>
          </div>
        ) : (
          <div className="flex flex-col">
            {sortedAlerts.map(alert => (
              <AlertCard 
                key={alert.id} 
                alert={alert} 
                updateAlertStatus={updateAlertStatus} 
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
