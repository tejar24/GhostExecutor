import { useState, useEffect, useCallback, useRef } from 'react';
import { RemoteClient, RemoteRunStatus, LogEntry } from '../types';

const API_BASE = '/api/v1';

interface UseRemoteClientsReturn {
  clients: RemoteClient[];
  isLoading: boolean;
  error: string | null;
  selectedClient: RemoteClient | null;
  runStatus: RemoteRunStatus | null;
  isRunning: boolean;
  logs: LogEntry[];
  isStreaming: boolean;
  selectClient: (client: RemoteClient | null) => void;
  refreshClients: () => Promise<void>;
  runTest: (featureContent: string, headless: boolean) => Promise<void>;
  stopTest: () => Promise<void>;
  clearLogs: () => void;
}

export function useRemoteClients(): UseRemoteClientsReturn {
  const [clients, setClients] = useState<RemoteClient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClient, setSelectedClient] = useState<RemoteClient | null>(null);
  const [runStatus, setRunStatus] = useState<RemoteRunStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const pollIntervalRef = useRef<number | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const logIdCounter = useRef(0);

  // Clear logs
  const clearLogs = useCallback(() => {
    setLogs([]);
    logIdCounter.current = 0;
  }, []);

  // Add log entry
  const addLog = useCallback((type: LogEntry['type'], message: string, success?: boolean, duration_ms?: number) => {
    const entry: LogEntry = {
      id: `log-${logIdCounter.current++}`,
      timestamp: new Date().toISOString(),
      type,
      message,
      success,
      duration_ms,
    };
    setLogs(prev => [...prev, entry]);
  }, []);

  // Connect to SSE stream
  const connectToStream = useCallback((runId: string) => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`${API_BASE}/remote/run/${runId}/stream`);
    eventSourceRef.current = eventSource;
    setIsStreaming(true);

    eventSource.onopen = () => {
      addLog('info', 'Connected to remote execution stream');
    };

    eventSource.addEventListener('browser_starting', () => {
      addLog('info', 'Starting browser on remote client...');
    });

    eventSource.addEventListener('browser_started', () => {
      addLog('info', 'Browser started successfully');
    });

    eventSource.addEventListener('browser_stopped', () => {
      addLog('info', 'Browser stopped');
    });

    eventSource.addEventListener('feature_started', (e) => {
      const data = JSON.parse(e.data);
      addLog('info', `Running feature: ${data.data?.feature_name || 'Unknown'}`);
    });

    eventSource.addEventListener('scenario_started', (e) => {
      const data = JSON.parse(e.data);
      addLog('scenario_start', `Scenario: ${data.data?.scenario_name || 'Unknown'}`);
    });

    eventSource.addEventListener('scenario_completed', (e) => {
      const data = JSON.parse(e.data);
      const status = data.data?.status || 'unknown';
      addLog('scenario_end', `Scenario ${status}: ${data.data?.scenario_name || 'Unknown'}`, status === 'passed');
    });

    eventSource.addEventListener('step_started', (e) => {
      const data = JSON.parse(e.data);
      addLog('step_start', `${data.data?.step || 'Unknown step'}`);
    });

    eventSource.addEventListener('step_completed', (e) => {
      const data = JSON.parse(e.data);
      const success = data.data?.status === 'passed';
      const message = success
        ? `PASSED: ${data.data?.step || 'Unknown'}`
        : `FAILED: ${data.data?.step || 'Unknown'} - ${data.data?.error || ''}`;
      addLog('step_result', message, success, data.data?.duration_ms);
    });

    eventSource.addEventListener('run_started', () => {
      addLog('info', 'Test run started');
    });

    eventSource.addEventListener('run_completed', (e) => {
      const data = JSON.parse(e.data);
      const status = data.data?.result?.status || 'completed';
      addLog('info', `Test run ${status}`);
      setIsStreaming(false);
      eventSource.close();
    });

    eventSource.addEventListener('keepalive', () => {
      // Ignore keepalive events
    });

    eventSource.onerror = () => {
      setIsStreaming(false);
      eventSource.close();
    };
  }, [addLog]);

  // Fetch clients list
  const refreshClients = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE}/remote/clients`);
      if (!response.ok) {
        throw new Error('Failed to fetch clients');
      }
      const data = await response.json();
      setClients(data.clients || []);
      setError(null);

      // Update selected client if it's in the list
      if (selectedClient) {
        const updated = data.clients.find(
          (c: RemoteClient) => c.session_id === selectedClient.session_id
        );
        if (updated) {
          setSelectedClient(updated);
        } else {
          // Client disconnected
          setSelectedClient(null);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [selectedClient]);

  // Poll for clients every 5 seconds
  useEffect(() => {
    refreshClients();
    const interval = setInterval(refreshClients, 5000);
    return () => clearInterval(interval);
  }, [refreshClients]);

  // Select a client
  const selectClient = useCallback((client: RemoteClient | null) => {
    setSelectedClient(client);
    setRunStatus(null);
    setCurrentRunId(null);
  }, []);

  // Poll for run status
  const pollRunStatus = useCallback(async (runId: string) => {
    try {
      const response = await fetch(`${API_BASE}/remote/run/${runId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch run status');
      }
      const data = await response.json();
      setRunStatus(data);

      // Stop polling if completed
      if (data.status === 'passed' || data.status === 'failed' ||
          data.status === 'error' || data.status === 'cancelled') {
        setIsRunning(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }
    } catch (err) {
      console.error('Error polling run status:', err);
    }
  }, []);

  // Run test on selected client
  const runTest = useCallback(async (featureContent: string, headless: boolean) => {
    if (!selectedClient) {
      setError('No client selected');
      return;
    }

    try {
      setIsRunning(true);
      setError(null);
      setRunStatus(null);
      clearLogs();

      addLog('info', `Starting test on ${selectedClient.client_name}...`);

      const response = await fetch(`${API_BASE}/remote/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: selectedClient.session_id,
          feature_content: featureContent,
          headless: headless,
          slow_mo: 100,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start test');
      }

      const data = await response.json();
      setCurrentRunId(data.run_id);

      // Connect to SSE stream for live logs
      connectToStream(data.run_id);

      // Start polling for status
      pollIntervalRef.current = window.setInterval(() => {
        pollRunStatus(data.run_id);
      }, 2000);

      // Initial poll
      pollRunStatus(data.run_id);

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      addLog('error', `Error: ${errorMsg}`);
      setIsRunning(false);
    }
  }, [selectedClient, pollRunStatus, clearLogs, addLog, connectToStream]);

  // Stop running test
  const stopTest = useCallback(async () => {
    if (!currentRunId) return;

    try {
      await fetch(`${API_BASE}/remote/run/${currentRunId}`, {
        method: 'DELETE',
      });
      setIsRunning(false);
      addLog('info', 'Test cancelled');
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        setIsStreaming(false);
      }
    } catch (err) {
      console.error('Error stopping test:', err);
    }
  }, [currentRunId, addLog]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return {
    clients,
    isLoading,
    error,
    selectedClient,
    runStatus,
    isRunning,
    logs,
    isStreaming,
    selectClient,
    refreshClients,
    runTest,
    stopTest,
    clearLogs,
  };
}
