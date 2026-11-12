import type { ReactElement, ReactNode } from 'react';

type Tone = 'primary' | 'danger' | 'neutral';

const TONES: Record<Tone, string> = {
  primary: 'text-grit-blue-strong hover:bg-select',
  danger: 'text-grit-red-strong hover:bg-[#fdecec]',
  neutral: 'text-ink-soft hover:bg-sand',
};

interface Props {
  /** Shown as the hover tooltip and read out by screen readers. */
  label: string;
  tone?: Tone;
  onClick: () => void;
  isDisabled?: boolean;
  children: ReactNode;
}

/** Square icon-only button for table row actions. */
export function IconButton({
  label,
  tone = 'primary',
  onClick,
  isDisabled = false,
  children,
}: Readonly<Props>): ReactElement {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isDisabled}
      aria-label={label}
      title={label}
      className={`inline-flex h-9 w-9 items-center justify-center rounded-lg transition disabled:cursor-not-allowed disabled:text-muted disabled:opacity-50 disabled:hover:bg-transparent ${TONES[tone]}`}
    >
      {children}
    </button>
  );
}
