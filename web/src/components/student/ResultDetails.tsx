import type { ReactElement } from 'react';

import { ButtonLink } from '@/components/ui/ButtonLink';
import type { CardKind } from '@/lib/journey-card';
import { plural } from '@/lib/labels';
import { formatDate } from '@/lib/time';
import type { JourneyCard, OutcomeView, Stats } from '@/types/models';

interface Props {
  kind: CardKind;
  journey: JourneyCard;
  last: OutcomeView | null;
  stats: Stats;
  passMiles: number;
}

function Feedback({ last }: Readonly<{ last: OutcomeView | null }>): ReactElement | null {
  if (!last?.feedback_to_student) return null;
  return (
    <blockquote className="border-l-4 border-current pl-3 italic">
      From your interviewer: “{last.feedback_to_student}”
    </blockquote>
  );
}

function Rebook({ journey }: Readonly<{ journey: JourneyCard }>): ReactElement | null {
  if (!journey.next_bookable_at) return null;
  return (
    <p>
      You can book a new slot from <strong>{formatDate(journey.next_bookable_at)}</strong> ·{' '}
      {plural(journey.attempts_left, 'attempt')} left.
    </p>
  );
}

function Passed({
  last,
  stats,
  passMiles,
}: Readonly<Omit<Props, 'kind' | 'journey'>>): ReactElement {
  return (
    <div className="flex flex-col gap-3 text-sm">
      <p>
        <strong>+{passMiles} Miles</strong> added. You’re on the Qualiflyer leaderboard
        {stats.rank === null ? '' : ` at #${String(stats.rank)}`}.
      </p>
      <Feedback last={last} />
      <div>
        <ButtonLink href="/student/leaderboard" variant="secondary">
          View leaderboard
        </ButtonLink>
      </div>
    </div>
  );
}

function Retake({ journey, last }: Readonly<Pick<Props, 'journey' | 'last'>>): ReactElement {
  return (
    <div className="flex flex-col gap-2 text-sm">
      <p>This is not a fail, and it does not count against your attempts.</p>
      {last?.feedback_to_student ? (
        <p>
          What to prepare: <em>“{last.feedback_to_student}”</em>
        </p>
      ) : null}
      <Rebook journey={journey} />
    </div>
  );
}

function Failed({ journey, last }: Readonly<Pick<Props, 'journey' | 'last'>>): ReactElement {
  return (
    <div className="flex flex-col gap-2 text-sm">
      {last?.result === 'no_show' ? (
        <p>We didn’t see you in the call. This counts as one attempt.</p>
      ) : (
        <Feedback last={last} />
      )}
      <Rebook journey={journey} />
      <p className="font-semibold">Your skills stay cleared.</p>
    </div>
  );
}

export function ResultDetails(props: Readonly<Props>): ReactElement | null {
  if (props.kind === 'passed') return <Passed {...props} />;
  if (props.kind === 'retake') return <Retake journey={props.journey} last={props.last} />;
  if (props.kind === 'failed') return <Failed journey={props.journey} last={props.last} />;
  return <StatusNote kind={props.kind} journey={props.journey} passMiles={props.passMiles} />;
}

function StatusNote({
  kind,
  journey,
  passMiles,
}: Readonly<{
  kind: CardKind;
  journey: JourneyCard;
  passMiles: number;
}>): ReactElement | null {
  if (kind === 'locked') {
    return (
      <p className="text-sm">
        You’ve used all {journey.attempts_used} attempts for this badge. The interview team will
        contact you within 3 working days about next steps.
      </p>
    );
  }
  if (kind === 'under_review') {
    return (
      <p className="text-sm">
        Your badge stays on your profile while the interview team reviews a report, usually within 5
        working days. Your leaderboard position is paused.
      </p>
    );
  }
  if (kind === 'nullified') {
    return (
      <p className="text-sm">
        The badge and its {passMiles} Miles have been removed. To appeal, reply to the GRIT team
        within 7 days.
      </p>
    );
  }
  return null;
}
