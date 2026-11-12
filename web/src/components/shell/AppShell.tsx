'use client';

import { usePathname, useRouter } from 'next/navigation';
import { type ReactElement, type ReactNode, useEffect } from 'react';

import { ErrorBox, Loading } from '@/components/ui/StateView';
import { useClearApiCache } from '@/hooks/use-api';
import { useMe } from '@/hooks/use-session';
import { isSignedOut } from '@/lib/api';
import { HOME_FOR_ROLE } from '@/lib/roles';
import { getSupabase } from '@/lib/supabase/client';
import type { Role } from '@/types/models';

import { type NavItem, PageNav } from './PageNav';
import { Wordmark } from './Wordmark';

export type { NavItem } from './PageNav';

interface Props {
  area: Role;
  nav: readonly NavItem[];
  children: ReactNode;
}

/** Signed-in frame. Hides other roles' areas; FastAPI still enforces every permission. */
export function AppShell({ area, nav, children }: Readonly<Props>): ReactElement {
  const router = useRouter();
  const pathname = usePathname();
  const { data: me, error } = useMe();
  const clearCache = useClearApiCache();

  useEffect(() => {
    if (me && me.role !== area) router.replace(HOME_FOR_ROLE[me.role]);
    if (isSignedOut(error)) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [me, error, area, router, pathname]);

  async function signOut(): Promise<void> {
    await getSupabase().auth.signOut();
    await clearCache();
    router.replace('/login');
  }

  return (
    <div className="min-h-dvh">
      <header className="sticky top-3 z-10 px-3">
        <div className="mx-auto flex max-w-7xl items-center gap-4 rounded-full bg-ink/90 px-5 py-3 text-white shadow-lg backdrop-blur">
          <span className="mr-auto">
            <Wordmark onDark />
          </span>
          <span className="hidden text-sm text-white/70 sm:inline">{me?.full_name}</span>
          <button
            type="button"
            onClick={() => void signOut()}
            className="min-h-9 text-sm font-semibold text-white underline-offset-4 hover:underline"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 pt-6 pb-10">
        {error && !isSignedOut(error) ? <ErrorBox error={error} /> : null}
        {!me && !error ? <Loading /> : null}
        {me?.role === area ? (
          <>
            <PageNav items={nav} />
            {children}
          </>
        ) : null}
      </main>
    </div>
  );
}
