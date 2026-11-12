'use client';

import { type ReactElement, useState } from 'react';

import { CancelInterviewDialog } from '@/components/schedule/CancelInterviewDialog';
import { IconButton } from '@/components/ui/IconButton';
import { CloseIcon, SwapIcon } from '@/components/ui/icons';
import { formatDateTime } from '@/lib/time';
import type { BookedRow } from '@/types/models';

import { ReassignDialog } from './ReassignDialog';
import { CELL, InterviewerCell, StudentCell, Table } from './Table';

const HEADERS = [
  'Student',
  'Slot time',
  'Interviewer',
  'Booked at',
  'Reschedules used',
  '',
] as const;

interface Props {
  rows: BookedRow[];
  onChanged: () => Promise<unknown>;
}

export function BookedTable({ rows, onChanged }: Readonly<Props>): ReactElement {
  const [reassigning, setReassigning] = useState<BookedRow | null>(null);
  const [cancelling, setCancelling] = useState<BookedRow | null>(null);
  return (
    <>
      <Table headers={HEADERS} isEmpty={rows.length === 0} emptyText="No upcoming interviews.">
        {rows.map((row) => (
          <tr key={row.booking_id}>
            <StudentCell name={row.name} campus={row.campus} />
            <td className={CELL}>{formatDateTime(row.start_at)}</td>
            <InterviewerCell name={row.interviewer_name} />
            <td className={CELL}>{formatDateTime(row.booked_at)}</td>
            <td className={CELL}>{row.reschedules_used}</td>
            <td className={`${CELL} whitespace-nowrap text-right`}>
              <IconButton
                label={`Reassign interviewer: ${row.name}`}
                onClick={() => {
                  setReassigning(row);
                }}
              >
                <SwapIcon />
              </IconButton>
              <IconButton
                label={`Cancel interview: ${row.name}`}
                tone="danger"
                onClick={() => {
                  setCancelling(row);
                }}
              >
                <CloseIcon />
              </IconButton>
            </td>
          </tr>
        ))}
      </Table>
      <ReassignDialog
        row={reassigning}
        onClose={() => {
          setReassigning(null);
        }}
        onDone={onChanged}
      />
      <CancelInterviewDialog
        slotId={cancelling?.slot_id ?? null}
        studentName={cancelling?.name ?? ''}
        onClose={() => {
          setCancelling(null);
        }}
        onDone={onChanged}
      />
    </>
  );
}
