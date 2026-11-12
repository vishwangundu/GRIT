import type { ReactElement } from 'react';

import { Chip } from '@/components/ui/Chip';
import { IconButton } from '@/components/ui/IconButton';
import { SendIcon } from '@/components/ui/icons';
import { WAIT_LABELS } from '@/lib/labels';
import { formatDate, formatDateTime } from '@/lib/time';
import type { NotBookedRow } from '@/types/models';

import { CELL, StudentCell } from './Table';

interface Props {
  row: NotBookedRow;
  isBusy: boolean;
  onNudge: (studentId: string) => void;
}

export function NotBookedRowView({ row, isBusy, onNudge }: Readonly<Props>): ReactElement {
  const label = WAIT_LABELS[row.status];
  return (
    <tr>
      <StudentCell name={row.name} campus={row.campus} />
      <td className={CELL}>
        <Chip tone={label.tone}>
          {label.label}
          {row.until ? ` ${formatDate(row.until)}` : ''}
        </Chip>
      </td>
      <td className={CELL}>
        {row.days_since_eligible ?? '–'}
        {row.is_slow ? (
          <span className="ml-2">
            <Chip tone="danger">Slow</Chip>
          </span>
        ) : null}
      </td>
      <td className={CELL}>{row.last_nudged_at ? formatDateTime(row.last_nudged_at) : 'Never'}</td>
      <td className={`${CELL} text-right`}>
        <IconButton
          label={row.can_nudge ? `Send nudge: ${row.name}` : `Nudge not available yet: ${row.name}`}
          isDisabled={!row.can_nudge || isBusy}
          onClick={() => {
            onNudge(row.student_id);
          }}
        >
          <SendIcon />
        </IconButton>
      </td>
    </tr>
  );
}
