import type { ReactElement, ReactNode } from 'react';

import { TONE_CLASSES, type Tone } from '@/lib/tones';

export function Chip({
  tone,
  children,
}: Readonly<{ tone: Tone; children: ReactNode }>): ReactElement {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}
