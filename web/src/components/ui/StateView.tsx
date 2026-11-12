import type { ReactElement, ReactNode } from 'react';

import { CREST } from '@/components/shell/Wordmark';
import type { ApiError } from '@/lib/api';

import { Button } from './Button';

/** GRIT crest inside a turning ring. The label is for screen readers only. */
export function Loading({ label = 'Loading…' }: Readonly<{ label?: string }>): ReactElement {
  return (
    <div role="status" className="flex justify-center py-12">
      <span className="relative flex h-16 w-16 items-center justify-center">
        <span
          aria-hidden="true"
          className="absolute inset-0 rounded-full border-[3px] border-line border-t-grit-blue-strong motion-safe:animate-spin"
        />
        <svg
          viewBox="0 0 21 27"
          aria-hidden="true"
          focusable="false"
          className="h-7 w-auto text-ink motion-safe:animate-pulse"
        >
          <path d={CREST} fill="currentColor" />
        </svg>
      </span>
      <span className="sr-only">{label}</span>
    </div>
  );
}

export function Empty({ children }: Readonly<{ children: ReactNode }>): ReactElement {
  return (
    <div className="rounded-2xl border border-dashed border-line-strong bg-white p-6 text-center text-sm text-ink-soft">
      {children}
    </div>
  );
}

export function ErrorBox({
  error,
  onRetry,
}: Readonly<{
  error: ApiError | Error;
  onRetry?: () => void;
}>): ReactElement {
  return (
    <div role="alert" className="grit-panel bg-[#fdecec] p-4 text-sm text-[#94262b]">
      <p className="font-semibold">Something went wrong</p>
      <p className="mt-1">{error.message}</p>
      {onRetry ? (
        <Button variant="secondary" className="mt-3" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}

export function InlineError({
  message,
}: Readonly<{ message: string | null }>): ReactElement | null {
  if (!message) return null;
  return (
    <p role="alert" className="text-sm font-medium text-grit-red-strong">
      {message}
    </p>
  );
}
