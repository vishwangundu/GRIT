import type { ReactElement } from 'react';

import { Field, INPUT_CLASS } from '@/components/ui/Field';
import { addDays, istDateKey } from '@/lib/time';

interface Props {
  times: string[];
  horizonDays: number;
}

function TimeSelect(
  props: Readonly<{ id: string; name: string; label: string; times: string[]; initial: string }>,
): ReactElement {
  return (
    <Field id={props.id} label={props.label}>
      <select id={props.id} name={props.name} defaultValue={props.initial} className={INPUT_CLASS}>
        {props.times.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
    </Field>
  );
}

export function WindowFields({ times, horizonDays }: Readonly<Props>): ReactElement {
  const today = istDateKey();
  return (
    <>
      <Field id="window-date" label="Date">
        <input
          id="window-date"
          name="date"
          type="date"
          required
          min={today}
          max={addDays(today, horizonDays)}
          defaultValue={addDays(today, 1)}
          className={INPUT_CLASS}
        />
      </Field>
      <TimeSelect id="window-start" name="start" label="Start" times={times} initial="18:00" />
      <TimeSelect id="window-end" name="end" label="End" times={times} initial="20:00" />
    </>
  );
}
