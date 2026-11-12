import type { ReactElement, ReactNode } from 'react';

import { TONE_CLASSES, type Tone } from '@/lib/tones';

interface Props {
  title?: string;
  /** Header row tinted in the tone colour. */
  band?: ReactNode;
  tone?: Tone;
  children: ReactNode;
  className?: string;
}

export function Card({
  title,
  band,
  tone = 'neutral',
  children,
  className = '',
}: Readonly<Props>): ReactElement {
  return (
    <section className={`grit-panel overflow-hidden ${className}`}>
      {band ? (
        <div
          className={`flex flex-wrap items-center justify-between gap-2 border-b border-b-line px-4 py-2.5 text-sm font-semibold ${TONE_CLASSES[tone]}`}
        >
          {typeof band === 'string' ? <h2 className="text-base font-semibold">{band}</h2> : band}
        </div>
      ) : null}
      <div className="p-4 sm:p-5">
        {title ? <h2 className="mb-3 text-lg">{title}</h2> : null}
        {children}
      </div>
    </section>
  );
}
