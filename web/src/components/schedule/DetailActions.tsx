'use client';

import type { ReactElement } from 'react';

import { Button } from '@/components/ui/Button';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { useNow } from '@/hooks/use-now';
import { formatTime } from '@/lib/time';
import type { InterviewDetail } from '@/types/models';

interface Props {
  detail: InterviewDetail;
  onCancel: () => void;
}

/** Join call (enabled 10 min before start until the end) and Cancel for upcoming ones. */
function JoinCall({ detail }: Readonly<{ detail: InterviewDetail }>): ReactElement {
  const now = useNow();
  if (detail.is_join_open && detail.meeting_link) {
    return (
      <ButtonLink href={detail.meeting_link} isExternal>
        Join call
      </ButtonLink>
    );
  }
  if (now >= new Date(detail.end_at)) return <Button disabled>Call ended</Button>;
  return <Button disabled>Join opens {formatTime(detail.join_opens_at)}</Button>;
}

export function DetailActions({ detail, onCancel }: Readonly<Props>): ReactElement {
  return (
    <div className="mt-4 flex flex-wrap gap-2">
      <JoinCall detail={detail} />
      {detail.can_cancel ? (
        <Button variant="ghost" onClick={onCancel}>
          Cancel interview
        </Button>
      ) : null}
    </div>
  );
}
