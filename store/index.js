import { create } from 'zustand';

export const MOCK_GRAPH = {
  nodes: [
    { id: 0,  label: "ACC-1042", risk: 0.94, degree: 12, centrality: 0.041, cluster_id: 1, x: 320, y: 180 },
    { id: 1,  label: "ACC-1087", risk: 0.88, degree: 9,  centrality: 0.038, cluster_id: 1, x: 420, y: 240 },
    { id: 2,  label: "ACC-1103", risk: 0.79, degree: 7,  centrality: 0.029, cluster_id: 1, x: 280, y: 290 },
    { id: 3,  label: "ACC-1156", risk: 0.61, degree: 5,  centrality: 0.018, cluster_id: 2, x: 500, y: 160 },
    { id: 4,  label: "ACC-1201", risk: 0.55, degree: 4,  centrality: 0.014, cluster_id: 2, x: 560, y: 260 },
    { id: 5,  label: "ACC-1234", risk: 0.18, degree: 3,  centrality: 0.007, cluster_id: null, x: 160, y: 150 },
    { id: 6,  label: "ACC-1298", risk: 0.12, degree: 2,  centrality: 0.004, cluster_id: null, x: 680, y: 180 },
    { id: 7,  label: "ACC-1311", risk: 0.09, degree: 2,  centrality: 0.003, cluster_id: null, x: 200, y: 380 },
    { id: 8,  label: "ACC-1377", risk: 0.83, degree: 8,  centrality: 0.035, cluster_id: 1, x: 370, y: 130 },
    { id: 9,  label: "ACC-1402", risk: 0.22, degree: 3,  centrality: 0.009, cluster_id: null, x: 620, y: 340 },
    { id: 10, label: "ACC-1456", risk: 0.71, degree: 6,  centrality: 0.021, cluster_id: 2, x: 480, y: 310 },
    { id: 11, label: "ACC-1489", risk: 0.14, degree: 2,  centrality: 0.005, cluster_id: null, x: 130, y: 270 },
    { id: 12, label: "ACC-1521", risk: 0.91, degree: 10, centrality: 0.039, cluster_id: 1, x: 340, y: 230 },
    { id: 13, label: "ACC-1563", risk: 0.08, degree: 1,  centrality: 0.002, cluster_id: null, x: 720, y: 280 },
    { id: 14, label: "ACC-1607", risk: 0.44, degree: 4,  centrality: 0.012, cluster_id: 2, x: 540, y: 200 },
    { id: 15, label: "ACC-1644", risk: 0.07, degree: 1,  centrality: 0.002, cluster_id: null, x: 180, y: 450 }
  ],
  edges: [
    { source: 0, target: 1, weight: 0.9, shared_device: true,  shared_ip: true  },
    { source: 0, target: 2, weight: 0.8, shared_device: true,  shared_ip: false },
    { source: 0, target: 8, weight: 0.9, shared_device: true,  shared_ip: true  },
    { source: 0, target: 12,weight: 0.7, shared_device: false, shared_ip: true  },
    { source: 1, target: 2, weight: 0.6, shared_device: true,  shared_ip: false },
    { source: 1, target: 8, weight: 0.8, shared_device: true,  shared_ip: true  },
    { source: 2, target: 12,weight: 0.7, shared_device: false, shared_ip: true  },
    { source: 3, target: 4, weight: 0.5, shared_device: false, shared_ip: true  },
    { source: 3, target: 10,weight: 0.6, shared_device: true,  shared_ip: false },
    { source: 4, target: 14,weight: 0.4, shared_device: false, shared_ip: false },
    { source: 5, target: 0, weight: 0.2, shared_device: false, shared_ip: false },
    { source: 6, target: 3, weight: 0.3, shared_device: false, shared_ip: false },
    { source: 7, target: 2, weight: 0.2, shared_device: false, shared_ip: false },
    { source: 8, target: 12,weight: 0.9, shared_device: true,  shared_ip: true  },
    { source: 9, target: 10,weight: 0.3, shared_device: false, shared_ip: false },
    { source: 11, target: 5,weight: 0.1, shared_device: false, shared_ip: false },
    { source: 13, target: 6,weight: 0.1, shared_device: false, shared_ip: false },
    { source: 14, target: 10,weight:0.5, shared_device: true,  shared_ip: false },
    { source: 15, target: 7,weight: 0.1, shared_device: false, shared_ip: false }
  ]
};

const useStore = create((set) => ({
  nodes: MOCK_GRAPH.nodes,
  edges: MOCK_GRAPH.edges,
  selectedNodeId: null,
  alerts: [],
  wsStatus: 'disconnected',
  replayMode: false,
  replayTimestamp: null,
  isDemo: true,

  setGraph: (nodes, edges) => set({ nodes, edges }),
  
  setIsDemo: (isDemo) => set({ isDemo }),
  
  setSelectedNode: (selectedNodeId) => set({ selectedNodeId }),
  
  addAlert: (alert) => set((state) => ({ 
    alerts: [alert, ...state.alerts] 
  })),
  
  updateAlertStatus: (alertId, status) => set((state) => ({
    alerts: state.alerts.map(a => 
      a.id === alertId ? { ...a, status } : a
    )
  })),
  
  setWsStatus: (wsStatus) => set({ wsStatus }),
  
  setReplayMode: (replayMode, replayTimestamp = null) => set({ 
    replayMode, 
    replayTimestamp 
  }),
}));

export default useStore;
