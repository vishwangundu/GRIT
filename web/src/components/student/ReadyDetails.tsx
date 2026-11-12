import type { ReactElement } from 'react';

import { ButtonLink } from '@/components/ui/ButtonLink';
import { plural } from '@/lib/labels';
import type { JourneyCard, LadderRung, OutcomeView } from '@/types/models';

export function SkillsLeft({ rung }: Readonly<{ rung: LadderRung | undefined }>): ReactElement {
  const missing = rung?.skills.filter((s) => !s.cleared) ?? [];
  return (
    <div className="text-sm">
      <p>
        Clear these to unlock your interview ({rung?.skills_done ?? 0} of {rung?.skills_total ?? 0}{' '}
        done):
      </p>
      <ul className="mt-2 list-disc pl-5">
        {missing.map((skill) => (
          <li key={skill.name}>
            {skill.name} · Level {skill.min_level}
          </li>
        ))}
      </ul>
    </div>
  );
}

interface ReadyProps {
  journey: JourneyCard;
  last: OutcomeView | null;
}

export function ReadyDetails({ journey, last }: Readonly<ReadyProps>): ReactElement {
  const isRetry = last !== null && last.result !== 'pass';
  return (
    <div className="flex flex-col gap-3 text-sm">
      {journey.priority ? (
        <p>Your interviewer had to cancel. You’ll be first in line when new slots open.</p>
      ) : (
        <p>Book a 30-minute interview to unlock the {journey.badge.name} Badge.</p>
      )}
      {isRetry && last.feedback_to_student ? (
        <blockquote className="border-l-4 border-ink pl-3 italic">
          “{last.feedback_to_student}”
        </blockquote>
      ) : null}
      {isRetry ? <p>{plural(journey.attempts_left, 'attempt')} left.</p> : null}
      <div>
        <ButtonLink href="/student/book">Book interview</ButtonLink>
      </div>
    </div>
  );
}
