import { describe, expect, it } from 'vitest';

import { profileDetailsSchema, signUpSchema } from './registration';

const valid = {
  full_name: 'Riya Kapoor',
  campus: 'Pune',
  batch: '2025',
  email: 'riya@demo.grit',
  password: 'longenough',
  confirm: 'longenough',
};

describe('signUpSchema', () => {
  it('accepts a complete form', () => {
    expect(signUpSchema.safeParse(valid).success).toBe(true);
  });

  it('rejects mismatched passwords on the confirm field', () => {
    const result = signUpSchema.safeParse({ ...valid, confirm: 'different' });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.path).toEqual(['confirm']);
  });

  it('rejects short passwords and bad emails', () => {
    expect(signUpSchema.safeParse({ ...valid, password: 'short', confirm: 'short' }).success).toBe(
      false,
    );
    expect(signUpSchema.safeParse({ ...valid, email: 'nope' }).success).toBe(false);
  });

  it('gives a friendly message when a select was never chosen', () => {
    const result = signUpSchema.safeParse({ ...valid, campus: undefined });
    expect(result.error?.issues[0]?.message).toBe('Pick your campus.');
  });

  it('reads profile details back from user metadata', () => {
    expect(
      profileDetailsSchema.safeParse({ full_name: 'Riya', campus: 'Pune', batch: '2025' }).success,
    ).toBe(true);
    expect(profileDetailsSchema.safeParse({}).success).toBe(false);
  });
});
