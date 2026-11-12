'use client';

import type { ReactElement, SubmitEvent } from 'react';
import { z } from 'zod';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { InlineError } from '@/components/ui/StateView';
import { useAction } from '@/hooks/use-action';
import { addWindow } from '@/lib/endpoints/interviewer';
import { halfHourOptions } from '@/lib/half-hours';
import type { Rules } from '@/types/models';

import { WindowFields } from './WindowFields';

const windowSchema = z
  .object({ date: z.iso.date(), start: z.string(), end: z.string() })
  .refine((w) => w.end > w.start, { message: 'End time must be after start time.' });

interface Props {
  rules: Rules;
  onAdded: () => Promise<unknown>;
}

export function AddWindowForm({ rules, onAdded }: Readonly<Props>): ReactElement {
  const action = useAction();

  function onSubmit(event: SubmitEvent<HTMLFormElement>): void {
    event.preventDefault();
    const parsed = windowSchema.safeParse(Object.fromEntries(new FormData(event.currentTarget)));
    void action.run(async () => {
      if (!parsed.success) throw new Error(parsed.error.issues[0]?.message ?? 'Check the window.');
      const created = await addWindow(parsed.data);
      await onAdded();
      return `Added ${String(created.slots_created)} slots.`;
    });
  }

  return (
    <Card band="Add availability (IST)" tone="warning">
      <form onSubmit={onSubmit} noValidate className="grid gap-3 sm:grid-cols-4 sm:items-end">
        <WindowFields
          times={halfHourOptions(rules.slot_minutes)}
          horizonDays={rules.book_horizon_days}
        />
        <Button type="submit" isBusy={action.isBusy}>
          Add window
        </Button>
      </form>
      <div className="mt-2">
        <InlineError message={action.error} />
        {action.message ? (
          <p role="status" className="text-sm font-medium text-grit-green">
            {action.message}
          </p>
        ) : null}
      </div>
    </Card>
  );
}
