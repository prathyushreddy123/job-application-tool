import type { AutomationStatus, Job } from "./types";

const API_KEY = "dev-key";

const headers = {
  "Content-Type": "application/json",
  "X-API-Key": API_KEY,
};

export async function fetchJobs(): Promise<Job[]> {
  const res = await fetch("/api/jobs", { headers });
  if (!res.ok) throw new Error(`Failed to fetch jobs: ${res.status}`);
  return res.json();
}

export async function approveJob(
  jobId: string
): Promise<{ status: string; job_id: string }> {
  const res = await fetch(`/api/jobs/${jobId}/approve`, {
    method: "POST",
    headers,
  });
  if (!res.ok) throw new Error(`Failed to approve job: ${res.status}`);
  return res.json();
}

export async function skipJob(
  jobId: string
): Promise<{ status: string; job_id: string }> {
  const res = await fetch(`/api/jobs/${jobId}/skip`, {
    method: "POST",
    headers,
  });
  if (!res.ok) throw new Error(`Failed to skip job: ${res.status}`);
  return res.json();
}

export async function startAutomation(
  demo = false,
  dryRun = false
): Promise<{ status: string; mode: string; job_count: number }> {
  const params = new URLSearchParams();
  if (demo) params.set("demo", "true");
  if (dryRun) params.set("dry_run", "true");
  const res = await fetch(`/api/automation/start?${params}`, {
    method: "POST",
    headers,
  });
  if (!res.ok) throw new Error(`Failed to start: ${res.status}`);
  return res.json();
}

export async function stopAutomation(): Promise<{ status: string }> {
  const res = await fetch("/api/automation/stop", {
    method: "POST",
    headers,
  });
  if (!res.ok) throw new Error(`Failed to stop: ${res.status}`);
  return res.json();
}

export async function fetchStatus(): Promise<AutomationStatus> {
  const res = await fetch("/api/automation/status", { headers });
  if (!res.ok) throw new Error(`Failed to fetch status: ${res.status}`);
  return res.json();
}

export async function fetchStats(): Promise<Record<string, unknown>> {
  const res = await fetch("/api/stats", { headers });
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`);
  return res.json();
}

export async function editJob(
  jobId: string,
  fields: { label: string; value: string }[],
  bringBrowserToFront = false
): Promise<{ status: string; job_id: string; edits_applied: number }> {
  const res = await fetch(`/api/jobs/${jobId}/edit`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      fields,
      bring_browser_to_front: bringBrowserToFront,
    }),
  });
  if (!res.ok) throw new Error(`Failed to edit job: ${res.status}`);
  return res.json();
}

export function getScreenshotUrl(jobId: string): string {
  return `/api/jobs/${jobId}/screenshot`;
}
