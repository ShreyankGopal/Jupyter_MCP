/**
 * Shared TypeScript types for Jupyter kernel management
 * These types match the Python implementation for cross-tool compatibility
 */

export interface KernelInfo {
  kernel_id: string;           // SHA256 hash of notebook path
  jupyter_kernel_id: string;   // Jupyter's actual kernel UUID
  notebook_path: string;      // Absolute path to notebook
  kernel_name: string;        // e.g., "python3"
  status: 'running' | 'stopped' | 'error';
  connection_info: ConnectionInfo;
  created_at: string;         // ISO timestamp
  last_updated: string;       // ISO timestamp
}

export interface ConnectionInfo {
  ip: string;
  ports: {
    shell_port: number;
    iopub_port: number;
    stdin_port: number;
    control_port: number;
    hb_port: number;
  };
  transport: 'tcp' | 'ipc';
  key: string;
  signature_scheme: string;
}

export interface ExecutionResult {
  status: 'ok' | 'error' | 'timeout';
  execution_count?: number;
  outputs: Output[];
  ename?: string;
  evalue?: string;
  traceback?: string[];
}

export interface Output {
  output_type: 'stream' | 'execute_result' | 'display_data' | 'error';
  name?: string;
  text?: string;
  data?: Record<string, any>;
  metadata?: Record<string, any>;
  execution_count?: number;
  ename?: string;
  evalue?: string;
  traceback?: string[];
}

export interface KernelStatus {
  is_running: boolean;
  kernel_id?: string;
  jupyter_kernel_id?: string;
}

export interface Cell {
  cell_id: string;
  position: number;
  cell_type: 'code' | 'markdown' | 'raw';
  source: string;
  line_start: number;
  line_end: number;
  execution_count?: number;
  has_output: boolean;
}
