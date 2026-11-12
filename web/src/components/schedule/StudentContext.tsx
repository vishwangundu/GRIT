import type { ReactElement } from 'react';

import { Chip } from '@/components/ui/Chip';
import { RESULT_LABELS } from '@/lib/labels';
import { formatDate } from '@/lib/time';
import type { InterviewDetail } from '@/types/models';

export function StudentContext({ detail }: Readonly<{ detail: InterviewDetail }>): ReactElement {
  return (
    <div className="flex flex-col gap-3 text-sm">
      <div>
        <p className="text-lg font-bold">{detail.student.name}</p>
        <p className="text-muted">
          {detail.student.campus} · Batch {detail.student.batch} · {detail.badge_name} Badge
        </p>
      </div>
      <div>
        <h3 className="font-semibold">Skills cleared</h3>
        <ul className="mt-1 flex flex-wrap gap-1">
          {detail.skills.map((skill) => (
            <li key={skill.name}>
              <Chip tone="neutral">
                {skill.name} · L{skill.level}
              </Chip>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h3 className="font-semibold">Earlier attempts</h3>
        {detail.earlier_attempts.length === 0 ? (
          <p className="text-muted">First attempt.</p>
        ) : (
          <ul className="mt-1 flex flex-col gap-2">
            {detail.earlier_attempts.map((attempt) => (
              <li key={attempt.recorded_at} className="rounded-lg bg-sand p-2">
                <span className="font-semibold">{formatDate(attempt.start_at)}</span> ·{' '}
                {RESULT_LABELS[attempt.result].label}
                {attempt.feedback_to_student ? (
                  <p className="mt-1 italic">“{attempt.feedback_to_student}”</p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
