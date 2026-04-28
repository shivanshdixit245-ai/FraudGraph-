import React, { useState, useEffect, useRef } from 'react';
import useStore from './store';
import { Play, Pause, SkipBack, Rewind, FastForward, AlertTriangle } from 'lucide-react';
import apiClient from './api/client';

const formatTime = (ms) => {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

export default function ReplayBar() {
  const setGraph = useStore(state => state.setGraph);
  const setReplayMode = useStore(state => state.setReplayMode);

  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [keyframes, setKeyframes] = useState([]);
  const [duration, setDuration] = useState(0);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  
  const [flashAlert, setFlashAlert] = useState(false);
  const flashedNodesRef = useRef(new Set());
  const previousTimeRef = useRef(0);

  // Fetch scenarios on mount
  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const res = await apiClient.get('/replay');
        if (res.data) {
          setScenarios(Array.isArray(res.data.scenarios) ? res.data.scenarios : []);
        }
      } catch (err) {
        console.error('Failed to fetch scenarios:', err);
        setScenarios([
          { event_id: 'case_1', title: 'Account Takeover Cluster', node_count: 142 },
          { event_id: 'case_2', title: 'Velocity Anomaly Series', node_count: 85 }
        ]);
      }
    };
    fetchScenarios();
  }, []);

  const handleSelectScenario = async (e) => {
    const event_id = e.target.value;
    setSelectedScenario(event_id);
    setIsPlaying(false);
    
    if (!event_id) {
      setKeyframes([]);
      setReplayMode(false, null);
      return;
    }

    try {
      const res = await apiClient.get(`/replay/${event_id}`);
      if (res.data) {
        const data = res.data;
        const frames = data.keyframes || [];
        // Conver seconds to ms for frontend player
        const framesWithMs = frames.map(f => ({
          ...f,
          timestamp: f.elapsed_seconds * 1000
        }));
        setKeyframes(framesWithMs);
        setDuration(data.duration_seconds * 1000 || (framesWithMs.length > 0 ? framesWithMs[framesWithMs.length - 1].timestamp : 0));
        setCurrentTime(0);
        flashedNodesRef.current.clear();
        setReplayMode(true, 0);
      }
    } catch (err) {
      console.error('Failed to load replay data:', err);
    }
  };

  // Playback Loop
  useEffect(() => {
    if (!isPlaying || keyframes.length === 0) return;
    
    let lastTime = performance.now();
    let animationFrameId;
    
    const loop = (now) => {
      const delta = now - lastTime;
      lastTime = now;
      
      setCurrentTime(prev => {
        let nextTime = prev + delta * playbackSpeed;
        if (nextTime >= duration) {
          setIsPlaying(false);
          nextTime = duration;
        }
        return nextTime;
      });
      
      animationFrameId = requestAnimationFrame(loop);
    };
    
    animationFrameId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animationFrameId);
  }, [isPlaying, playbackSpeed, keyframes.length, duration]);

  // Graph Interpolation & Flash Logic
  useEffect(() => {
    if (keyframes.length === 0) return;

    // Reset flashes if we scrub backwards
    if (currentTime < previousTimeRef.current) {
      flashedNodesRef.current.clear();
    }
    previousTimeRef.current = currentTime;

    // Find nearest keyframes
    let prevIdx = 0;
    for (let i = 0; i < keyframes.length; i++) {
      if (keyframes[i].timestamp <= currentTime) prevIdx = i;
      else break;
    }
    
    const prevFrame = keyframes[prevIdx];
    const nextFrame = keyframes[prevIdx + 1] || prevFrame;
    
    let interpolatedNodes = prevFrame.nodes;
    const edges = prevFrame.edges;
    
    if (nextFrame !== prevFrame && nextFrame.timestamp > prevFrame.timestamp) {
      const ratio = (currentTime - prevFrame.timestamp) / (nextFrame.timestamp - prevFrame.timestamp);
      interpolatedNodes = prevFrame.nodes.map(n => {
        const nextNode = nextFrame.nodes.find(nx => nx.id === n.id);
        if (!nextNode) return n;
        return {
          ...n,
          // Interpolate risk score smoothly
          risk: n.risk + (nextNode.risk - n.risk) * ratio
        };
      });
    }

    // Flash notification logic
    let crossedThreshold = false;
    interpolatedNodes.forEach(n => {
      if (n.risk > 0.8 && !flashedNodesRef.current.has(n.id)) {
        flashedNodesRef.current.add(n.id);
        crossedThreshold = true;
      }
    });

    if (crossedThreshold) {
      setFlashAlert(true);
      setTimeout(() => setFlashAlert(false), 500);
    }

    // Push state
    setGraph(interpolatedNodes, edges);
    setReplayMode(true, currentTime);

  }, [currentTime, keyframes, setGraph, setReplayMode]);

  return (
    <>
      {/* Global Red Flash Overlay */}
      <div 
        className={`fixed inset-0 pointer-events-none transition-colors duration-500 z-[100] ${
          flashAlert ? 'bg-[#E24B4A]/20' : 'bg-transparent'
        }`} 
      />

      {/* Main Replay Toolbar */}
      <div className="fixed bottom-0 left-[240px] right-[320px] h-[64px] bg-[#161B22] border-t border-[#30363D] flex items-center px-6 z-40 font-['Inter'] shadow-[0_-4px_24px_rgba(0,0,0,0.5)]">
        
        <style>
          {`
            .custom-scrubber::-webkit-slider-thumb {
              -webkit-appearance: none;
              appearance: none;
              width: 14px;
              height: 14px;
              background: #388ADD;
              cursor: pointer;
              transform: rotate(45deg);
              border-radius: 2px;
              box-shadow: 0 0 10px rgba(56, 138, 221, 0.6);
            }
            .custom-scrubber::-moz-range-thumb {
              width: 14px;
              height: 14px;
              background: #388ADD;
              cursor: pointer;
              transform: rotate(45deg);
              border-radius: 2px;
              border: none;
              box-shadow: 0 0 10px rgba(56, 138, 221, 0.6);
            }
          `}
        </style>

        {/* Dropdown */}
        <select 
          value={selectedScenario} 
          onChange={handleSelectScenario}
          className="bg-[#0D1117] border border-[#30363D] text-[#E6EDF3] text-sm rounded-[8px] px-3 py-1.5 focus:outline-none focus:border-[#388ADD] w-[240px] mr-6"
        >
          <option value="">Select Replay Scenario...</option>
          {scenarios.map(s => (
            <option key={s.id || s.event_id} value={s.id || s.event_id}>
              {s.title} ({s.node_count || s.nodes_count || 0} nodes)
            </option>
          ))}
        </select>

        {/* Controls */}
        <div className="flex items-center space-x-3 mr-6">
          <button 
            onClick={() => setCurrentTime(0)}
            className="text-[#8B949E] hover:text-[#E6EDF3] transition-colors"
            title="Reset"
          >
            <SkipBack className="w-5 h-5" />
          </button>
          
          <button 
            onClick={() => setCurrentTime(prev => Math.max(0, prev - 10000))}
            className="text-[#8B949E] hover:text-[#E6EDF3] transition-colors"
            title="-10s"
          >
            <Rewind className="w-5 h-5" />
          </button>

          <button 
            onClick={() => setIsPlaying(!isPlaying)}
            disabled={!selectedScenario || duration === 0}
            className="w-10 h-10 rounded-full bg-[#388ADD] text-[#E6EDF3] flex items-center justify-center hover:bg-[#2A6BAA] transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_12px_rgba(56,138,221,0.4)]"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>

          <button 
            onClick={() => setCurrentTime(prev => Math.min(duration, prev + 10000))}
            className="text-[#8B949E] hover:text-[#E6EDF3] transition-colors"
            title="+10s"
          >
            <FastForward className="w-5 h-5" />
          </button>
        </div>

        {/* Scrubber & Time */}
        <div className="flex-1 flex items-center space-x-4">
          <span className="font-['JetBrains_Mono'] text-sm text-[#8B949E] w-[70px] text-right">
            {formatTime(currentTime)}
          </span>
          
          <input 
            type="range" 
            min="0" 
            max={duration || 100} 
            value={currentTime} 
            onChange={(e) => {
              setIsPlaying(false);
              setCurrentTime(Number(e.target.value));
            }}
            disabled={!selectedScenario}
            className="flex-1 h-1.5 bg-[#30363D] rounded-full appearance-none outline-none custom-scrubber disabled:opacity-50"
          />
          
          <span className="font-['JetBrains_Mono'] text-sm text-[#8B949E] w-[70px]">
            {formatTime(duration)}
          </span>
        </div>

        {/* Speed Selector */}
        <div className="flex space-x-1 ml-6">
          {[1, 2, 5].map(speed => (
            <button 
              key={speed}
              onClick={() => setPlaybackSpeed(speed)}
              className={`px-3 py-1 rounded-[20px] text-xs font-bold transition-colors ${
                playbackSpeed === speed 
                  ? 'bg-[#388ADD] text-[#E6EDF3] shadow-[0_0_8px_rgba(56,138,221,0.3)]' 
                  : 'bg-[#0D1117] text-[#8B949E] border border-[#30363D] hover:text-[#E6EDF3]'
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
        
      </div>
    </>
  );
}
