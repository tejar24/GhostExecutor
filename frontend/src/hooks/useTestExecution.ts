import { useState, useCallback, useRef } from 'react';
import { TestRunStatus } from '../types';

const API_BASE = '/api/v1';

interface UseTestExecutionReturn {
  runId: string | null;
  status: TestRunStatus | null;
  isRunning: boolean;
  error: string | null;
  startTest: (content: string, headless: boolean) => Promise<void>;
  stopTest: () => Promise<void>;
}

export function useTestExecution(): UseTestExecutionReturn {
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<TestRunStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollIntervalRef = useRef<number | null>(null);

  const pollStatus = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/tests/${id}`);
      if (!res.ok) throw new Error('Failed to fetch status');

      const data: TestRunStatus = await res.json();
      setStatus(data);

      // Stop polling if test is complete
      if (data.status !== 'pending' && data.status !== 'running') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsRunning(false);
      }
    } catch (e) {
      console.error('Poll error:', e);
    }
  }, []);

  const startTest = useCallback(async (content: string, headless: boolean) => {
    setError(null);
    setStatus(null);

    // Generate a unique temp filename for this test run
    const tempFilename = `temp_test_${Date.now()}.feature`;

    // First, save the feature content to a temp file
    try {
      const saveRes = await fetch(`${API_BASE}/features/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: tempFilename, content }),
      });

      if (!saveRes.ok) {
        throw new Error('Failed to save feature content');
      }
    } catch (e) {
      setError(`Failed to save feature: ${e instanceof Error ? e.message : 'Unknown error'}`);
      return;
    }

    // Now start the test with the temp feature file
    try {
      const res = await fetch(`${API_BASE}/tests/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feature_files: [`features/${tempFilename}`],
          headless,
          stop_on_failure: false,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start test');
      }

      const data = await res.json();
      setRunId(data.run_id);
      setIsRunning(true);

      // Start polling for status
      pollIntervalRef.current = window.setInterval(() => {
        pollStatus(data.run_id);
      }, 2000);

      // Initial poll
      await pollStatus(data.run_id);

    } catch (e) {
      setError(`Failed to start test: ${e instanceof Error ? e.message : 'Unknown error'}`);
      setIsRunning(false);
    }
  }, [pollStatus]);

  const stopTest = useCallback(async () => {
    if (!runId) return;

    try {
      const res = await fetch(`${API_BASE}/tests/${runId}`, {
        method: 'DELETE',
      });

      if (!res.ok) {
        throw new Error('Failed to stop test');
      }

      // Stop polling
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }

      setIsRunning(false);
      setStatus((prev) => prev ? { ...prev, status: 'skipped' } : null);

    } catch (e) {
      setError(`Failed to stop test: ${e instanceof Error ? e.message : 'Unknown error'}`);
    }
  }, [runId]);

  return {
    runId,
    status,
    isRunning,
    error,
    startTest,
    stopTest,
  };
}
