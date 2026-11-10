import { Chart as ChartClass } from "chart.js";
declare global {
  const Chart: typeof ChartClass;
}
export type Status = {
  status: string;
  error: string | null;
  timestamp: number | null;
  last_success: number | null;
};
export type GPU = {
  index: number;
  uuid: string;
  name: string | null;
  gpu_util_percent: number | null;
  vram_percent: number | null;
  temperature_c: number | null;
  power_w: number | null;
  power_limit_w: number | null;
  memory_used_bytes: number | null;
  memory_total_bytes: number | null;
  status: string;
  errors: Record<string, string>;
};
export type Process = {
  pid: number;
  gpu_uuid: string;
  name: string | null;
  start_time: number | null;
  process_type: string;
  gpu_memory_bytes: number | null;
  ram_bytes: number | null;
  cpu_percent: number | null;
  gpu_util_percent: number | null;
};
export type Network = {
  name: string;
  addresses: string[];
  is_up: boolean | null;
  receive_bytes_per_second: number | null;
  transmit_bytes_per_second: number | null;
  received_bytes: number | null;
  sent_bytes: number | null;
  errors_in: number | null;
  errors_out: number | null;
  drops_in: number | null;
  drops_out: number | null;
};
export type Snapshot = {
  timestamp: number;
  sequence: number;
  stale_after_seconds: number;
  collector: Status;
  gpu: {
    source: Status;
    devices: GPU[];
    processes: Process[];
    processes_source: Status;
  };
  system: {
    source: Status;
    cpu: { usage_percent: number | null; per_core_percent: number[] };
    memory: { percent: number | null };
    disks: {
      device: string;
      mountpoint: string;
      filesystem: string;
      total_bytes: number | null;
      used_bytes: number | null;
      free_bytes: number | null;
      percent: number | null;
    }[];
    disk_io: {
      device: string;
      read_bytes_per_second: number | null;
      write_bytes_per_second: number | null;
      read_iops: number | null;
      write_iops: number | null;
      read_operations: number;
      write_operations: number;
    }[];
    network: Network[];
    info: { hostname: string };
    errors: Record<string, string>;
  };
  activity: {
    gpu_uuid: string;
    average_util_percent: number | null;
    peak_util_percent: number | null;
    active_seconds: number;
    idle_seconds: number;
    coverage_percent: number;
    process_count: number;
    vram_change_bytes: number | null;
    memory_pressure: boolean;
    average_power_w: number | null;
    peak_temperature_c: number | null;
    patterns: string[];
  }[];
  integration: { source: Status; loaded_models: string[] };
  storage: Status;
  alerts: { id: string; severity: string; message: string; since: number }[];
  observer: object;
};
export type Aggregate = {
  mean: number;
  minimum: number;
  maximum: number;
  count: number;
};
export type Point = { timestamp: number; metrics: Record<string, Aggregate> };
export type History = {
  resolution_seconds: number;
  source: Status;
  points: Point[];
};
