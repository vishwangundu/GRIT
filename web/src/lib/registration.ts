/** Sign-up validation and the details we keep in Supabase user_metadata until the
 * GRIT profile exists (covers projects that require email confirmation first). */
import { z } from 'zod';

const MIN_PASSWORD = 8;

/** A required field that may be missing from FormData (e.g. an unselected <select>). */
function required(message: string, min = 1): z.ZodString {
  return z.string({ error: message }).trim().min(min, message);
}

export const profileDetailsSchema = z.object({
  full_name: required('Enter your full name.', 2),
  campus: required('Pick your campus.'),
  batch: required('Pick your batch.'),
});

export const signUpSchema = profileDetailsSchema
  .extend({
    email: z.email('Enter a valid email address.'),
    password: z.string().min(MIN_PASSWORD, `Use at least ${String(MIN_PASSWORD)} characters.`),
    confirm: z.string(),
  })
  .refine((v) => v.password === v.confirm, {
    message: 'Passwords don’t match.',
    path: ['confirm'],
  });

export type SignUp = z.infer<typeof signUpSchema>;

/** Query flag the register flow adds to /login so the sign-in screen can confirm success. */
export const REGISTERED_PARAM = 'registered';
