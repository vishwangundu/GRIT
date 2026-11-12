'use client';

import { useState } from 'react';

/** Runs one mutation at a time and keeps its error / success message.
 * ApiError messages come from FastAPI and are written for end users. */
export function useAction(): {
  isBusy: boolean;
  error: string | null;
  message: string | null;
  run: (action: () => Promise<string | undefined>) => Promise<boolean>;
  reset: () => void;
} {
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function run(action: () => Promise<string | undefined>): Promise<boolean> {
    setIsBusy(true);
    setError(null);
    setMessage(null);
    try {
      setMessage((await action()) ?? null);
      return true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'That action failed. Try again.');
      return false;
    } finally {
      setIsBusy(false);
    }
  }

  function reset(): void {
    setError(null);
    setMessage(null);
  }

  return { isBusy, error, message, run, reset };
}
