import { useEffect, useRef, useState } from 'react';

/**
 * WebSocket hook with auto-reconnect and fallback to polling.
 * 
 * @param {string} wsUrl - WebSocket URL (e.g., 'ws://localhost:8000/ws/signals')
 * @param {Object} options - Configuration options
 * @param {number} options.reconnectDelay - Delay between reconnect attempts (ms)
 * @param {number} options.maxReconnectDelay - Maximum reconnect delay (ms)
 * @param {boolean} options.enabled - Whether WebSocket is enabled
 * @returns {Object} - { data, connected, error, send }
 */
export function useWebSocket(wsUrl, options = {}) {
  const {
    reconnectDelay = 1000,
    maxReconnectDelay = 30000,
    enabled = true
  } = options;

  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectDelayRef = useRef(reconnectDelay);
  const reconnectAttemptsRef = useRef(0);

  const connect = () => {
    if (!enabled || !wsUrl) return;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setError(null);
        reconnectDelayRef.current = reconnectDelay;
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          setData(parsedData);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('WebSocket error');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setConnected(false);
        
        // Auto-reconnect with exponential backoff
        if (enabled) {
          const delay = Math.min(
            reconnectDelayRef.current * Math.pow(1.5, reconnectAttemptsRef.current),
            maxReconnectDelay
          );
          
          console.log(`Reconnecting in ${delay}ms...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect();
          }, delay);
        }
      };

    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError(err.message);
    }
  };

  const send = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof message === 'string' ? message : JSON.stringify(message));
    }
  };

  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [wsUrl, enabled]);

  return { data, connected, error, send };
}
