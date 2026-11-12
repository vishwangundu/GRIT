import Link from 'next/link';
import type { ReactElement } from 'react';

import { AUTH_LINK, AuthFrame } from '@/components/shell/AuthFrame';
import { RegisterForm } from '@/components/shell/RegisterForm';

export default function RegisterPage(): ReactElement {
  return (
    <AuthFrame
      title={
        <>
          Create your <span className="text-navy">GRIT account</span>
        </>
      }
      subtitle="For NIAT students. Interviewers and the interview team are added by GRIT."
      footer={
        <>
          Already registered?{' '}
          <Link href="/login" className={AUTH_LINK}>
            Sign in
          </Link>
        </>
      }
    >
      <RegisterForm />
    </AuthFrame>
  );
}
