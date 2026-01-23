import { useState, useCallback } from 'react';
import { StatusIndicator } from './components/StatusIndicator';
import { FeatureEditor } from './components/FeatureEditor';
import { ExecutionControls } from './components/ExecutionControls';
import { LogConsole } from './components/LogConsole';
import { ExecutionSummary } from './components/ExecutionSummary';
import { FeatureList } from './components/FeatureList';
import { RemoteClientsPanel } from './components/RemoteClientsPanel';
import { useTestExecution } from './hooks/useTestExecution';
import { useSSEStream } from './hooks/useSSEStream';
import { useRemoteClients } from './hooks/useRemoteClients';

type ExecutionMode = 'local' | 'remote';

function App() {
  const [featureContent, setFeatureContent] = useState('');
  const [headless, setHeadless] = useState(false);
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('local');

  // Local execution hooks
  const { runId, status, isRunning: isLocalRunning, error: localError, startTest, stopTest } = useTestExecution();
  const { logs, isConnected, clearLogs } = useSSEStream(runId);

  // Remote execution hooks
  const {
    clients,
    isLoading: isLoadingClients,
    error: remoteError,
    selectedClient,
    runStatus,
    isRunning: isRemoteRunning,
    logs: remoteLogs,
    isStreaming: isRemoteStreaming,
    selectClient,
    refreshClients,
    runTest: runRemoteTest,
    stopTest: stopRemoteTest,
    clearLogs: clearRemoteLogs,
  } = useRemoteClients();

  const isRunning = executionMode === 'local' ? isLocalRunning : isRemoteRunning;
  const error = executionMode === 'local' ? localError : remoteError;

  const handleRun = useCallback(() => {
    if (executionMode === 'local') {
      clearLogs();
      startTest(featureContent, headless);
    } else {
      runRemoteTest(featureContent, headless);
    }
  }, [executionMode, featureContent, headless, startTest, clearLogs, runRemoteTest]);

  const handleStop = useCallback(() => {
    if (executionMode === 'local') {
      stopTest();
    } else {
      stopRemoteTest();
    }
  }, [executionMode, stopTest, stopRemoteTest]);

  const handleFeatureSelect = useCallback((content: string) => {
    setFeatureContent(content);
  }, []);

  const canRun = executionMode === 'local' || selectedClient !== null;

  return (
    <div className="min-h-screen bg-ghost-bg text-ghost-text p-4">
      <div className="max-w-[1600px] mx-auto">
        {/* Header */}
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-ghost-blue">
            Ghost-QC Test Runner
          </h1>
          <StatusIndicator />
        </header>

        {/* Execution Mode Tabs */}
        <div className="flex gap-1 mb-6 bg-ghost-surface rounded-lg p-1 w-fit">
          <button
            onClick={() => setExecutionMode('local')}
            className={`px-4 py-2 rounded-md font-medium transition-colors ${
              executionMode === 'local'
                ? 'bg-ghost-blue text-black'
                : 'text-ghost-text-muted hover:text-ghost-text hover:bg-ghost-bg'
            }`}
          >
            Local Execution
          </button>
          <button
            onClick={() => setExecutionMode('remote')}
            className={`px-4 py-2 rounded-md font-medium transition-colors flex items-center gap-2 ${
              executionMode === 'remote'
                ? 'bg-ghost-blue text-black'
                : 'text-ghost-text-muted hover:text-ghost-text hover:bg-ghost-bg'
            }`}
          >
            Remote Execution
            {clients.length > 0 && (
              <span className={`px-2 py-0.5 text-xs rounded-full ${
                executionMode === 'remote'
                  ? 'bg-black/20 text-black'
                  : 'bg-ghost-green/20 text-ghost-green'
              }`}>
                {clients.length}
              </span>
            )}
          </button>
        </div>

        {/* Main Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="flex flex-col gap-4">
            {/* Feature Editor */}
            <div className="bg-ghost-surface rounded-lg border border-ghost-border p-4 h-[400px]">
              <FeatureEditor
                value={featureContent}
                onChange={setFeatureContent}
                disabled={isRunning}
              />
            </div>

            {/* Execution Controls */}
            <ExecutionControls
              isRunning={isRunning}
              headless={headless}
              onHeadlessChange={setHeadless}
              onRun={handleRun}
              onStop={handleStop}
              canRun={canRun}
              executionMode={executionMode}
              selectedClientName={selectedClient?.client_name}
            />

            {/* Saved Features */}
            <div className="bg-ghost-surface rounded-lg border border-ghost-border p-4 h-[200px]">
              <FeatureList onSelect={handleFeatureSelect} />
            </div>
          </div>

          {/* Right Column */}
          <div className="flex flex-col gap-4">
            {executionMode === 'local' ? (
              <>
                {/* Execution Summary */}
                <ExecutionSummary status={status} error={error} />

                {/* Log Console */}
                <div className="bg-ghost-surface rounded-lg border border-ghost-border p-4 flex-1 min-h-[500px]">
                  <LogConsole
                    logs={logs}
                    isStreaming={isConnected}
                    onClear={clearLogs}
                  />
                </div>
              </>
            ) : (
              <>
                {/* Remote Clients Panel */}
                <div className="bg-ghost-surface rounded-lg border border-ghost-border p-4">
                  <RemoteClientsPanel
                    clients={clients}
                    isLoading={isLoadingClients}
                    selectedClient={selectedClient}
                    runStatus={runStatus}
                    isRunning={isRemoteRunning}
                    onSelectClient={selectClient}
                    onRefresh={refreshClients}
                  />
                </div>

                {/* Remote Log Console */}
                {selectedClient && (
                  <div className="bg-ghost-surface rounded-lg border border-ghost-border p-4 flex-1 min-h-[400px]">
                    <LogConsole
                      logs={remoteLogs}
                      isStreaming={isRemoteStreaming}
                      onClear={clearRemoteLogs}
                    />
                  </div>
                )}

                {/* Remote execution info/instructions */}
                {!selectedClient && (
                  <div className="bg-ghost-surface rounded-lg border border-ghost-border p-6">
                    <h3 className="text-lg font-semibold text-ghost-text mb-4">
                      How to Connect a Remote Client
                    </h3>
                    <div className="space-y-4 text-sm">
                      <div className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-ghost-blue/20 text-ghost-blue flex items-center justify-center text-xs font-bold">1</span>
                        <div>
                          <p className="text-ghost-text">Install required packages on your local machine:</p>
                          <code className="block mt-1 p-2 bg-ghost-bg rounded text-ghost-blue">
                            pip install websockets playwright
                          </code>
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-ghost-blue/20 text-ghost-blue flex items-center justify-center text-xs font-bold">2</span>
                        <div>
                          <p className="text-ghost-text">Run the client to connect:</p>
                          <code className="block mt-1 p-2 bg-ghost-bg rounded text-ghost-blue break-all">
                            python -m client.cli --server ws://{window.location.host}/api/v1/remote/ws
                          </code>
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-ghost-blue/20 text-ghost-blue flex items-center justify-center text-xs font-bold">3</span>
                        <div>
                          <p className="text-ghost-text">
                            Once connected, select the client above and click "Run Test"
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Show error if any */}
                {remoteError && (
                  <div className="bg-ghost-red/10 border border-ghost-red rounded-lg p-4">
                    <p className="text-ghost-red">{remoteError}</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
