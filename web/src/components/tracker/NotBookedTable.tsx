'use client';

import type { ReactElement } from 'react';

import { Button } from '@/components/ui/Button';
import { InlineError } from '@/components/ui/StateView';
import { useAction } from '@/hooks/use-action';
import { sendNudges } from '@/lib/endpoints/admin';
import { plural } from '@/lib/labels';
import type { NotBookedRow, NudgeRequest } from '@/types/models';

import { NotBookedRowView } from './NotBookedRowView';
import { Table } from './Table';

const HEADERS = ['Student', 'Status', 'Days since eligible', 'Last nudge', ''] as const;

interface Props {
  rows: NotBookedRow[];
  slowAfterDays: number;
  onChanged: () => Promise<unknown>;
}

export function NotBookedTable({ rows, slowAfterDays, onChanged }: Readonly<Props>): ReactElement {
  const action = useAction();

  function nudge(body: NudgeRequest): void {
    void action.run(async () => {
      const result = await sendNudges(body);
      await onChanged();
      const skipped = String(result.skipped_recent);
      return `Sent ${plural(result.sent, 'nudge')}; skipped ${skipped} nudged in the last 24 h.`;
    });
  }

  return (
    <div className="grit-fill flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="secondary"
          isBusy={action.isBusy}
          onClick={() => {
            nudge({ min_days_waiting: slowAfterDays });
          }}
        >
          Nudge everyone waiting {slowAfterDays}+ days
        </Button>
        {action.message ? (
          <p role="status" className="text-sm text-grit-green">
            {action.message}
          </p>
        ) : null}
        <InlineError message={action.error} />
      </div>
      <Table
        headers={HEADERS}
        isEmpty={rows.length === 0}
        emptyText="Every eligible student has booked."
      >
        {rows.map((row) => (
          <NotBookedRowView
            key={row.student_id}
            row={row}
            isBusy={action.isBusy}
            onNudge={(id) => {
              nudge({ student_ids: [id] });
            }}
          />
        ))}
      </Table>
    </div>
  );
}
