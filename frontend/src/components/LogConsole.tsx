import { useEffect, useRef, useState } from 'react';
import { LogEntry } from '../types';

interface LogConsoleProps {
  logs: LogEntry[];
  isStreaming: boolean;
  onClear: () => void;
}

export function LogConsole({ logs, isStreaming, onClear }: LogConsoleProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Detect if user scrolled up (disable auto-scroll)
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    setAutoScroll(isAtBottom);
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', { hour12: false });
    } catch {
      return '';
    }
  };

  const getLogColor = (entry: LogEntry) => {
    if (entry.type === 'step_result') {
      return entry.success ? 'text-ghost-green' : 'text-ghost-red';
    }
    if (entry.type === 'scenario_end') {
      return entry.success ? 'text-ghost-green' : 'text-ghost-red';
    }
    if (entry.type === 'healing') {
      return entry.success ? 'text-ghost-yellow' : 'text-ghost-text-muted';
    }
    if (entry.type === 'error') {
      return 'text-ghost-red';
    }
    if (entry.type === 'scenario_start') {
      return 'text-ghost-blue';
    }
    return 'text-ghost-text';
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-ghost-blue font-semibold flex items-center gap-2">
          Live Log Console
          {isStreaming && (
            <span className="flex items-center gap-1 text-xs text-ghost-green">
              <span className="w-2 h-2 bg-ghost-green rounded-full animate-pulse" />
              STREAMING
            </span>
          )}
        </h2>
        <div className="flex items-center gap-2">
          {!autoScroll && (
            <button
              onClick={() => {
                setAutoScroll(true);
                if (containerRef.current) {
                  containerRef.current.scrollTop = containerRef.current.scrollHeight;
                }
              }}
              className="text-xs px-2 py-1 bg-ghost-blue/20 text-ghost-blue rounded hover:bg-ghost-blue/30"
            >
              Scroll to Bottom
            </button>
          )}
          <button
            onClick={onClear}
            className="text-xs px-2 py-1 bg-ghost-surface text-ghost-text-muted hover:text-ghost-text rounded"
          >
            Clear
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 bg-ghost-bg rounded-lg border border-ghost-border overflow-y-auto font-mono text-sm"
      >
        {logs.length === 0 ? (
          <div className="p-4 text-ghost-text-muted">
            Logs will appear here when test execution starts...
          </div>
        ) : (
          <div className="p-3 space-y-1">
            {logs.map((entry) => (
              <div key={entry.id} className={`${getLogColor(entry)} leading-relaxed`}>
                <span className="text-ghost-text-muted mr-2">
                  [{formatTimestamp(entry.timestamp)}]
                </span>
                {entry.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
