import { useState } from "react";
import { PartyPopper } from "lucide-react";
import type { Job } from "../lib/types";
import { editJob } from "../lib/api";
import { ApplicationCard } from "./ApplicationCard";
import { ScreenshotModal } from "./ScreenshotModal";
import { useKeyboard } from "../hooks/useKeyboard";

interface CardStackProps {
  currentJob: Job | null;
  cardNumber: number;
  totalCards: number;
  loading: boolean;
  started: boolean;
  onApprove: () => void;
  onSkip: () => void;
  onPanic: () => void;
}

export function CardStack({
  currentJob,
  cardNumber,
  totalCards,
  loading,
  started,
  onApprove,
  onSkip,
  onPanic,
}: CardStackProps) {
  const [editMode, setEditMode] = useState(false);
  const [showScreenshot, setShowScreenshot] = useState(false);

  useKeyboard({
    onApprove,
    onSkip,
    onPanic,
    onScreenshot: () => setShowScreenshot(true),
    onEdit: () => {
      const entering = !editMode;
      setEditMode(entering);
      if (entering && currentJob) {
        editJob(currentJob.id, [], true).catch(() => {});
      }
    },
    enabled: !!currentJob && !showScreenshot,
  });

  // Not started yet
  if (!started) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-400">
          <p className="text-lg font-medium">Ready to start</p>
          <p className="text-sm mt-1">
            Click "Start" to begin processing applications
          </p>
        </div>
      </div>
    );
  }

  // All done
  if (!currentJob) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <PartyPopper className="w-16 h-16 text-amber-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900">All caught up!</h2>
          <p className="text-gray-500 mt-2">
            No more applications to review right now.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-full relative">
      {/* Stacked card visual (background cards) */}
      <div className="absolute top-8 w-full max-w-2xl px-4">
        {totalCards > 1 && (
          <div className="bg-white rounded-xl shadow-md border border-gray-200 h-4 mx-4 opacity-60" />
        )}
        {totalCards > 2 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 h-4 mx-8 -mt-2 opacity-30" />
        )}
      </div>

      {/* Current card */}
      <div className="relative z-10 w-full px-4 flex justify-center">
        <ApplicationCard
          job={currentJob}
          cardNumber={cardNumber}
          totalCards={totalCards}
          editMode={editMode}
          loading={loading}
          onApprove={onApprove}
          onSkip={onSkip}
        />
      </div>

      {/* Edit mode indicator */}
      {editMode && (
        <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs px-3 py-1 rounded-full z-20">
          Edit Mode — press E to exit
        </div>
      )}

      {/* Screenshot modal */}
      {showScreenshot && currentJob && (
        <ScreenshotModal
          jobId={currentJob.id}
          company={currentJob.company}
          onClose={() => setShowScreenshot(false)}
        />
      )}
    </div>
  );
}
