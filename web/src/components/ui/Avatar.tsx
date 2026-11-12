import type { ReactElement, ReactNode } from 'react';

import { initialsOf } from '@/lib/initials';

const SIZES = {
  sm: 'h-7 w-7 text-[11px]',
  md: 'h-8 w-8 text-xs',
  lg: 'h-11 w-11 text-sm',
} as const;

const LOOKS = {
  /** On the dark header. */
  solid: 'bg-grit-blue-strong text-white ring-2 ring-white/20',
  /** On light screens: a quiet tint so a column of avatars doesn't shout. */
  soft: 'bg-select text-grit-blue-strong',
} as const;

interface Props {
  name: string | null | undefined;
  size?: keyof typeof SIZES;
  look?: keyof typeof LOOKS;
}

/** Round initials badge (no photos are stored). Decorative: the name is always shown beside it. */
export function Avatar({ name, size = 'md', look = 'solid' }: Readonly<Props>): ReactElement {
  return (
    <span
      aria-hidden="true"
      title={name ?? undefined}
      className={`flex shrink-0 items-center justify-center rounded-full font-bold ${SIZES[size]} ${LOOKS[look]}`}
    >
      {initialsOf(name)}
    </span>
  );
}

interface PersonProps {
  name: string;
  /** Second line under the name, e.g. the campus. */
  detail?: ReactNode;
  size?: keyof typeof SIZES;
  nameClassName?: string;
}

/** A person's name with their initials avatar in front, for tables and lists. */
export function PersonName({
  name,
  detail,
  size = 'sm',
  nameClassName = 'font-semibold',
}: Readonly<PersonProps>): ReactElement {
  return (
    <span className="flex items-center gap-2.5">
      <Avatar name={name} size={size} look="soft" />
      <span className="min-w-0">
        <span className={`block ${nameClassName}`}>{name}</span>
        {detail ? <span className="block text-xs font-normal text-muted">{detail}</span> : null}
      </span>
    </span>
  );
}
