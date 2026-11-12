import type { ReactElement } from 'react';

import { Field, INPUT_CLASS } from '@/components/ui/Field';
import { PasswordInput } from '@/components/ui/PasswordInput';
import type { SignUp } from '@/lib/registration';
import type { RegistrationOptions } from '@/types/models';

interface Props {
  options: RegistrationOptions;
  errors: Partial<Record<keyof SignUp, string>>;
}

/** ids are prefixed so they never clash with the sign-in form, which Next keeps mounted. */
const idFor = (name: keyof SignUp): string => `reg-${name}`;

function Choice(
  props: Readonly<{ name: keyof SignUp; label: string; items: string[]; error?: string }>,
): ReactElement {
  const id = idFor(props.name);
  return (
    <Field id={id} label={props.label} error={props.error}>
      <select id={id} name={props.name} defaultValue="" className={INPUT_CLASS}>
        <option value="" disabled>
          Select
        </option>
        {props.items.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </Field>
  );
}

export function RegisterFields({ options, errors }: Readonly<Props>): ReactElement {
  return (
    <>
      <Field id={idFor('full_name')} label="Full name" error={errors.full_name}>
        <input
          id={idFor('full_name')}
          name="full_name"
          autoComplete="name"
          className={INPUT_CLASS}
        />
      </Field>
      <Field id={idFor('email')} label="Email" error={errors.email}>
        <input
          id={idFor('email')}
          name="email"
          type="email"
          autoComplete="email"
          className={INPUT_CLASS}
        />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Choice name="campus" label="Campus" items={options.campuses} error={errors.campus} />
        <Choice name="batch" label="Batch" items={options.batches} error={errors.batch} />
      </div>
      <Field
        id={idFor('password')}
        label="Password"
        hint="At least 8 characters."
        error={errors.password}
      >
        <PasswordInput id={idFor('password')} name="password" autoComplete="new-password" />
      </Field>
      <Field id={idFor('confirm')} label="Confirm password" error={errors.confirm}>
        <PasswordInput id={idFor('confirm')} name="confirm" autoComplete="new-password" />
      </Field>
    </>
  );
}
