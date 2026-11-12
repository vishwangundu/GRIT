'use client';

import { useEffect, useState } from 'react';

const DEFAULT_TICK_MS = 30_000;

/** Current time that re-renders every tick, so render functions stay pure. */
export function useNow(tickMs: number = DEFAULT_TICK_MS): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => {
      setNow(new Date());
    }, tickMs);
    return () => {
      clearInterval(id);
    };
  }, [tickMs]);
  return now;
}
