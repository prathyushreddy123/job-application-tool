import { useCallback, useEffect, useRef, useState } from "react";
import { approveJob, fetchJobs, skipJob } from "../lib/api";
import type { Job, WsMessage } from "../lib/types";
import { wsClient } from "../lib/websocket";

interface JobCounts {
  approved: number;
  skipped: number;
  failed: number;
  pending: number;
}

export function useJobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [counts, setCounts] = useState<JobCounts>({
    approved: 0,
    skipped: 0,
    failed: 0,
    pending: 0,
  });
  const [recentEvents, setRecentEvents] = useState<
    { type: string; company: string; time: string }[]
  >([]);

  // Track jobs that are actionable (ready/new)
  const actionableJobs = jobs.filter(
    (j) => j.status === "ready" || j.status === "new"
  );
  const currentJob = actionableJobs[currentIndex] ?? null;

  const loadJobs = useCallback(async () => {
    try {
      const fetched = await fetchJobs();
      setJobs(fetched);
      setCurrentIndex(0);
      updateCounts(fetched);
    } catch (err) {
      console.error("Failed to fetch jobs:", err);
    }
  }, []);

  const updateCounts = (jobList: Job[]) => {
    setCounts({
      approved: jobList.filter(
        (j) => j.status === "submitted" || j.status === "approved"
      ).length,
      skipped: jobList.filter((j) => j.status === "skipped").length,
      failed: jobList.filter((j) => j.status === "failed").length,
      pending: jobList.filter(
        (j) => j.status === "ready" || j.status === "new"
      ).length,
    });
  };

  const addEvent = (type: string, company: string) => {
    const time = new Date().toLocaleTimeString();
    setRecentEvents((prev) => [{ type, company, time }, ...prev].slice(0, 10));
  };

  const approve = useCallback(async () => {
    if (!currentJob || loading) return;
    setLoading(true);
    try {
      await approveJob(currentJob.id);
      setJobs((prev) => {
        const updated = prev.map((j) =>
          j.id === currentJob.id ? { ...j, status: "submitted" as const } : j
        );
        updateCounts(updated);
        return updated;
      });
      addEvent("submitted", currentJob.company);
      // Don't increment index — the filter will naturally skip this job
    } catch (err) {
      console.error("Approve failed:", err);
      addEvent("failed", currentJob.company);
    } finally {
      setLoading(false);
    }
  }, [currentJob, loading]);

  const skip = useCallback(async () => {
    if (!currentJob || loading) return;
    setLoading(true);
    try {
      await skipJob(currentJob.id);
      setJobs((prev) => {
        const updated = prev.map((j) =>
          j.id === currentJob.id ? { ...j, status: "skipped" as const } : j
        );
        updateCounts(updated);
        return updated;
      });
      addEvent("skipped", currentJob.company);
    } catch (err) {
      console.error("Skip failed:", err);
    } finally {
      setLoading(false);
    }
  }, [currentJob, loading]);

  // WebSocket handler
  useEffect(() => {
    const unsubscribe = wsClient.onMessage((msg: WsMessage) => {
      if (msg.type === "jobs_synced") {
        loadJobs();
      }
      if (msg.type === "job_submitted" && msg.company) {
        addEvent("submitted", msg.company);
      }
      if (msg.type === "job_failed" && msg.company) {
        addEvent("failed", msg.company);
      }
    });
    return unsubscribe;
  }, [loadJobs]);

  // Fallback polling every 5 seconds
  const pollRef = useRef<ReturnType<typeof setInterval>>(undefined);
  useEffect(() => {
    pollRef.current = setInterval(() => {
      if (!wsClient.isConnected) {
        loadJobs();
      }
    }, 5000);
    return () => clearInterval(pollRef.current);
  }, [loadJobs]);

  return {
    jobs,
    currentJob,
    currentIndex: actionableJobs.indexOf(currentJob!),
    totalActionable: actionableJobs.length,
    counts,
    recentEvents,
    loading,
    loadJobs,
    approve,
    skip,
  };
}
