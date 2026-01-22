interface ExecutionControlsProps {
  isRunning: boolean;
  headless: boolean;
  onHeadlessChange: (headless: boolean) => void;
  onRun: () => void;
  onStop: () => void;
  canRun?: boolean;
  executionMode?: 'local' | 'remote';
  selectedClientName?: string;
}

export function ExecutionControls({
  isRunning,
  headless,
  onHeadlessChange,
  onRun,
  onStop,
  canRun = true,
  executionMode = 'local',
  selectedClientName,
}: ExecutionControlsProps) {
  const isRemote = executionMode === 'remote';
  const runDisabled = isRunning || !canRun;

  const getRunButtonText = () => {
    if (isRunning) {
      return (
        <span className="flex items-center gap-2">
          <span className="w-4 h-4 border-2 border-ghost-text-muted border-t-transparent rounded-full animate-spin" />
          Running...
        </span>
      );
    }
    if (isRemote && selectedClientName) {
      return `Run on ${selectedClientName}`;
    }
    if (isRemote) {
      return 'Select a Client';
    }
    return 'Run Test';
  };

  return (
    <div className="flex items-center gap-4 p-3 bg-ghost-surface rounded-lg border border-ghost-border">
      <button
        onClick={onRun}
        disabled={runDisabled}
        className={`px-4 py-2 font-bold rounded transition-colors ${
          isRemote && canRun
            ? 'bg-ghost-green text-black hover:bg-green-400 disabled:bg-ghost-border disabled:text-ghost-text-muted disabled:cursor-not-allowed'
            : 'bg-ghost-blue text-black hover:bg-blue-400 disabled:bg-ghost-border disabled:text-ghost-text-muted disabled:cursor-not-allowed'
        }`}
      >
        {getRunButtonText()}
      </button>

      <button
        onClick={onStop}
        disabled={!isRunning}
        className="px-4 py-2 bg-ghost-surface text-ghost-text border border-ghost-border font-bold rounded hover:bg-ghost-border disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Stop
      </button>

      <label className="flex items-center gap-2 cursor-pointer ml-auto">
        <input
          type="checkbox"
          checked={!headless}
          onChange={(e) => onHeadlessChange(!e.target.checked)}
          disabled={isRunning}
          className="w-4 h-4 rounded border-ghost-border bg-ghost-bg text-ghost-blue focus:ring-ghost-blue focus:ring-offset-ghost-bg"
        />
        <span className="text-sm text-ghost-text-muted">
          {isRemote ? 'Show Browser (on client)' : 'Headed Mode (Show Browser)'}
        </span>
      </label>

      {isRemote && (
        <div className="flex items-center gap-2 text-sm">
          <span className={`w-2 h-2 rounded-full ${canRun ? 'bg-ghost-green' : 'bg-ghost-text-muted'}`} />
          <span className="text-ghost-text-muted">
            {canRun ? 'Client selected' : 'No client selected'}
          </span>
        </div>
      )}
    </div>
  );
}
