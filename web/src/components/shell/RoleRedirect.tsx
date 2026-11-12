'use client';

import { useRouter } from 'next/navigation';
import { type ReactElement, useEffect } from 'react';

import { ErrorBox, Loading } from '@/components/ui/StateView';
import { useMe } from '@/hooks/use-session';
import { isSignedOut } from '@/lib/api';
import { HOME_FOR_ROLE } from '@/lib/roles';

export function RoleRedirect(): ReactElement {
  const router = useRouter();
  const { data, error } = useMe();

  useEffect(() => {
    if (data) router.replace(HOME_FOR_ROLE[data.role]);
    if (isSignedOut(error)) router.replace('/login');
  }, [data, error, router]);

  if (error && !isSignedOut(error)) return <ErrorBox error={error} />;
  return <Loading label="Opening GRIT…" />;
}
