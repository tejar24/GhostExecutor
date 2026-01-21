import { useState, useEffect, useCallback, useRef } from 'react';
import { LogEntry, SSEEvent } from '../types';


interface UseSSEStreamReturn {
  logs: LogEntry[];
  isConnected: boolean;
  clearLogs: () => void;
}

/**
 * Type guards for SSE event data
 */
function isScenarioStart(
  event: SSEEvent
): event is SSEEvent & { data: { scenario_name: string } } {
  return event.type === 'scenario_start';
}

function isScenarioEnd(
  event: SSEEvent
): event is SSEEvent & {
  data: {
    scenario_name: string;
    passed_steps: number;
    failed_steps: number;
    duration_ms: number;
  };
} {
  return event.type === 'scenario_end';
}

function isStepStart(
  event: SSEEvent
): event is SSEEvent & {
  data: { step_text: string; action_type: string };
} {
  return event.type === 'step_start';
}

function isStepResult(
  event: SSEEvent
): event is SSEEvent & {
  data: {
    step_text: string;
    success: boolean;
    duration_ms: number;
    error?: string;
  };
} {
  return event.type === 'step_result';
}

function isHealingEvent(
  event: SSEEvent
): event is SSEEvent & {
  data: {
    method: string;
    tried_selector: string;
    success: boolean;
  };
} {
  return event.type === 'healing';
}

export function useSSEStream(runId: string | null): UseSSEStreamReturn {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const logIdCounter = useRef(0);

  const addLog = useCallback((entry: Omit<LogEntry, 'id'>) => {
    const id = `log-${logIdCounter.current++}`;
    setLogs((prev) => [...prev, { ...entry, id }]);
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
    logIdCounter.current = 0;
  }, []);

  useEffect(() => {
    if (!runId) {
      eventSourceRef.current?.close();
      eventSourceRef.current = null;
      setIsConnected(false);
      return;
    }

    eventSourceRef.current?.close();

    const url = `/api/v1/tests/${runId}/stream`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      addLog({
        timestamp: new Date().toISOString(),
        type: 'info',
        message: 'Connected to log stream',
      });
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      addLog({
        timestamp: new Date().toISOString(),
        type: 'error',
        message: 'Stream connection lost',
      });
    };

    eventSource.addEventListener('scenario_start', (e: MessageEvent) => {
      const event: SSEEvent = JSON.parse(e.data);
      if (!isScenarioStart(event)) return;

      addLog({
        timestamp: event.timestamp,
        type: 'scenario_start',
        message: `Starting scenario: ${event.data.scenario_name}`,
      });
    });

    eventSource.addEventListener('scenario_end', (e: MessageEvent) => {
      const event: SSEEvent = JSON.parse(e.data);
      if (!isScenarioEnd(event)) return;

      const { scenario_name, passed_steps, failed_steps, duration_ms } =
        event.data;
      const status = failed_steps === 0 ? 'PASS' : 'FAIL';

      addLog({
        timestamp: event.timestamp,
        type: 'scenario_end',
        message: `Scenario "${scenario_name}" ${status} (${passed_steps}/${passed_steps + failed_steps} steps, ${duration_ms.toFixed(
          0
        )}ms)`,
        success: failed_steps === 0,
        duration_ms,
      });
    });

    eventSource.addEventListener('step_start', (e: MessageEvent) => {
      const event: SSEEvent = JSON.parse(e.data);
      if (!isStepStart(event)) return;

      addLog({
        timestamp: event.timestamp,
        type: 'step_start',
        message: `STEP: ${event.data.step_text}`,
      });
    });

    eventSource.addEventListener('step_result', (e: MessageEvent) => {
      const event: SSEEvent = JSON.parse(e.data);
      if (!isStepResult(event)) return;

      const { success, duration_ms, error } = event.data;

      addLog({
        timestamp: event.timestamp,
        type: 'step_result',
        message: `${success ? 'PASS' : 'FAIL'} (${duration_ms.toFixed(
          0
        )}ms)${error ? ` - ${error}` : ''}`,
        success,
        duration_ms,
      });
    });

    eventSource.addEventListener('healing', (e: MessageEvent) => {
      const event: SSEEvent = JSON.parse(e.data);
      if (!isHealingEvent(event)) return;

      const { method, tried_selector, success } = event.data;

      addLog({
        timestamp: event.timestamp,
        type: 'healing',
        message: `[HEAL] ${method}: ${tried_selector.slice(
          0,
          50
        )}... -> ${success ? 'SUCCESS' : 'FAILED'}`,
        success,
      });
    });
    function isRunComplete(
  event: SSEEvent
): event is SSEEvent & { data: { status: 'passed' | 'failed' | string } } {
  return event.type === 'run_complete';
}

eventSource.addEventListener('run_complete', (e: MessageEvent) => {
  const event: SSEEvent = JSON.parse(e.data);
  if (!isRunComplete(event)) return;

  addLog({
    timestamp: event.timestamp,
    type: 'info',
    message: `Test run completed: ${event.data.status.toUpperCase()}`,
    success: event.data.status === 'passed',
  });

  eventSource.close();
  setIsConnected(false);
});

  }, [runId, addLog]);

  return { logs, isConnected, clearLogs };
}
