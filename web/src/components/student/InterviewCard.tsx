import type { ReactElement } from 'react';

import { Card } from '@/components/ui/Card';
import { Chip } from '@/components/ui/Chip';
import { cardFor } from '@/lib/journey-card';
import { stateLabel } from '@/lib/labels';
import type { Dashboard, JourneyCard } from '@/types/models';

import { BookedTicket } from './BookedTicket';
import { ReadyDetails, SkillsLeft } from './ReadyDetails';
import { ResultDetails } from './ResultDetails';

interface Props {
  dashboard: Dashboard;
  journey: JourneyCard;
  passMiles: number;
  now: Date;
}

export function InterviewCard({
  dashboard,
  journey,
  passMiles,
  now,
}: Readonly<Props>): ReactElement {
  const { booking, last_outcome: last } = dashboard;
  const spec = cardFor(journey, booking, last, now);
  const rung = dashboard.ladder.find((r) => r.badge_id === journey.badge.id);
  return (
    <Card
      tone={spec.tone}
      band={
        <>
          <span>
            {journey.badge.track} · {journey.badge.name} Badge interview
          </span>
          <Chip tone={spec.tone}>{stateLabel(journey.effective_state)}</Chip>
        </>
      }
    >
      <h1 className="mb-3 text-2xl">{spec.title}</h1>
      {spec.kind === 'skills_left' ? <SkillsLeft rung={rung} /> : null}
      {spec.kind === 'ready' ? <ReadyDetails journey={journey} last={last} /> : null}
      {booking && (spec.kind === 'ticket' || spec.kind === 'live') ? (
        <BookedTicket journey={journey} booking={booking} isLive={spec.kind === 'live'} />
      ) : null}
      {spec.kind === 'result_pending' ? (
        <p className="text-sm">Interviewers record results within 24 hours. We’ll message you.</p>
      ) : null}
      <ResultDetails
        kind={spec.kind}
        journey={journey}
        last={last}
        stats={dashboard.stats}
        passMiles={passMiles}
      />
    </Card>
  );
}
