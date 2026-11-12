'use client';

import { type ReactElement, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { Chip } from '@/components/ui/Chip';
import { RESULT_LABELS, stateLabel } from '@/lib/labels';
import { formatDateTime } from '@/lib/time';
import type { ResultRow } from '@/types/models';

import { DecisionDialog, RaiseFlagDialog } from './FlagDialogs';
import { OverrideDialog } from './OverrideDialog';
import { CELL, StudentCell, Table } from './Table';

const HEADERS = ['Student', 'Result', 'Recorded', 'Interviewer', 'Badge status', ''] as const;
type Mode = 'flag' | 'uphold' | 'dismiss' | 'override';

function Actions({
  row,
  onPick,
}: Readonly<{ row: ResultRow; onPick: (mode: Mode) => void }>): ReactElement {
  const canFlag = row.journey_state === 'passed' && row.award_status === 'active';
  return (
    <div className="flex flex-wrap gap-1">
      {canFlag ? (
        <Button
          variant="ghost"
          onClick={() => {
            onPick('flag');
          }}
        >
          Flag malpractice
        </Button>
      ) : null}
      {row.open_flag_id ? (
        <>
          <Button
            variant="ghost"
            onClick={() => {
              onPick('uphold');
            }}
          >
            Uphold
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              onPick('dismiss');
            }}
          >
            Dismiss
          </Button>
        </>
      ) : null}
      <Button
        variant="ghost"
        onClick={() => {
          onPick('override');
        }}
      >
        Edit result
      </Button>
    </div>
  );
}

export function ResultsTable({
  rows,
  onChanged,
}: Readonly<{
  rows: ResultRow[];
  onChanged: () => Promise<unknown>;
}>): ReactElement {
  const [active, setActive] = useState<{ row: ResultRow; mode: Mode } | null>(null);
  const close = (): void => {
    setActive(null);
  };
  const rowFor = (mode: Mode): ResultRow | null => (active?.mode === mode ? active.row : null);
  return (
    <>
      <Table headers={HEADERS} isEmpty={rows.length === 0} emptyText="No results recorded yet.">
        {rows.map((row) => {
          const result = RESULT_LABELS[row.result];
          return (
            <tr key={row.booking_id}>
              <StudentCell name={row.name} campus={row.campus} />
              <td className={CELL}>
                <Chip tone={result.tone}>{result.label}</Chip>
              </td>
              <td className={CELL}>{formatDateTime(row.recorded_at)}</td>
              <td className={CELL}>{row.interviewer_name}</td>
              <td className={CELL}>
                {stateLabel(row.journey_state)}
                {row.award_status ? (
                  <span className="block text-xs text-muted">
                    Award: {row.award_status.replace('_', ' ')}
                  </span>
                ) : null}
              </td>
              <td className={CELL}>
                <Actions
                  row={row}
                  onPick={(mode) => {
                    setActive({ row, mode });
                  }}
                />
              </td>
            </tr>
          );
        })}
      </Table>
      <RaiseFlagDialog row={rowFor('flag')} onClose={close} onDone={onChanged} />
      <DecisionDialog row={rowFor('uphold')} decision="uphold" onClose={close} onDone={onChanged} />
      <DecisionDialog
        row={rowFor('dismiss')}
        decision="dismiss"
        onClose={close}
        onDone={onChanged}
      />
      <OverrideDialog row={rowFor('override')} onClose={close} onDone={onChanged} />
    </>
  );
}
