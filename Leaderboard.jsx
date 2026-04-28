import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useStore from './store';
import { Search, Info, RotateCcw } from 'lucide-react';
import apiClient from './api/client';

const LEADERBOARD_MOCK = [
  { rank: 1, node_id: 12, label: "ACC-1521", centrality: 0.0391, risk: 0.91 },
  { rank: 2, node_id: 0,  label: "ACC-1042", centrality: 0.0412, risk: 0.94 },
  { rank: 3, node_id: 8,  label: "ACC-1377", centrality: 0.0348, risk: 0.83 },
  { rank: 4, node_id: 1,  label: "ACC-1087", centrality: 0.0381, risk: 0.88 },
  { rank: 5, node_id: 10, label: "ACC-1456", centrality: 0.0212, risk: 0.71 },
  { rank: 6, node_id: 3,  label: "ACC-1156", centrality: 0.0178, risk: 0.61 },
  { rank: 7, node_id: 4,  label: "ACC-1201", centrality: 0.0143, risk: 0.55 },
  { rank: 8, node_id: 14, label: "ACC-1607", centrality: 0.0119, risk: 0.44 },
  { rank: 9, node_id: 9,  label: "ACC-1402", centrality: 0.0091, risk: 0.22 },
  { rank:10, node_id: 5,  label: "ACC-1234", centrality: 0.0073, risk: 0.18 }
];

export default function Leaderboard() {
  const [data, setData] = useState([]);
  const [lastFetched, setLastFetched] = useState(Date.now());
  const [secondsAgo, setSecondsAgo] = useState(0);
  const [isFetching, setIsFetching] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  
  const setSelectedNode = useStore(state => state.setSelectedNode);
  const navigate = useNavigate();

  const load = async (isManual = false) => {
    if (isManual) setIsFetching(true);
    try {
      const response = await apiClient.get('/centrality');
      if (!response.data) throw new Error('not ok');
      const json = response.data;
      
      const rawResults = json.results || json;
      let sorted = [];
      if (Array.isArray(rawResults)) {
        sorted = rawResults.sort((a, b) => (b.centrality || 0) - (a.centrality || 0));
      } else if (rawResults && typeof rawResults === 'object') {
        // Fallback if data is wrapped differently
        const values = Object.values(rawResults).find(Array.isArray);
        if (values) {
          sorted = values.sort((a, b) => (b.centrality || 0) - (a.centrality || 0));
        }
      }
      
      console.log("[Leaderboard] Parsed data:", sorted);
      setData(sorted);
      setIsDemo(false);
      setLastFetched(Date.now());
    } catch (err) {
      console.error('Failed to fetch centrality, using demo data:', err);
      setData(LEADERBOARD_MOCK);
      setIsDemo(true);
      setLastFetched(Date.now());
    } finally {
      if (isManual) setIsFetching(false);
    }
  };

  const fetchData = () => load(true);

  // Initial load and periodic refresh
  useEffect(() => {
    load();
    const fetchInterval = setInterval(load, 30000);
    return () => clearInterval(fetchInterval);
  }, []);

  // 1s ticker for the "Updated X seconds ago" counter
  useEffect(() => {
    const tickerInterval = setInterval(() => {
      setSecondsAgo(Math.floor((Date.now() - lastFetched) / 1000));
    }, 1000);
    return () => clearInterval(tickerInterval);
  }, [lastFetched]);

  const handleInspect = (nodeId) => {
    setSelectedNode(nodeId);
    navigate('/'); // Redirect to LiveGraph
  };

  return (
    <div className="flex flex-col h-full bg-[#0D1117] font-['Inter'] relative">
      {/* Header */}
      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#E6EDF3] mb-1">Mule Leaderboard</h1>
          <p className="text-[#8B949E] text-sm">Real-time ranking of betweenness centrality across the transaction graph.</p>
        </div>
        <div className="flex items-center space-x-3 text-sm">
          <div className="text-[#8B949E] flex items-center">
            {isFetching && <RotateCcw className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
            {isDemo && (
              <span className="mr-3 px-1.5 py-0.5 bg-[#30363D] text-[#8B949E] rounded text-[10px] uppercase font-bold tracking-tight">
                (demo data)
              </span>
            )}
            Updated {secondsAgo} second{secondsAgo !== 1 ? 's' : ''} ago
          </div>
          <button 
            onClick={fetchData}
            disabled={isFetching}
            className="px-3 py-1.5 rounded-[8px] bg-[#161B22] border border-[#30363D] text-[#E6EDF3] hover:bg-[#30363D] transition-colors disabled:opacity-50"
          >
            Refresh Now
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="flex-1 bg-[#161B22] border border-[#30363D] rounded-[8px] overflow-hidden flex flex-col shadow-xl">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left border-collapse">
            <thead className="bg-[#0D1117] sticky top-0 z-10 border-b border-[#30363D]">
              <tr>
                <th className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider w-[80px] text-center">Rank</th>
                <th className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider">Account ID</th>
                
                {/* Custom Tooltip Column Header */}
                <th className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider">
                  <div className="flex items-center space-x-1 cursor-help relative group inline-flex">
                    <span>Centrality Score</span>
                    <Info className="w-3.5 h-3.5 text-[#388ADD]" />
                    
                    {/* Tooltip implementation */}
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-48 bg-[#0D1117] border border-[#30363D] text-[#E6EDF3] p-2 rounded-[4px] text-[11px] normal-case tracking-normal shadow-xl z-20 text-center font-normal leading-relaxed">
                      Accounts sitting on the most transaction paths — classic money mule indicator.
                      <div className="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-[#30363D]"></div>
                      <div className="absolute top-[calc(100%-1px)] left-1/2 -translate-x-1/2 border-[4px] border-transparent border-t-[#0D1117]"></div>
                    </div>
                  </div>
                </th>
                
                <th className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider">Risk Level</th>
                <th className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => {
                const rank = index + 1;
                
                // Row Background Tints
                let rowBgClass = 'bg-[#161B22] hover:bg-[#30363D]/30';
                let rankStyle = {};
                if (rank === 1) {
                  rowBgClass = 'bg-[#FFD700]/5 hover:bg-[#FFD700]/10';
                  rankStyle = { color: '#FFD700', textShadow: '0 0 8px rgba(255,215,0,0.5)' };
                } else if (rank === 2) {
                  rowBgClass = 'bg-[#C0C0C0]/5 hover:bg-[#C0C0C0]/10';
                  rankStyle = { color: '#C0C0C0' };
                } else if (rank === 3) {
                  rowBgClass = 'bg-[#CD7F32]/5 hover:bg-[#CD7F32]/10';
                  rankStyle = { color: '#CD7F32' };
                }

                // Risk Badge Mapping
                const riskPct = Math.round((row.risk || 0) * 100);
                let badgeColor = '#1D9E75';
                let badgeText = 'LOW';
                if (row.risk > 0.7) {
                  badgeColor = '#E24B4A';
                  badgeText = 'HIGH';
                } else if (row.risk >= 0.3) {
                  badgeColor = '#EF9F27';
                  badgeText = 'MEDIUM';
                }

                return (
                  <tr key={row.node_id || row.id} className={`border-b border-[#30363D] transition-colors ${rowBgClass}`}>
                    <td className="px-6 py-4 text-center">
                      <span className="font-['JetBrains_Mono'] font-bold text-lg" style={rankStyle || { color: '#8B949E' }}>
                        #{rank}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-['JetBrains_Mono'] text-[#E6EDF3]">{row.label || row.id}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-['JetBrains_Mono'] text-[#E6EDF3]">
                        {Number(row.centrality || 0).toFixed(4)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span 
                        className="px-2.5 py-1 rounded-[4px] text-[11px] font-bold text-[#E6EDF3] tracking-wide"
                        style={{ backgroundColor: badgeColor }}
                      >
                        {badgeText} ({riskPct}%)
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => handleInspect(row.node_id || row.id)}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-[#388ADD]/10 text-[#388ADD] hover:bg-[#388ADD]/20 border border-[#388ADD]/30 rounded-[4px] text-xs font-medium transition-colors"
                      >
                        <Search className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
              
              {data.length === 0 && !isFetching && (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-[#8B949E]">
                    No centrality data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
