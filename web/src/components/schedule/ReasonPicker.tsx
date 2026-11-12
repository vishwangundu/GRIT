import type { ReactElement } from 'react';

export const CANCEL_REASONS = ['scheduling conflict', 'illness', 'technical issue'] as const;

interface Props {
  value: string;
  onChange: (reason: string) => void;
}

export function ReasonPicker({ value, onChange }: Readonly<Props>): ReactElement {
  return (
    <fieldset className="flex flex-col gap-2 text-sm">
      <legend className="mb-1 font-semibold">Reason (shown to the student)</legend>
      {CANCEL_REASONS.map((option) => (
        <label key={option} className="flex items-center gap-2">
          <input
            type="radio"
            name="cancel-reason"
            value={option}
            checked={value === option}
            onChange={() => {
              onChange(option);
            }}
            className="size-4"
          />
          <span className="capitalize">{option}</span>
        </label>
      ))}
    </fieldset>
  );
}
