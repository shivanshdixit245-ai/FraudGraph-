import { useEffect, useRef } from 'react';
import useStore, { MOCK_GRAPH } from '../store';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/graph';

export default function useWebSocket() {
  const setWsStatus = useStore((state) => state.setWsStatus);
  const setGraph = useStore((state) => state.setGraph);
  const setIsDemo = useStore((state) => state.setIsDemo);
  const wsStatus = useStore((state) => state.wsStatus);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    let isMounted = true;

    const connect = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      setWsStatus('reconnecting');
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isMounted) {
          setWsStatus('connected');
          setIsDemo(false);
        }
      };

      ws.onmessage = (event) => {
        if (!isMounted) return;
        try {
          const data = JSON.parse(event.data);
          
          if (data.nodes && data.edges) {
            setGraph(data.nodes, data.edges);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        if (!isMounted) return;
        setWsStatus('disconnected');
        setIsDemo(true);
        setGraph(MOCK_GRAPH.nodes, MOCK_GRAPH.edges);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 2000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (isMounted) {
          setIsDemo(true);
          setGraph(MOCK_GRAPH.nodes, MOCK_GRAPH.edges);
        }
        ws.close();
      };
    };

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [setWsStatus, setGraph]);

  return { status: wsStatus };
}
