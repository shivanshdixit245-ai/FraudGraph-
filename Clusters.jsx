import React, { useState, useEffect } from 'react';
import ForceGraph from './ForceGraph';
import useStore from './store';
import { ChevronDown, ChevronUp, AlertOctagon, Clock } from 'lucide-react';
import apiClient from './api/client';

export default function Clusters() {
  const [data, setData] = useState([]);
  const [isFetching, setIsFetching] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'risk', direction: 'desc' });
  
  const addAlert = useStore(state => state.addAlert);

  useEffect(() => {
    const fetchClusters = async () => {
      setIsFetching(true);
      try {
        const res = await apiClient.get('/clusters');
        if (res.data) {
          setData(Array.isArray(res.data.clusters) ? res.data.clusters : []);
        }
      } catch (err) {
        console.warn('Failed to fetch clusters. Using mock data.', err);
        // Fallback Mock Data
        setData([
          {
            id: 'CL-942X',
            memberCount: 14,
            risk: 0.88,
            sharedSignals: ['IP Subnet: 192.168.45.x', 'Device Hash: a8f921'],
            created: new Date(Date.now() - 3600000).toISOString(), // 1 hr ago
            members: ['ACC-101', 'ACC-102', 'ACC-103', 'ACC-104', 'ACC-105'],
            subgraph: {
              nodes: [
                { id: 'ACC-101', risk: 0.9, label: 'ACC-101' },
                { id: 'ACC-102', risk: 0.85, label: 'ACC-102' },
                { id: 'ACC-103', risk: 0.88, label: 'ACC-103' },
                { id: 'ACC-104', risk: 0.92, label: 'ACC-104' },
                { id: 'ACC-105', risk: 0.81, label: 'ACC-105' }
              ],
              edges: [
                { source: 'ACC-101', target: 'ACC-102' },
                { source: 'ACC-101', target: 'ACC-103' },
                { source: 'ACC-102', target: 'ACC-104' },
                { source: 'ACC-103', target: 'ACC-105' },
                { source: 'ACC-104', target: 'ACC-105' }
              ]
            }
          },
          {
            id: 'CL-218Y',
            memberCount: 6,
            risk: 0.65,
            sharedSignals: ['Email Domain: @disposable.com'],
            created: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
            members: ['ACC-201', 'ACC-202', 'ACC-203'],
            subgraph: {
              nodes: [
                { id: 'ACC-201', risk: 0.6, label: 'ACC-201' },
                { id: 'ACC-202', risk: 0.65, label: 'ACC-202' },
                { id: 'ACC-203', risk: 0.7, label: 'ACC-203' }
              ],
              edges: [
                { source: 'ACC-201', target: 'ACC-202' },
                { source: 'ACC-202', target: 'ACC-203' }
              ]
            }
          },
          {
            id: 'CL-005Z',
            memberCount: 42,
            risk: 0.15,
            sharedSignals: ['ASN: AS15169 Google LLC'],
            created: new Date(Date.now() - 172800000).toISOString(),
            members: ['ACC-301', 'ACC-302'],
            subgraph: {
              nodes: [
                { id: 'ACC-301', risk: 0.1, label: 'ACC-301' },
                { id: 'ACC-302', risk: 0.2, label: 'ACC-302' }
              ],
              edges: [
                { source: 'ACC-301', target: 'ACC-302' }
              ]
            }
          }
        ]);
      } finally {
        setIsFetching(false);
      }
    };
    fetchClusters();
  }, []);

  const handleInvestigateAll = (cluster) => {
    if (!cluster.subgraph?.nodes) return;
    
    cluster.subgraph.nodes.forEach(node => {
      const newAlert = {
        id: `alert-cluster-${cluster.id}-${node.id}-${Date.now()}`,
        nodeId: node.id,
        label: node.label || node.id,
        risk: node.risk || cluster.risk,
        topReason: `Cluster ${cluster.id} Member`,
        timestamp: new Date().toISOString(),
        status: 'unreviewed'
      };
      addAlert(newAlert);
    });
    
    // Optional: could show a toast here
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedData = [...data].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
    if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const toggleRow = (id) => {
    setExpandedId(prev => prev === id ? null : id);
  };

  const formatDate = (isoStr) => {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  };

  return (
    <div className="flex flex-col h-full bg-[#0D1117] p-8 overflow-y-auto font-['Inter']">
      
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#E6EDF3] mb-1">Syndicate Clusters</h1>
        <p className="text-[#8B949E] text-sm">Auto-detected macro networks grouped by shared device, network, or behavioral traits.</p>
      </div>

      <div className="flex-1 bg-[#161B22] border border-[#30363D] rounded-[8px] overflow-hidden flex flex-col shadow-xl">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left border-collapse">
            <thead className="bg-[#0D1117] sticky top-0 z-10 border-b border-[#30363D]">
              <tr>
                <th className="px-6 py-4 w-[50px]"></th>
                
                <th 
                  className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider cursor-pointer hover:text-[#E6EDF3] transition-colors group"
                  onClick={() => handleSort('id')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Cluster ID</span>
                    {sortConfig.key === 'id' && (sortConfig.direction === 'asc' ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />)}
                  </div>
                </th>
                
                <th 
                  className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider cursor-pointer hover:text-[#E6EDF3] transition-colors"
                  onClick={() => handleSort('risk')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Risk Level</span>
                    {sortConfig.key === 'risk' && (sortConfig.direction === 'asc' ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />)}
                  </div>
                </th>
                
                <th 
                  className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider cursor-pointer hover:text-[#E6EDF3] transition-colors"
                  onClick={() => handleSort('memberCount')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Members</span>
                    {sortConfig.key === 'memberCount' && (sortConfig.direction === 'asc' ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />)}
                  </div>
                </th>

                <th className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider">Shared Signals</th>
                
                <th 
                  className="px-6 py-4 text-[#8B949E] text-xs uppercase font-semibold tracking-wider cursor-pointer hover:text-[#E6EDF3] transition-colors"
                  onClick={() => handleSort('created')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Detected Time</span>
                    {sortConfig.key === 'created' && (sortConfig.direction === 'asc' ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />)}
                  </div>
                </th>
              </tr>
            </thead>
            
            <tbody>
              {sortedData.map((cluster) => {
                const isExpanded = expandedId === cluster.id;
                
                let badgeColor = '#8B949E';
                let badgeText = 'SAFE';
                if (cluster.risk > 0.8) {
                  badgeColor = '#E24B4A';
                  badgeText = 'HIGH';
                } else if (cluster.risk >= 0.5) {
                  badgeColor = '#EF9F27';
                  badgeText = 'MEDIUM';
                }

                return (
                  <React.Fragment key={cluster.id}>
                    {/* Main Row */}
                    <tr 
                      className={`border-b border-[#30363D] hover:bg-[#30363D]/30 transition-colors cursor-pointer ${isExpanded ? 'bg-[#30363D]/20' : 'bg-[#161B22]'}`}
                      onClick={() => toggleRow(cluster.id)}
                    >
                      <td className="px-6 py-4 text-[#8B949E]">
                        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-['JetBrains_Mono'] text-[#388ADD] font-bold">{cluster.id}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span 
                          className="px-2.5 py-1 rounded-[4px] text-[11px] font-bold text-[#E6EDF3] tracking-wide"
                          style={{ backgroundColor: badgeColor }}
                        >
                          {badgeText} ({Math.round(cluster.risk * 100)}%)
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-['JetBrains_Mono'] text-[#E6EDF3] text-lg">{cluster.memberCount}</span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1.5">
                          {cluster.sharedSignals?.map(sig => (
                            <span key={sig} className="px-2 py-0.5 bg-[#0D1117] border border-[#30363D] text-[#8B949E] text-[11px] rounded-[4px]">
                              {sig}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center text-[#8B949E] text-sm">
                          <Clock className="w-3.5 h-3.5 mr-1.5" />
                          {formatDate(cluster.created)}
                        </div>
                      </td>
                    </tr>

                    {/* Expanded Detail View */}
                    {isExpanded && (
                      <tr className="bg-[#0D1117] border-b border-[#30363D]">
                        <td colSpan="6" className="p-0">
                          <div className="animate-[slideDown_0.3s_ease-out] overflow-hidden">
                            <div className="p-6 grid grid-cols-3 gap-6">
                              
                              {/* Left: Accounts & Attributes */}
                              <div className="col-span-1 flex flex-col space-y-6">
                                
                                <div>
                                  <div className="text-[#E6EDF3] text-sm font-semibold mb-3">Syndicate Members</div>
                                  <div className="flex flex-wrap gap-2">
                                    {cluster.members?.map(memberId => (
                                      <span key={memberId} className="px-2.5 py-1 bg-[#161B22] border border-[#30363D] text-[#E6EDF3] text-xs rounded-full font-['JetBrains_Mono'] shadow-sm">
                                        {memberId}
                                      </span>
                                    ))}
                                    {cluster.memberCount > (cluster.members?.length || 0) && (
                                      <span className="px-2.5 py-1 bg-[#161B22] border border-[#30363D] text-[#8B949E] text-xs rounded-full font-['JetBrains_Mono'] italic">
                                        +{cluster.memberCount - cluster.members.length} more
                                      </span>
                                    )}
                                  </div>
                                </div>

                                <div>
                                  <div className="text-[#E6EDF3] text-sm font-semibold mb-3">Shared Attributes List</div>
                                  <ul className="space-y-2">
                                    {cluster.sharedSignals?.map(sig => (
                                      <li key={sig} className="text-[#8B949E] text-sm flex items-start">
                                        <div className="w-1.5 h-1.5 rounded-full bg-[#388ADD] mt-1.5 mr-2 flex-shrink-0" />
                                        {sig}
                                      </li>
                                    ))}
                                  </ul>
                                </div>

                                <div className="pt-2 mt-auto">
                                  <button 
                                    onClick={() => handleInvestigateAll(cluster)}
                                    className="w-full flex items-center justify-center space-x-2 py-2 bg-[#E24B4A]/10 text-[#E24B4A] hover:bg-[#E24B4A]/20 border border-[#E24B4A]/30 rounded-[8px] text-sm font-medium transition-colors shadow-[0_0_12px_rgba(226,75,74,0.1)]"
                                  >
                                    <AlertOctagon className="w-4 h-4" />
                                    <span>Investigate All Members</span>
                                  </button>
                                  <p className="text-center text-[10px] text-[#8B949E] mt-2">
                                    Adds all nodes to the Alert Queue.
                                  </p>
                                </div>

                              </div>

                              {/* Right: Subgraph Visualization */}
                              <div className="col-span-2 flex flex-col">
                                <div className="text-[#E6EDF3] text-sm font-semibold mb-3">Topological Subgraph</div>
                                <div className="flex-1 bg-[#161B22] border border-[#30363D] rounded-[8px] overflow-hidden min-h-[300px] shadow-inner relative">
                                  {cluster.subgraph?.nodes?.length > 0 ? (
                                    <ForceGraph 
                                      nodes={cluster.subgraph.nodes} 
                                      edges={cluster.subgraph.edges || []} 
                                    />
                                  ) : (
                                    <div className="absolute inset-0 flex items-center justify-center text-[#8B949E]">
                                      No topology data available.
                                    </div>
                                  )}
                                </div>
                              </div>
                              
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
              
              {data.length === 0 && !isFetching && (
                <tr>
                  <td colSpan="6" className="px-6 py-16 text-center">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[#1D9E75]/10 mb-4">
                      <div className="w-4 h-4 rounded-full bg-[#1D9E75] shadow-[0_0_12px_rgba(29,158,117,0.8)]" />
                    </div>
                    <h3 className="text-[#E6EDF3] font-medium text-lg">System Nominal</h3>
                    <p className="text-[#8B949E] text-sm mt-1">No active fraud clusters detected.</p>
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
