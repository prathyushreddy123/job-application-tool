export type FieldStatus = "filled" | "skipped" | "ai_generated" | "failed";

export interface FilledField {
  label: string;
  value: string;
  status: FieldStatus;
  source: string;
}

export interface JobTiming {
  url_opened_at: string;
  form_filled_at: string;
  user_reviewed_at: string;
  submitted_at: string;
}

export type JobStatus =
  | "new"
  | "filling"
  | "ready"
  | "approved"
  | "submitted"
  | "failed"
  | "skipped";

export interface Job {
  id: string;
  job_url: string;
  company: string;
  job_title: string;
  location: string;
  portal_type: string;
  priority: string;
  status: JobStatus;
  date_added: string;
  fields: FilledField[];
  screenshot_path: string;
  error_log: string;
  timing: JobTiming;
}

export interface AutomationStatus {
  running: boolean;
  mode: string;
  jobs: Record<string, number>;
  n8n_online: boolean;
  n8n_queued: number;
  pending_count?: number;
  ready_count?: number;
  total_processed?: number;
  consecutive_failures?: number;
}

export interface WsMessage {
  type: string;
  job_id?: string;
  company?: string;
  error?: string;
  count?: number;
  mode?: string;
  job_count?: number;
}
