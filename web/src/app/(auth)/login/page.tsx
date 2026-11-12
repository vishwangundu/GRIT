import Link from 'next/link';
import { type ReactElement, Suspense } from 'react';

import { AUTH_LINK, AuthFrame } from '@/components/shell/AuthFrame';
import { HelpButton } from '@/components/shell/HelpButton';
import { LoginForm } from '@/components/shell/LoginForm';
import { RegisteredToast } from '@/components/shell/RegisteredToast';
import { Loading } from '@/components/ui/StateView';

export default function LoginPage(): ReactElement {
  return (
    <>
      <div className="absolute top-4 right-4 z-20">
        <HelpButton />
      </div>
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
          <RegisteredToast />
          <LoginForm />
        </Suspense>
      </AuthFrame>
    </>
  );
}
