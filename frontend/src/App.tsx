import { useState, useCallback } from "react";
import { Toaster, toast } from "sonner";
import { useJobs } from "./hooks/useJobs";
import { stopAutomation } from "./lib/api";
import { TopBar } from "./components/TopBar";
import { CardStack } from "./components/CardStack";
import { ProgressSidebar } from "./components/ProgressSidebar";
import { PanicButton } from "./components/PanicButton";

function App() {
  const [started, setStarted] = useState(false);
  const [running, setRunning] = useState(false);

  const {
    currentJob,
    currentIndex,
    totalActionable,
    counts,
    recentEvents,
    loading,
    loadJobs,
    approve,
    skip,
  } = useJobs();

  const handleStarted = useCallback(() => {
    setStarted(true);
    setRunning(true);
    loadJobs();
    toast.success("Automation started");
  }, [loadJobs]);

  const handleApprove = useCallback(async () => {
    if (!currentJob) return;
    const company = currentJob.company;
    await approve();
    toast.success(`Approved: ${company}`);
  }, [currentJob, approve]);

  const handleSkip = useCallback(async () => {
    if (!currentJob) return;
    const company = currentJob.company;
    await skip();
    toast("Skipped: " + company, { icon: "⏭" });
  }, [currentJob, skip]);

  const handlePanic = useCallback(async () => {
    try {
      await stopAutomation();
      setRunning(false);
      toast.error("Automation stopped");
    } catch (err) {
      console.error("Stop failed:", err);
      toast.error("Failed to stop automation");
    }
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Toaster position="top-center" richColors />

      <TopBar running={running} onStarted={handleStarted} />

      <div className="flex flex-1 overflow-hidden">
        {/* Main card area */}
        <div className="flex-1 overflow-y-auto p-6">
          <CardStack
            currentJob={currentJob}
            cardNumber={currentIndex + 1}
            totalCards={totalActionable}
            loading={loading}
            started={started}
            onApprove={handleApprove}
            onSkip={handleSkip}
            onPanic={handlePanic}
          />
        </div>

        {/* Sidebar */}
        <ProgressSidebar
          counts={counts}
          recentEvents={recentEvents}
          running={running}
        />
      </div>

      <PanicButton onClick={handlePanic} visible={running} />
    </div>
  );
}

export default App;
