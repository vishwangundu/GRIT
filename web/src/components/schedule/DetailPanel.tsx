'use client';

import { type ReactElement, useState } from 'react';

import { Card } from '@/components/ui/Card';
import { Chip } from '@/components/ui/Chip';
import { ErrorBox, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { useRules } from '@/hooks/use-session';
import { PATHS } from '@/lib/endpoints/paths';
import { CHIP_LABELS } from '@/lib/labels';
import { formatDate, formatRange } from '@/lib/time';
import type { InterviewDetail } from '@/types/models';

import { CancelInterviewDialog } from './CancelInterviewDialog';
import { DetailActions } from './DetailActions';
import { DetailResult } from './DetailResult';
import { StudentContext } from './StudentContext';

interface Props {
  bookingId: string;
  onChanged: () => Promise<unknown>;
}

export function DetailPanel({ bookingId, onChanged }: Readonly<Props>): ReactElement {
  const { data, error, mutate } = useApi<InterviewDetail>(PATHS.interview(bookingId));
  const { data: rules } = useRules();
  const [isCancelling, setIsCancelling] = useState(false);

  if (error) return <ErrorBox error={error} onRetry={() => void mutate()} />;
  if (!data || !rules) return <Loading label="Loading interview…" />;

  const refresh = (): Promise<unknown> => Promise.all([mutate(), onChanged()]);
  const chip = CHIP_LABELS[data.chip];
  return (
    <Card>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-semibold">
          {formatDate(data.start_at)} · {formatRange(data.start_at, data.end_at)}
        </span>
        <Chip tone={chip.tone}>{chip.label}</Chip>
      </div>
      <StudentContext detail={data} />
      <DetailActions
        detail={data}
        onCancel={() => {
          setIsCancelling(true);
        }}
      />
      <hr className="my-4 border-ink/15" />
      <DetailResult detail={data} rules={rules} onSaved={refresh} />
      <CancelInterviewDialog
        slotId={isCancelling ? data.slot_id : null}
        studentName={data.student.name}
        onClose={() => {
          setIsCancelling(false);
        }}
        onDone={refresh}
      />
    </Card>
  );
}
