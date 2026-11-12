import type { ReactElement, ReactNode } from 'react';

interface Props {
  id: string;
  label: string;
  hint?: string;
  error?: string | null;
  children: ReactNode;
}

/** Label + control + hint/error, wired with aria-describedby by id convention. */
export function Field({ id, label, hint, error, children }: Readonly<Props>): ReactElement {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-semibold text-ink">
        {label}
      </label>
      {children}
      {hint ? (
        <p id={`${id}-hint`} className="text-xs text-muted">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${id}-error`} role="alert" className="text-xs font-medium text-grit-red-strong">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export const INPUT_CLASS =
  'min-h-10 rounded-lg border border-line-strong bg-white px-3 py-2 text-sm focus:border-grit-blue-strong';
