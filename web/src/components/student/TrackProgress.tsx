import type { ReactElement } from 'react';

import { Card } from '@/components/ui/Card';
import type { LadderRung } from '@/types/models';

type Status = LadderRung['status'];

const RUNG: Record<Status, { label: string; dot: string; text: string }> = {
  earned: { label: 'Unlocked', dot: 'bg-grit-green text-white', text: 'text-grit-green' },
  current: {
    label: 'In progress',
    dot: 'bg-grit-blue-strong text-white ring-4 ring-select',
    text: 'text-grit-blue-strong',
  },
  under_review: {
    label: 'Under review',
    dot: 'bg-grit-purple text-white',
    text: 'text-grit-purple',
  },
  withdrawn: {
    label: 'Withdrawn',
    dot: 'bg-grit-red-strong text-white',
    text: 'text-grit-red-strong',
  },
  next: {
    label: 'Up next',
    dot: 'border-2 border-grit-blue-strong bg-white text-grit-blue-strong',
    text: 'text-grit-blue-strong',
  },
  locked: {
    label: 'Locked',
    dot: 'border border-line-strong bg-white text-muted',
    text: 'text-muted',
  },
};

const SHOWS_SKILLS: readonly Status[] = ['current', 'next'];
const PERCENT = 100;

function SkillBar({ done, total }: Readonly<{ done: number; total: number }>): ReactElement {
  const percent = total === 0 ? 0 : Math.round((done / total) * PERCENT);
  return (
    <div className="mt-2 flex items-center gap-3">
      <div
        className="h-1.5 flex-1 overflow-hidden rounded-full bg-sand"
        role="progressbar"
        aria-valuenow={done}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label="Skills cleared"
      >
        <div
          className="h-full rounded-full bg-grit-blue-strong"
          style={{ width: `${String(percent)}%` }}
        />
      </div>
      <span className="shrink-0 text-xs text-muted">
        {done} of {total} skills
      </span>
    </div>
  );
}

function SkillList({ rung }: Readonly<{ rung: LadderRung }>): ReactElement {
  return (
    <ul className="mt-3 flex flex-col gap-1.5 text-sm">
      {rung.skills.map((skill) => (
        <li key={skill.name} className="flex items-start gap-2">
          <span
            aria-hidden="true"
            className={`mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full text-[10px] ${
              skill.cleared ? 'bg-grit-green text-white' : 'border border-line-strong'
            }`}
          >
            {skill.cleared ? '✓' : ''}
          </span>
          <span className={skill.cleared ? '' : 'text-muted'}>
            {skill.name} <span className="text-muted">· Level {skill.min_level}</span>
            <span className="sr-only">{skill.cleared ? ' (cleared)' : ' (not cleared yet)'}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

function Rung({ rung, isLast }: Readonly<{ rung: LadderRung; isLast: boolean }>): ReactElement {
  const meta = RUNG[rung.status];
  const isActive = SHOWS_SKILLS.includes(rung.status);
  return (
    <li className="relative flex gap-4 pb-5 last:pb-0">
      {isLast ? null : (
        <span aria-hidden="true" className="absolute top-8 bottom-0 left-4 w-px bg-line" />
      )}
      <span
        aria-hidden="true"
        className={`relative flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${meta.dot}`}
      >
        {rung.status === 'earned' ? '✓' : rung.level_order}
      </span>
      <div className="min-w-0 flex-1 pt-1">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3">
          <h3 className={`text-base ${rung.status === 'locked' ? 'text-muted' : ''}`}>
            {rung.name}
          </h3>
          <span className={`text-xs font-semibold ${meta.text}`}>{meta.label}</span>
        </div>
        {isActive && rung.skills_total > 0 ? (
          <SkillBar done={rung.skills_done} total={rung.skills_total} />
        ) : null}
        {isActive ? <SkillList rung={rung} /> : null}
        {rung.status === 'current' && rung.skills_done === rung.skills_total ? (
          <p className="mt-2 text-xs text-muted">All skills cleared · interview step pending</p>
        ) : null}
      </div>
    </li>
  );
}

export function TrackProgress({ ladder }: Readonly<{ ladder: LadderRung[] }>): ReactElement {
  return (
    <Card title="Your badge track">
      <ol>
        {ladder.map((rung, index) => (
          <Rung key={rung.badge_id} rung={rung} isLast={index === ladder.length - 1} />
        ))}
      </ol>
    </Card>
  );
}
