'use client';

import { type ReactElement, useEffect } from 'react';

const TOAST_VISIBLE_MS = 5000;

interface Props {
  message: string;
  onClose: () => void;
}

/** Short success message pinned to the top of the screen; closes itself after a few seconds. */
export function Toast({ message, onClose }: Readonly<Props>): ReactElement {
  useEffect(() => {
    const timer = window.setTimeout(onClose, TOAST_VISIBLE_MS);
    return () => {
      window.clearTimeout(timer);
    };
  }, [onClose]);

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed top-4 left-1/2 z-50 flex w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 items-center gap-3 rounded-xl border border-line bg-white px-4 py-3 text-sm text-ink shadow-lg"
    >
      <span
        aria-hidden="true"
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-grit-green text-xs font-bold text-white"
      >
        ✓
      </span>
      <p className="flex-1 font-semibold">{message}</p>
      <button
        type="button"
        onClick={onClose}
        aria-label="Dismiss"
        className="rounded-md px-1.5 text-lg leading-none text-muted hover:bg-sand"
      >
        ×
      </button>
    </div>
  );
}
