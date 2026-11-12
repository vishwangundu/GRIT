'use client';

import useSWR, { type SWRResponse, useSWRConfig } from 'swr';

import { type ApiError, getJson } from '@/lib/api';

/** SWR over a FastAPI GET path. Pass null to skip. `keepPrevious` keeps showing the last
 * response while a new path loads (filters, tabs), so the screen doesn't blank out. */
export function useApi<T>(
  path: string | null,
  refreshMs = 0,
  keepPrevious = false,
): SWRResponse<T, ApiError> {
  return useSWR<T, ApiError>(path, getJson, {
    refreshInterval: refreshMs,
    revalidateOnFocus: true,
    shouldRetryOnError: false,
    keepPreviousData: keepPrevious,
  });
}

/** Drops every cached API response. Call when the signed-in user changes, so one
 * account never sees (or is routed by) another account's cached data. */
export function useClearApiCache(): () => Promise<void> {
  const { mutate } = useSWRConfig();
  return async () => {
    await mutate(() => true, undefined, { revalidate: false });
  };
}
