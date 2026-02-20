import { useState } from "react";
import { Bot, Check, AlertTriangle, X } from "lucide-react";
import type { FilledField } from "../lib/types";

interface FormPreviewProps {
  fields: FilledField[];
  editMode: boolean;
  onFieldUpdate?: (index: number, value: string) => void;
}

const statusIcon = {
  filled: <Check className="w-4 h-4 text-green-600" />,
  skipped: <AlertTriangle className="w-4 h-4 text-amber-500" />,
  ai_generated: <Bot className="w-4 h-4 text-blue-500" />,
  failed: <X className="w-4 h-4 text-red-500" />,
};

export function FormPreview({
  fields,
  editMode,
  onFieldUpdate,
}: FormPreviewProps) {
  return (
    <div className="space-y-1">
      <div className="grid grid-cols-[1fr_auto] gap-x-3 text-sm">
        {fields.map((field, i) => (
          <FieldRow
            key={`${field.label}-${i}`}
            field={field}
            index={i}
            editable={
              editMode || field.status === "ai_generated"
            }
            onUpdate={onFieldUpdate}
          />
        ))}
      </div>
    </div>
  );
}

function FieldRow({
  field,
  index,
  editable,
  onUpdate,
}: {
  field: FilledField;
  index: number;
  editable: boolean;
  onUpdate?: (index: number, value: string) => void;
}) {
  const [value, setValue] = useState(field.value);

  const handleChange = (val: string) => {
    setValue(val);
    onUpdate?.(index, val);
  };

  return (
    <>
      <div className="flex items-center gap-2 py-1.5 border-b border-gray-100">
        <span className="flex-shrink-0">{statusIcon[field.status]}</span>
        <span className="text-gray-500 min-w-[120px]">{field.label}:</span>
        {editable ? (
          <input
            type="text"
            value={value}
            onChange={(e) => handleChange(e.target.value)}
            className="flex-1 px-2 py-0.5 text-gray-900 bg-blue-50 border border-blue-200 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
          />
        ) : (
          <span
            className={`flex-1 ${
              field.status === "skipped"
                ? "text-amber-600 italic"
                : "text-gray-900"
            }`}
          >
            {field.value || "(empty)"}
          </span>
        )}
      </div>
      <div /> {/* Grid spacer */}
    </>
  );
}
