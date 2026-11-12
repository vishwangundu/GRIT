import type { ReactElement, ReactNode } from 'react';

import type { ApiError } from '@/lib/api';

import { Button } from './Button';

export function Loading({ label = 'Loading…' }: Readonly<{ label?: string }>): ReactElement {
  return (
    <div
      role="status"
      className="animate-pulse rounded-2xl border-2 border-dashed border-[#bbb] bg-white p-6 text-sm text-muted"
    >
      {label}
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
