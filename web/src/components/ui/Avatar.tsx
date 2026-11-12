import type { ReactElement } from 'react';

import { initialsOf } from '@/lib/initials';

interface Props {
  name: string | null | undefined;
}

/** Round initials badge for the signed-in user (no photos are stored). */
export function Avatar({ name }: Readonly<Props>): ReactElement {
  return (
    <span
      aria-hidden="true"
      title={name ?? undefined}
      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-grit-blue-strong text-xs font-bold text-white ring-2 ring-white/20"
    >
      {initialsOf(name)}
    </span>
  );
}
