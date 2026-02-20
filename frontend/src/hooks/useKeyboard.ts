import { useEffect } from "react";

interface KeyboardActions {
  onApprove: () => void;
  onSkip: () => void;
  onPanic: () => void;
  onScreenshot: () => void;
  onEdit: () => void;
  enabled: boolean;
}

export function useKeyboard({
  onApprove,
  onSkip,
  onPanic,
  onScreenshot,
  onEdit,
  enabled,
}: KeyboardActions) {
  useEffect(() => {
    if (!enabled) return;

    const handler = (e: KeyboardEvent) => {
      // Don't capture when typing in an input/textarea
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      switch (e.key) {
        case "Enter":
        case "ArrowRight":
          e.preventDefault();
          onApprove();
          break;
        case "ArrowLeft":
        case "s":
        case "S":
          e.preventDefault();
          onSkip();
          break;
        case "Escape":
          e.preventDefault();
          onPanic();
          break;
        case " ":
          e.preventDefault();
          onScreenshot();
          break;
        case "e":
        case "E":
          e.preventDefault();
          onEdit();
          break;
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onApprove, onSkip, onPanic, onScreenshot, onEdit, enabled]);
}
