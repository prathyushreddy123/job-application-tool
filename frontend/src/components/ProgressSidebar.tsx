import { useEffect, useState } from "react";
import {
  CheckCircle2,
  SkipForward,
  AlertCircle,
  Clock,
  Wifi,
  WifiOff,
} from "lucide-react";
import { fetchStatus } from "../lib/api";

interface ProgressSidebarProps {
  counts: {
    approved: number;
    skipped: number;
    failed: number;
    pending: number;
  };
  recentEvents: { type: string; company: string; time: string }[];
  running: boolean;
}

export function ProgressSidebar({
  counts,
  recentEvents,
  running,
}: ProgressSidebarProps) {
  const [n8nOnline, setN8nOnline] = useState(true);

  useEffect(() => {
    if (!running) return;
    const check = async () => {
      try {
        const status = await fetchStatus();
        setN8nOnline(status.n8n_online);
      } catch {
        // ignore
      }
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, [running]);

  const total = counts.approved + counts.skipped + counts.failed;

  return (
    <div className="w-72 bg-white border-l border-gray-200 flex flex-col h-full">
      {/* Counts */}
      <div className="px-5 py-4 border-b border-gray-100">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Progress
        </h3>
        <div className="space-y-2">
          <CountRow
            icon={<CheckCircle2 className="w-4 h-4 text-green-500" />}
            label="Approved"
            count={counts.approved}
          />
          <CountRow
            icon={<SkipForward className="w-4 h-4 text-gray-400" />}
            label="Skipped"
            count={counts.skipped}
          />
          <CountRow
            icon={<AlertCircle className="w-4 h-4 text-red-400" />}
            label="Failed"
            count={counts.failed}
          />
          <CountRow
            icon={<Clock className="w-4 h-4 text-amber-500" />}
            label="Pending"
            count={counts.pending}
          />
        </div>
        {total > 0 && (
          <div className="mt-3">
            <div className="w-full bg-gray-100 rounded-full h-1.5">
              <div
                className="bg-green-500 h-1.5 rounded-full transition-all"
                style={{
                  width: `${(counts.approved / (total + counts.pending)) * 100}%`,
                }}
              />
            </div>
            <p className="text-xs text-gray-400 mt-1">
              {total} processed of {total + counts.pending}
            </p>
          </div>
        )}
      </div>

      {/* Status */}
      <div className="px-5 py-3 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Status</span>
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              running
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-500"
            }`}
          >
            {running ? "Running" : "Stopped"}
          </span>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-gray-500">n8n</span>
          <span className="flex items-center gap-1 text-xs">
            {n8nOnline ? (
              <>
                <Wifi className="w-3 h-3 text-green-500" />
                <span className="text-green-600">Online</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3 text-red-400" />
                <span className="text-red-500">Offline</span>
              </>
            )}
          </span>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="px-5 py-4 flex-1 overflow-y-auto">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Recent Activity
        </h3>
        {recentEvents.length === 0 ? (
          <p className="text-xs text-gray-400 italic">No activity yet</p>
        ) : (
          <div className="space-y-2">
            {recentEvents.map((event, i) => (
              <div
                key={`${event.time}-${i}`}
                className="flex items-start gap-2 text-xs"
              >
                <span
                  className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${
                    event.type === "submitted"
                      ? "bg-green-500"
                      : event.type === "skipped"
                        ? "bg-gray-400"
                        : "bg-red-400"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <span className="text-gray-700 truncate block">
                    {event.company}
                  </span>
                  <span className="text-gray-400">{event.type}</span>
                </div>
                <span className="text-gray-300 flex-shrink-0">
                  {event.time}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Keyboard hints */}
      <div className="px-5 py-3 border-t border-gray-100 bg-gray-50">
        <p className="text-xs text-gray-400 font-medium mb-1">Shortcuts</p>
        <div className="grid grid-cols-2 gap-1 text-xs text-gray-400">
          <span>
            <kbd className="bg-gray-200 text-gray-600 px-1 rounded">Enter</kbd>{" "}
            Approve
          </span>
          <span>
            <kbd className="bg-gray-200 text-gray-600 px-1 rounded">←</kbd>{" "}
            Skip
          </span>
          <span>
            <kbd className="bg-gray-200 text-gray-600 px-1 rounded">Esc</kbd>{" "}
            Stop
          </span>
          <span>
            <kbd className="bg-gray-200 text-gray-600 px-1 rounded">Space</kbd>{" "}
            Screenshot
          </span>
          <span>
            <kbd className="bg-gray-200 text-gray-600 px-1 rounded">E</kbd>{" "}
            Edit
          </span>
        </div>
      </div>
    </div>
  );
}

function CountRow({
  icon,
  label,
  count,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm text-gray-600">{label}</span>
      </div>
      <span className="text-sm font-semibold text-gray-900">{count}</span>
    </div>
  );
}
