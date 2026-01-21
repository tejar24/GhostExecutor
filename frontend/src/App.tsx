import { useState, useCallback } from 'react';
import { StatusIndicator } from './components/StatusIndicator';
import { FeatureEditor } from './components/FeatureEditor';
import { ExecutionControls } from './components/ExecutionControls';
import { LogConsole } from './components/LogConsole';
import { ExecutionSummary } from './components/ExecutionSummary';
import { FeatureList } from './components/FeatureList';
import { useTestExecution } from './hooks/useTestExecution';
import { useSSEStream } from './hooks/useSSEStream';

function App() {
  const [featureContent, setFeatureContent] = useState('');
  const [headless, setHeadless] = useState(false);

  const { runId, status, isRunning, error, startTest, stopTest } = useTestExecution();
  const { logs, isConnected, clearLogs } = useSSEStream(runId);

  const handleRun = useCallback(() => {
    clearLogs();
    startTest(featureContent, headless);
  }, [featureContent, headless, startTest, clearLogs]);

  const handleFeatureSelect = useCallback((content: string) => {
    setFeatureContent(content);
  }, []);

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
              onStop={stopTest}
            />

            {/* Saved Features */}
            <div className="bg-ghost-surface rounded-lg border border-ghost-border p-4 h-[200px]">
              <FeatureList onSelect={handleFeatureSelect} />
            </div>
          </div>

          {/* Right Column */}
          <div className="flex flex-col gap-4">
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
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
