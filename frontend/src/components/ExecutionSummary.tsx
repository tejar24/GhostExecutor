import { TestRunStatus } from '../types';

interface ExecutionSummaryProps {
  status: TestRunStatus | null;
  error: string | null;
}

export function ExecutionSummary({ status, error }: ExecutionSummaryProps) {
  if (error) {
    return (
      <div className="p-4 bg-red-900/20 border border-ghost-red rounded-lg">
        <h3 className="text-ghost-red font-semibold mb-2">Error</h3>
        <p className="text-ghost-text text-sm">{error}</p>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="p-4 bg-ghost-surface border border-ghost-border rounded-lg">
        <p className="text-ghost-text-muted text-sm">
          Click "Run Test" to start execution
        </p>
      </div>
    );
  }

  const getStatusColor = (s: string) => {
    switch (s) {
      case 'passed':
        return 'bg-green-900/20 border-ghost-green text-ghost-green';
      case 'failed':
      case 'error':
        return 'bg-red-900/20 border-ghost-red text-ghost-red';
      case 'running':
      case 'pending':
        return 'bg-blue-900/20 border-ghost-blue text-ghost-blue';
      default:
        return 'bg-ghost-surface border-ghost-border text-ghost-text-muted';
    }
  };

  const progress = status.progress || { total: 0, completed: 0, passed: 0, failed: 0 };
  const isRunning = status.status === 'running' || status.status === 'pending';

  return (
    <div className={`p-4 border rounded-lg ${getStatusColor(status.status)}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold flex items-center gap-2">
          {isRunning && (
            <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
          )}
          Status: {status.status.toUpperCase()}
        </h3>
        {status.current_scenario && isRunning && (
          <span className="text-xs text-ghost-text-muted truncate max-w-[200px]">
            {status.current_scenario.split('/').pop()}
          </span>
        )}
      </div>

      <div className="grid grid-cols-4 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-ghost-green">{progress.passed}</div>
          <div className="text-xs text-ghost-text-muted">Passed</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-ghost-red">{progress.failed}</div>
          <div className="text-xs text-ghost-text-muted">Failed</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-ghost-text">{progress.completed}</div>
          <div className="text-xs text-ghost-text-muted">Completed</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-ghost-text-muted">{progress.total}</div>
          <div className="text-xs text-ghost-text-muted">Total</div>
        </div>
      </div>

      {progress.total > 0 && (
        <div className="mt-3">
          <div className="h-2 bg-ghost-bg rounded-full overflow-hidden">
            <div
              className="h-full bg-ghost-green transition-all duration-300"
              style={{
                width: `${(progress.completed / progress.total) * 100}%`,
              }}
            />
          </div>
        </div>
      )}

      {status.error && (
        <div className="mt-3 p-2 bg-ghost-bg rounded text-sm text-ghost-red">
          {status.error}
        </div>
      )}
    </div>
  );
}
