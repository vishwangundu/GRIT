import type { ReactElement } from 'react';

import { Field, INPUT_CLASS } from '@/components/ui/Field';
import { addDays, istDateKey } from '@/lib/time';

interface Props {
  value: string;
  error?: string;
  onChange: (date: string) => void;
}

export function RetakeDateField({ value, error, onChange }: Readonly<Props>): ReactElement {
  return (
    <Field id="retake-date" label="Student can rebook from (IST)" error={error}>
      <input
        id="retake-date"
        type="date"
        min={addDays(istDateKey(), 1)}
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
        }}
        className={INPUT_CLASS}
      />
    </Field>
  );
}
