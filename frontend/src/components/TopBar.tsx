import { useState } from "react";
import { Play, Loader2 } from "lucide-react";
import { startAutomation } from "../lib/api";

interface TopBarProps {
  running: boolean;
  onStarted: () => void;
}

export function TopBar({ running, onStarted }: TopBarProps) {
  const [demo, setDemo] = useState(true);
  const [dryRun, setDryRun] = useState(false);
  const [starting, setStarting] = useState(false);

  const handleStart = async () => {
    setStarting(true);
    try {
      await startAutomation(demo, dryRun);
      onStarted();
    } catch (err) {
      console.error("Failed to start:", err);
    } finally {
      setStarting(false);
    }
  };

  return (
    <div className="h-14 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
      <h1 className="text-lg font-bold text-gray-900">Job Auto-Apply</h1>

      <div className="flex items-center gap-4">
        <label className="flex items-center gap-1.5 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={demo}
            onChange={(e) => setDemo(e.target.checked)}
            disabled={running}
            className="rounded border-gray-300"
          />
          Demo
        </label>
        <label className="flex items-center gap-1.5 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={dryRun}
            onChange={(e) => setDryRun(e.target.checked)}
            disabled={running}
            className="rounded border-gray-300"
          />
          Dry Run
        </label>

        <button
          onClick={handleStart}
          disabled={running || starting}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {starting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          {running ? "Running" : "Start"}
        </button>
      </div>
    </div>
  );
}
