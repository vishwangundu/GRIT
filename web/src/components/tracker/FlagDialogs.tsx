'use client';

import { type SubmitEvent, type ReactElement, useState } from 'react';
import { z } from 'zod';

import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { Field, INPUT_CLASS } from '@/components/ui/Field';
import { InlineError } from '@/components/ui/StateView';
import { useAction } from '@/hooks/use-action';
import { decideFlag, raiseFlag } from '@/lib/endpoints/admin';
import type { ResultRow } from '@/types/models';

const MIN_TEXT_CHARS = 3;

const flagSchema = z.object({
  source: z.string().trim().min(MIN_TEXT_CHARS, 'Say where the report came from.'),
  evidence_url: z.union([z.literal(''), z.url('Enter a full link, or leave it empty.')]),
});

interface Props {
  row: ResultRow | null;
  onClose: () => void;
  onDone: () => Promise<unknown>;
}

export function RaiseFlagDialog({ row, onClose, onDone }: Readonly<Props>): ReactElement {
  const action = useAction();
  const [error, setError] = useState<string | null>(null);

  function onSubmit(event: SubmitEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!row) return;
    const parsed = flagSchema.safeParse(Object.fromEntries(new FormData(event.currentTarget)));
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? 'Check the form.');
      return;
    }
    setError(null);
    const { source, evidence_url: evidence } = parsed.data;
    void action.run(async () => {
      await raiseFlag({
        student_id: row.student_id,
        badge_id: row.badge_id,
        source,
        evidence_url: evidence || null,
      });
      await onDone();
      onClose();
      return undefined;
    });
  }

  return (
    <Dialog isOpen={row !== null} title={`Flag malpractice: ${row?.name ?? ''}`} onClose={onClose}>
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-3">
        <p className="text-sm">
          The badge stays visible, the leaderboard entry pauses, and the student is told a review is
          open.
        </p>
        <Field id="flag-source" label="Source">
          <input
            id="flag-source"
            name="source"
            placeholder="proctoring report"
            className={INPUT_CLASS}
          />
        </Field>
        <Field id="flag-evidence" label="Evidence link (optional)">
          <input id="flag-evidence" name="evidence_url" type="url" className={INPUT_CLASS} />
        </Field>
        <InlineError message={error ?? action.error} />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Button type="submit" variant="danger" isBusy={action.isBusy}>
            Raise flag
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

interface DecisionProps extends Props {
  decision: 'uphold' | 'dismiss';
}

/** Uphold is destructive (badge and Miles removed), so it always needs this confirm step. */
export function DecisionDialog({
  row,
  decision,
  onClose,
  onDone,
}: Readonly<DecisionProps>): ReactElement {
  const action = useAction();
  const [note, setNote] = useState('');
  const isUphold = decision === 'uphold';
  const flagId = row?.open_flag_id ?? null;

  function confirm(): void {
    if (!flagId) return;
    void action.run(async () => {
      await decideFlag(flagId, { decision, note });
      await onDone();
      onClose();
      return undefined;
    });
  }

  return (
    <Dialog
      isOpen={flagId !== null}
      title={isUphold ? `Uphold flag for ${row?.name ?? ''}?` : 'Dismiss this flag?'}
      onClose={onClose}
    >
      <p className="text-sm">
        {isUphold
          ? 'This withdraws the badge, removes its Miles and moves the student back to Pre-Qualiflyer. It cannot be undone here.'
          : 'The badge returns to active and the student is told no issue was found.'}
      </p>
      <div className="mt-3">
        <Field id="decision-note" label="Decision note (required)">
          <textarea
            id="decision-note"
            rows={3}
            value={note}
            onChange={(e) => {
              setNote(e.target.value);
            }}
            className={INPUT_CLASS}
          />
        </Field>
      </div>
      <InlineError message={action.error} />
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
        <Button
          variant={isUphold ? 'danger' : 'primary'}
          disabled={note.trim().length < MIN_TEXT_CHARS}
          isBusy={action.isBusy}
          onClick={confirm}
        >
          {isUphold ? 'Uphold and nullify' : 'Dismiss flag'}
        </Button>
      </div>
    </Dialog>
  );
}
