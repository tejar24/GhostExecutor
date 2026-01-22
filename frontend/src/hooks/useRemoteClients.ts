import { useState, useEffect, useCallback, useRef } from 'react';
import { RemoteClient, RemoteRunStatus } from '../types';

const API_BASE = '/api/v1';

interface UseRemoteClientsReturn {
  clients: RemoteClient[];
  isLoading: boolean;
  error: string | null;
  selectedClient: RemoteClient | null;
  runStatus: RemoteRunStatus | null;
  isRunning: boolean;
  selectClient: (client: RemoteClient | null) => void;
  refreshClients: () => Promise<void>;
  runTest: (featureContent: string, headless: boolean) => Promise<void>;
  stopTest: () => Promise<void>;
}

export function useRemoteClients(): UseRemoteClientsReturn {
  const [clients, setClients] = useState<RemoteClient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClient, setSelectedClient] = useState<RemoteClient | null>(null);
  const [runStatus, setRunStatus] = useState<RemoteRunStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);

  const pollIntervalRef = useRef<number | null>(null);

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

      // Start polling for status
      pollIntervalRef.current = window.setInterval(() => {
        pollRunStatus(data.run_id);
      }, 2000);

      // Initial poll
      pollRunStatus(data.run_id);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setIsRunning(false);
    }
  }, [selectedClient, pollRunStatus]);

  // Stop running test
  const stopTest = useCallback(async () => {
    if (!currentRunId) return;

    try {
      await fetch(`${API_BASE}/remote/run/${currentRunId}`, {
        method: 'DELETE',
      });
      setIsRunning(false);
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    } catch (err) {
      console.error('Error stopping test:', err);
    }
  }, [currentRunId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
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
    selectClient,
    refreshClients,
    runTest,
    stopTest,
  };
}
