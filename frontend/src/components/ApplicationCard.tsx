import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import type { Job } from "../lib/types";
import { FormPreview } from "./FormPreview";

interface ApplicationCardProps {
  job: Job;
  cardNumber: number;
  totalCards: number;
  editMode: boolean;
  loading: boolean;
  onApprove: () => void;
  onSkip: () => void;
  onFieldUpdate?: (index: number, value: string) => void;
}

const atsBadgeColor: Record<string, string> = {
  greenhouse: "bg-green-100 text-green-800",
  workday: "bg-blue-100 text-blue-800",
  lever: "bg-purple-100 text-purple-800",
  unknown: "bg-gray-100 text-gray-600",
};

export function ApplicationCard({
  job,
  cardNumber,
  totalCards,
  editMode,
  loading,
  onApprove,
  onSkip,
  onFieldUpdate,
}: ApplicationCardProps) {
  const filledCount = job.fields.filter((f) => f.status === "filled").length;
  const skippedCount = job.fields.filter((f) => f.status === "skipped").length;
  const aiCount = job.fields.filter(
    (f) => f.status === "ai_generated"
  ).length;

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 w-full max-w-2xl overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">
            Card {cardNumber} of {totalCards}
          </span>
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full uppercase ${
              atsBadgeColor[job.portal_type] || atsBadgeColor.unknown
            }`}
          >
            {job.portal_type || "unknown"}
          </span>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mt-1">
          {job.company}
        </h2>
        <p className="text-gray-600">{job.job_title}</p>
        {job.location && (
          <p className="text-sm text-gray-500">{job.location}</p>
        )}
      </div>

      {/* Form Preview */}
      <div className="px-6 py-4 max-h-[400px] overflow-y-auto">
        <div className="flex items-center gap-4 mb-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            {filledCount} filled
          </span>
          {skippedCount > 0 && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              {skippedCount} skipped
            </span>
          )}
          {aiCount > 0 && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              {aiCount} AI
            </span>
          )}
        </div>
        <FormPreview
          fields={job.fields}
          editMode={editMode}
          onFieldUpdate={onFieldUpdate}
        />
      </div>

      {/* Footer / Actions */}
      <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
        <button
          onClick={onSkip}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-100 transition disabled:opacity-50"
        >
          <ArrowLeft className="w-4 h-4" />
          Skip
          <kbd className="ml-1 text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
            ←
          </kbd>
        </button>

        <button
          onClick={onApprove}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 text-white bg-green-600 rounded-lg hover:bg-green-700 transition disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              Approve
              <ArrowRight className="w-4 h-4" />
              <kbd className="ml-1 text-xs text-green-200 bg-green-700 px-1.5 py-0.5 rounded">
                Enter
              </kbd>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
