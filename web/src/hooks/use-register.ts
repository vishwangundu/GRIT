'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { registerProfile } from '@/lib/endpoints/auth';
import { type SignUp, signUpSchema } from '@/lib/registration';
import { getSupabase } from '@/lib/supabase/client';

import { useAction } from './use-action';
import { useClearApiCache } from './use-api';

type FieldErrors = Partial<Record<keyof SignUp, string>>;

export function useRegister(): {
  isBusy: boolean;
  error: string | null;
  fieldErrors: FieldErrors;
  needsConfirmation: boolean;
  signUp: (form: FormData) => void;
} {
  const router = useRouter();
  const action = useAction();
  const clearCache = useClearApiCache();
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [needsConfirmation, setNeedsConfirmation] = useState(false);

  async function create(values: SignUp): Promise<void> {
    const details = { full_name: values.full_name, campus: values.campus, batch: values.batch };
    const { data, error } = await getSupabase().auth.signUp({
      email: values.email,
      password: values.password,
      options: { data: details },
    });
    if (error) throw new Error(error.message);
    if (!data.session) {
      setNeedsConfirmation(true);
      return;
    }
    await clearCache();
    await registerProfile(details);
    router.replace('/student');
  }

  function signUp(form: FormData): void {
    const parsed = signUpSchema.safeParse(Object.fromEntries(form));
    if (!parsed.success) {
      const errors: FieldErrors = {};
      for (const issue of parsed.error.issues) {
        const key = issue.path[0] as keyof SignUp;
        errors[key] ??= issue.message;
      }
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    void action.run(async () => {
      await create(parsed.data);
      return undefined;
    });
  }

  return { isBusy: action.isBusy, error: action.error, fieldErrors, needsConfirmation, signUp };
}
