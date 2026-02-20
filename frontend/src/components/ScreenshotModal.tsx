import { useEffect } from "react";
import { X } from "lucide-react";
import { getScreenshotUrl } from "../lib/api";

interface ScreenshotModalProps {
  jobId: string;
  company: string;
  onClose: () => void;
}

export function ScreenshotModal({
  jobId,
  company,
  onClose,
}: ScreenshotModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" || e.key === " ") {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-8"
      onClick={onClose}
    >
      <div
        className="relative bg-white rounded-xl shadow-2xl max-w-4xl max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <span className="text-sm font-medium text-gray-700">
            Screenshot — {company}
          </span>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4">
          <img
            src={getScreenshotUrl(jobId)}
            alt={`Screenshot of ${company} application`}
            className="w-full rounded border border-gray-200"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
              e.currentTarget.parentElement!.innerHTML =
                '<p class="text-gray-400 text-center py-12">No screenshot available</p>';
            }}
          />
        </div>
        <div className="px-4 py-2 border-t border-gray-100 text-xs text-gray-400 text-center">
          Press Space or Esc to close
        </div>
      </div>
    </div>
  );
}
