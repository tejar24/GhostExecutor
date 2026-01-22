// Test execution types
export interface TestRunRequest {
  feature_files: string[];
  headless?: boolean;
  slow_mo?: number;
}

export interface TestRunResponse {
  run_id: string;
  status: string;
  message: string;
  results_url: string;
}

export interface TestRunStatus {
  run_id: string;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'error' | 'skipped';
  progress: {
    total: number;
    completed: number;
    passed: number;
    failed: number;
  };
  current_scenario?: string;
  results?: ScenarioResult[];
  error?: string;
}

export interface ScenarioResult {
  status: 'passed' | 'failed';
  total_scenarios: number;
  passed_scenarios: number;
  failed_scenarios: number;
  scenarios: {
    name: string;
    status: string;
    steps: StepResult[];
  }[];
}

export interface StepResult {
  keyword: string;
  step_text: string;
  status: string;
  error?: string;
}

// SSE Event types
export interface SSEEvent {
  type: string;
  timestamp: string;
  data: SSEEventData;
}

export type SSEEventData =
  | ScenarioStartEvent
  | ScenarioEndEvent
  | StepStartEvent
  | StepResultEvent
  | HealingEvent
  | RunCompleteEvent;

export interface ScenarioStartEvent {
  scenario_name: string;
  feature_name: string;
  timestamp: string;
}

export interface ScenarioEndEvent {
  scenario_name: string;
  feature_name: string;
  duration_ms: number;
  total_steps: number;
  passed_steps: number;
  failed_steps: number;
  healed_steps: number;
  timestamp: string;
}

export interface StepStartEvent {
  step_text: string;
  action_type: string;
  selector?: string;
  timestamp: string;
}

export interface StepResultEvent {
  step_text: string;
  success: boolean;
  duration_ms: number;
  error?: string;
  action_type: string;
  timestamp: string;
}

export interface HealingEvent {
  original_selector: string;
  tried_selector: string;
  success: boolean;
  method: string;
  timestamp: string;
}

export interface RunCompleteEvent {
  status: 'passed' | 'failed' | 'error';
}

// Log entry for display
export interface LogEntry {
  id: string;
  timestamp: string;
  type: 'scenario_start' | 'scenario_end' | 'step_start' | 'step_result' | 'healing' | 'info' | 'error';
  message: string;
  success?: boolean;
  duration_ms?: number;
}

// Feature types
export interface Feature {
  id: string;
  name: string;
  file_path: string;
  content: string;
  scenario_count: number;
}

export interface FeatureListItem {
  filename: string;
  name: string;
}

// API Health
export interface HealthResponse {
  status: string;
  timestamp: string;
}

// Remote Execution Types
export type ClientStatus = 'connected' | 'busy' | 'disconnected';

export interface RemoteClient {
  session_id: string;
  client_name: string;
  status: ClientStatus;
  connected_at: string;
  last_heartbeat: string;
  browser_running: boolean;
}

export interface RemoteClientListResponse {
  clients: RemoteClient[];
  total: number;
}

export interface RemoteRunRequest {
  session_id: string;
  feature_content: string;
  headless?: boolean;
  slow_mo?: number;
}

export interface RemoteRunResponse {
  run_id: string;
  session_id: string;
  status: string;
  message: string;
}

export interface RemoteRunStatus {
  session_id: string;
  status: string;
  result?: {
    run_id: string;
    status: string;
    total_scenarios: number;
    passed_scenarios: number;
    failed_scenarios: number;
    duration_ms: number;
    errors?: string[];
  };
  last_event?: {
    event: string;
    data: Record<string, unknown>;
  };
}
