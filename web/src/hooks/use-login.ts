'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { z } from 'zod';

import { ApiError, getJson } from '@/lib/api';
import { registerProfile } from '@/lib/endpoints/auth';
import { PATHS } from '@/lib/endpoints/paths';
import { profileDetailsSchema } from '@/lib/registration';
import { safeNextPath } from '@/lib/roles';
import { getSupabase } from '@/lib/supabase/client';
import type { Me } from '@/types/models';

import { useAction } from './use-action';
import { useClearApiCache } from './use-api';

const loginSchema = z.object({
  email: z.email('Enter a valid email address.'),
  password: z.string().min(1, 'Enter your password.'),
});

/** First sign-in after email confirmation: create the profile from the sign-up details. */
async function loadOrCreateProfile(): Promise<Me> {
  try {
    return await getJson<Me>(PATHS.me);
  } catch (err: unknown) {
    if (!(err instanceof ApiError) || err.code !== 'profile_not_found') throw err;
    const { data } = await getSupabase().auth.getUser();
    const details = profileDetailsSchema.safeParse(data.user?.user_metadata);
    if (!details.success) throw new Error('No GRIT profile found. Create an account first.');
    return registerProfile(details.data);
  }
}

export function useLogin(): {
  isBusy: boolean;
  error: string | null;
  signIn: (form: FormData) => void;
} {
  const router = useRouter();
  const params = useSearchParams();
  const action = useAction();
  const clearCache = useClearApiCache();
  const [formError, setFormError] = useState<string | null>(null);

  function signIn(form: FormData): void {
    const parsed = loginSchema.safeParse(Object.fromEntries(form));
    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? 'Check your details.');
      return;
    }
    setFormError(null);
    void action.run(async () => {
      const { error } = await getSupabase().auth.signInWithPassword(parsed.data);
      if (error) throw new Error('Email or password is incorrect.');
      await clearCache();
      const me = await loadOrCreateProfile();
      router.replace(safeNextPath(params.get('next'), me.role));
      return undefined;
    });
  }

  return { isBusy: action.isBusy, error: formError ?? action.error, signIn };
}
