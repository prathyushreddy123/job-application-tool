import { OctagonX } from "lucide-react";

interface PanicButtonProps {
  onClick: () => void;
  visible: boolean;
}

export function PanicButton({ onClick, visible }: PanicButtonProps) {
  if (!visible) return null;

  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-4 py-3 bg-red-600 text-white rounded-full shadow-lg hover:bg-red-700 transition active:scale-95"
      title="Emergency stop (Esc)"
    >
      <OctagonX className="w-5 h-5" />
      <span className="font-semibold text-sm">STOP</span>
      <kbd className="text-xs text-red-200 bg-red-700 px-1.5 py-0.5 rounded">
        Esc
      </kbd>
    </button>
  );
}
