import { RemoteClient, RemoteRunStatus } from '../types';

interface RemoteClientsPanelProps {
  clients: RemoteClient[];
  isLoading: boolean;
  selectedClient: RemoteClient | null;
  runStatus: RemoteRunStatus | null;
  isRunning: boolean;
  onSelectClient: (client: RemoteClient | null) => void;
  onRefresh: () => void;
}

export function RemoteClientsPanel({
  clients,
  isLoading,
  selectedClient,
  runStatus,
  isRunning,
  onSelectClient,
  onRefresh,
}: RemoteClientsPanelProps) {
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'text-ghost-green';
      case 'busy':
        return 'text-ghost-yellow';
      case 'disconnected':
        return 'text-ghost-red';
      default:
        return 'text-ghost-text-muted';
    }
  };

  const getStatusDot = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-ghost-green';
      case 'busy':
        return 'bg-ghost-yellow animate-pulse';
      case 'disconnected':
        return 'bg-ghost-red';
      default:
        return 'bg-ghost-text-muted';
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Header with refresh button */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-ghost-text">Remote Clients</h3>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="px-3 py-1 text-sm bg-ghost-surface border border-ghost-border rounded hover:bg-ghost-border transition-colors disabled:opacity-50"
        >
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Client list */}
      <div className="bg-ghost-surface rounded-lg border border-ghost-border overflow-hidden">
        {clients.length === 0 ? (
          <div className="p-8 text-center text-ghost-text-muted">
            <div className="text-4xl mb-4">🖥️</div>
            <p className="mb-2">No remote clients connected</p>
            <p className="text-sm">
              Run the client on your local machine to connect:
            </p>
            <code className="block mt-2 p-2 bg-ghost-bg rounded text-sm text-ghost-blue">
              python -m client.cli --server ws://SERVER:8000/api/v1/remote/ws
            </code>
          </div>
        ) : (
          <div className="divide-y divide-ghost-border">
            {clients.map((client) => (
              <div
                key={client.session_id}
                onClick={() => onSelectClient(
                  selectedClient?.session_id === client.session_id ? null : client
                )}
                className={`p-4 cursor-pointer transition-colors ${
                  selectedClient?.session_id === client.session_id
                    ? 'bg-ghost-blue/10 border-l-2 border-ghost-blue'
                    : 'hover:bg-ghost-bg'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${getStatusDot(client.status)}`} />
                    <div>
                      <div className="font-medium text-ghost-text">
                        {client.client_name}
                      </div>
                      <div className="text-xs text-ghost-text-muted">
                        Connected at {formatTime(client.connected_at)}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-medium ${getStatusColor(client.status)}`}>
                      {client.status.charAt(0).toUpperCase() + client.status.slice(1)}
                    </div>
                    {client.browser_running && (
                      <div className="text-xs text-ghost-yellow">
                        Browser active
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected client info */}
      {selectedClient && (
        <div className="bg-ghost-surface rounded-lg border border-ghost-blue/50 p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-2 h-2 rounded-full ${getStatusDot(selectedClient.status)}`} />
            <span className="font-medium text-ghost-blue">
              Selected: {selectedClient.client_name}
            </span>
          </div>
          <div className="text-sm text-ghost-text-muted">
            <p>Session: {selectedClient.session_id.slice(0, 8)}...</p>
            <p>Last heartbeat: {formatTime(selectedClient.last_heartbeat)}</p>
          </div>
        </div>
      )}

      {/* Run status */}
      {runStatus && (
        <div className="bg-ghost-surface rounded-lg border border-ghost-border p-4">
          <h4 className="font-medium text-ghost-text mb-2">Execution Status</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-ghost-text-muted">Status:</span>
              <span className={
                runStatus.status === 'passed' ? 'text-ghost-green' :
                runStatus.status === 'failed' ? 'text-ghost-red' :
                runStatus.status === 'running' ? 'text-ghost-yellow' :
                'text-ghost-text'
              }>
                {runStatus.status.toUpperCase()}
              </span>
            </div>
            {runStatus.result && (
              <>
                <div className="flex justify-between">
                  <span className="text-ghost-text-muted">Scenarios:</span>
                  <span>
                    <span className="text-ghost-green">{runStatus.result.passed_scenarios} passed</span>
                    {runStatus.result.failed_scenarios > 0 && (
                      <span className="text-ghost-red"> / {runStatus.result.failed_scenarios} failed</span>
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ghost-text-muted">Duration:</span>
                  <span>{(runStatus.result.duration_ms / 1000).toFixed(2)}s</span>
                </div>
              </>
            )}
            {runStatus.last_event && (
              <div className="mt-2 p-2 bg-ghost-bg rounded text-xs">
                <span className="text-ghost-text-muted">Last event: </span>
                <span className="text-ghost-blue">{runStatus.last_event.event}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Instructions */}
      {!selectedClient && clients.length > 0 && (
        <div className="text-sm text-ghost-text-muted text-center p-2">
          Click on a client to select it for test execution
        </div>
      )}
    </div>
  );
}
