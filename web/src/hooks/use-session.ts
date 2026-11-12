'use client';

import type { SWRResponse } from 'swr';

import { useApi } from '@/hooks/use-api';
import type { ApiError } from '@/lib/api';
import { PATHS } from '@/lib/endpoints/paths';
import type { Me, Rules } from '@/types/models';

export function useMe(): SWRResponse<Me, ApiError> {
  return useApi<Me>(PATHS.me);
}

/** Business constants from FastAPI (never hard-coded in the UI). */
export function useRules(): SWRResponse<Rules, ApiError> {
  return useApi<Rules>(PATHS.rules);
}
