'use client';

import type { ReactElement } from 'react';

import { Button } from '@/components/ui/Button';
import { ErrorBox, InlineError, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { useRegister } from '@/hooks/use-register';
import { PATHS } from '@/lib/endpoints/paths';
import type { RegistrationOptions } from '@/types/models';

import { RegisterFields } from './RegisterFields';

export function RegisterForm(): ReactElement {
  const { data: options, error, mutate } = useApi<RegistrationOptions>(PATHS.registrationOptions);
  const register = useRegister();

  if (register.needsConfirmation) {
    return (
      <div role="status" className="flex flex-col gap-2 text-sm">
        <p className="text-base font-semibold">Check your inbox</p>
        <p>
          We sent a confirmation link to your email. Open it, then sign in: your student profile is
          set up on first sign-in.
        </p>
      </div>
    );
  }
  if (error) return <ErrorBox error={error} onRetry={() => void mutate()} />;
  if (!options) return <Loading label="Loading campuses…" />;
  return (
    <form
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        register.signUp(new FormData(event.currentTarget));
      }}
      className="flex flex-col gap-4"
    >
      <RegisterFields options={options} errors={register.fieldErrors} />
      <InlineError message={register.error} />
      <Button type="submit" variant="navy" isBusy={register.isBusy}>
        Create account
      </Button>
    </form>
  );
}
