'use client';

import type { ReactElement } from 'react';

import { Button } from '@/components/ui/Button';
import { Chip } from '@/components/ui/Chip';
import { InlineError } from '@/components/ui/StateView';
import { useAction } from '@/hooks/use-action';
import { remindInterviewer } from '@/lib/endpoints/admin';
import type { Tone } from '@/lib/tones';
import { formatDateTime, formatDuration, msUntil } from '@/lib/time';
import type { AwaitingRow } from '@/types/models';

import { CELL, StudentCell, Table } from './Table';

const HEADERS = ['Student', 'Interview', 'Interviewer', 'Status', ''] as const;

function status(row: AwaitingRow): { tone: Tone; label: string } {
  if (row.status === 'in_progress') return { tone: 'success', label: 'In progress' };
  if (row.status === 'overdue') return { tone: 'danger', label: 'Overdue' };
  return { tone: 'warning', label: `Due in ${formatDuration(msUntil(row.due_at))}` };
}

export function AwaitingTable({ rows }: Readonly<{ rows: AwaitingRow[] }>): ReactElement {
  const action = useAction();
  return (
    <div className="flex flex-col gap-2">
      {action.message ? (
        <p role="status" className="text-sm text-grit-green">
          {action.message}
        </p>
      ) : null}
      <InlineError message={action.error} />
      <Table headers={HEADERS} isEmpty={rows.length === 0} emptyText="No results pending.">
        {rows.map((row) => {
          const chip = status(row);
          return (
            <tr key={row.booking_id}>
              <StudentCell name={row.name} campus={row.campus} />
              <td className={CELL}>{formatDateTime(row.start_at)}</td>
              <td className={CELL}>{row.interviewer_name}</td>
              <td className={CELL}>
                <Chip tone={chip.tone}>{chip.label}</Chip>
              </td>
              <td className={CELL}>
                <Button
                  variant="ghost"
                  disabled={row.status === 'in_progress' || action.isBusy}
                  onClick={() =>
                    void action.run(async () => {
                      await remindInterviewer(row.booking_id);
                      return `Reminder sent to ${row.interviewer_name}.`;
                    })
                  }
                >
                  Remind interviewer
                </Button>
              </td>
            </tr>
          );
        })}
      </Table>
    </div>
  );
}
