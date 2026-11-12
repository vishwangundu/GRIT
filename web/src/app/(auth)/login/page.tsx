import Link from 'next/link';
import { type ReactElement, Suspense } from 'react';

import { AUTH_LINK, AuthFrame } from '@/components/shell/AuthFrame';
import { LoginForm } from '@/components/shell/LoginForm';
import { Loading } from '@/components/ui/StateView';

export default function LoginPage(): ReactElement {
  return (
    <AuthFrame
      title={
        <>
          Level Clearance <span className="text-navy">Interviews</span>
        </>
      }
      subtitle="Sign in to your GRIT Dashboard."
      footer={
        <>
          New to GRIT?{' '}
          <Link href="/register" className={AUTH_LINK}>
            Create a student account
          </Link>
        </>
      }
    >
      <Suspense fallback={<Loading />}>
        <LoginForm />
      </Suspense>
    </AuthFrame>
  );
}
