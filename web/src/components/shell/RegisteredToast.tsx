'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { type ReactElement, useCallback, useEffect, useState } from 'react';

import { Toast } from '@/components/ui/Toast';
import { REGISTERED_PARAM } from '@/lib/registration';

/** Shows "Registered successfully" once after sign-up, then drops the flag from the URL
 * so a reload doesn't show it again. */
export function RegisteredToast(): ReactElement | null {
  const router = useRouter();
  const params = useSearchParams();
  const hasFlag = params.get(REGISTERED_PARAM) === '1';
  const [isShown, setIsShown] = useState(hasFlag);

  useEffect(() => {
    if (hasFlag) router.replace('/login');
  }, [hasFlag, router]);

  const close = useCallback(() => {
    setIsShown(false);
  }, []);

  if (!isShown) return null;
  return <Toast message="Registered successfully. Sign in to continue." onClose={close} />;
}
