'use client';

import type { ReactElement } from 'react';

import { Button } from '@/components/ui/Button';
import { Field, INPUT_CLASS } from '@/components/ui/Field';
import { PasswordInput } from '@/components/ui/PasswordInput';
import { InlineError } from '@/components/ui/StateView';
import { useLogin } from '@/hooks/use-login';

export function LoginForm(): ReactElement {
  const login = useLogin();
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        login.signIn(new FormData(event.currentTarget));
      }}
      noValidate
      className="flex flex-col gap-4"
    >
      <Field id="email" label="Email">
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          className={INPUT_CLASS}
        />
      </Field>
      <Field id="password" label="Password">
        <PasswordInput id="password" name="password" autoComplete="current-password" required />
      </Field>
      <InlineError message={login.error} />
      <Button type="submit" variant="navy" isBusy={login.isBusy}>
        Sign in
      </Button>
    </form>
  );
}
