import type { ReactElement } from 'react';

import { RESULT_LABELS } from '@/lib/labels';
import type { OutcomeResult } from '@/types/models';

const RESULTS: OutcomeResult[] = ['pass', 'fail', 'retake_later', 'no_show'];

interface Props {
  value: OutcomeResult | null;
  onChange: (result: OutcomeResult) => void;
  error?: string;
}

export function ResultChoice({ value, onChange, error }: Readonly<Props>): ReactElement {
  return (
    <fieldset>
      <legend className="mb-2 text-sm font-semibold">Result</legend>
      <div className="grid grid-cols-2 gap-2">
        {RESULTS.map((result) => (
          <label
            key={result}
            className="flex min-h-10 cursor-pointer items-center gap-2 rounded-lg border border-line-strong bg-white px-3 text-sm has-checked:border-grit-blue-strong has-checked:bg-select"
          >
            <input
              type="radio"
              name="result"
              value={result}
              checked={value === result}
              onChange={() => {
                onChange(result);
              }}
              className="size-4"
            />
            {RESULT_LABELS[result].label}
          </label>
        ))}
      </div>
      {error ? (
        <p role="alert" className="mt-1 text-xs text-grit-red-strong">
          {error}
        </p>
      ) : null}
    </fieldset>
  );
}
