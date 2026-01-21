import { useState, useEffect } from 'react';

const API_BASE = '/api/v1';

export function StatusIndicator() {
  const [connected, setConnected] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        setConnected(res.ok);
      } catch {
        setConnected(false);
      } finally {
        setChecking(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  if (checking) {
    return (
      <span className="text-xs px-3 py-1 rounded-full bg-ghost-surface text-ghost-text-muted">
        API: Checking...
      </span>
    );
  }

  return (
    <span
      className={`text-xs px-3 py-1 rounded-full ${
        connected
          ? 'bg-green-900/30 text-ghost-green'
          : 'bg-red-900/30 text-ghost-red'
      }`}
    >
      API: {connected ? 'Connected' : 'Disconnected'}
    </span>
  );
}
