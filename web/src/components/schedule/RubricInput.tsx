import type { ReactElement } from 'react';

import { RUBRIC_LABELS } from '@/lib/labels';

interface Props {
  areas: string[];
  min: number;
  max: number;
  value: Record<string, number | undefined>;
  onChange: (area: string, score: number) => void;
  error?: string;
}

export function RubricInput({
  areas,
  min,
  max,
  value,
  onChange,
  error,
}: Readonly<Props>): ReactElement {
  const scores = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  return (
    <div className="flex flex-col gap-3">
      {areas.map((area) => (
        <fieldset key={area} className="flex flex-wrap items-center justify-between gap-2">
          <legend className="sr-only">{RUBRIC_LABELS[area] ?? area}</legend>
          <span aria-hidden="true" className="text-sm font-semibold">
            {RUBRIC_LABELS[area] ?? area}
          </span>
          <div className="flex gap-1">
            {scores.map((score) => (
              <label key={score} className="cursor-pointer">
                <input
                  type="radio"
                  name={`rubric-${area}`}
                  value={score}
                  checked={value[area] === score}
                  onChange={() => {
                    onChange(area, score);
                  }}
                  className="peer sr-only"
                />
                <span className="flex size-10 items-center justify-center rounded-lg border border-line-strong bg-white text-sm font-semibold peer-checked:border-grit-blue-strong peer-checked:bg-grit-blue-strong peer-checked:text-white peer-focus-visible:outline-3 peer-focus-visible:outline-grit-blue-strong">
                  {score}
                </span>
              </label>
            ))}
          </div>
        </fieldset>
      ))}
      {error ? (
        <p role="alert" className="text-xs font-medium text-grit-red-strong">
          {error}
        </p>
      ) : null}
    </div>
  );
}
