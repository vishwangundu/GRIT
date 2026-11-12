'use client';

import { usePathname, useRouter } from 'next/navigation';
import { type ReactElement, type ReactNode, useEffect } from 'react';

import { Avatar } from '@/components/ui/Avatar';
import { ErrorBox, Loading } from '@/components/ui/StateView';
import { useClearApiCache } from '@/hooks/use-api';
import { useMe } from '@/hooks/use-session';
import { isSignedOut } from '@/lib/api';
import { HOME_FOR_ROLE } from '@/lib/roles';
import { getSupabase } from '@/lib/supabase/client';
import type { Role } from '@/types/models';

import { type NavItem, PageNav } from './PageNav';
import { SideNav } from './SideNav';
import { SignOutIcon } from './SignOutIcon';
import { Wordmark } from './Wordmark';

export type { NavItem } from './PageNav';

const SIDE_TITLES: Record<Role, string> = {
  student: 'Student',
  interviewer: 'Interviewer',
  admin: 'Interview team',
};

interface Props {
  area: Role;
  nav: readonly NavItem[];
  children: ReactNode;
  /** Extra header buttons shown before the user, e.g. the student's Messages bell. */
  headerActions?: ReactNode;
}

/** Signed-in frame. Hides other roles' areas; FastAPI still enforces every permission. */
export function AppShell({ area, nav, children, headerActions }: Readonly<Props>): ReactElement {
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

  const isMine = me?.role === area;

  return (
    <div className="min-h-dvh lg:flex lg:h-dvh lg:flex-col lg:overflow-hidden">
      <ShellHeader
        name={me?.full_name}
        actions={isMine ? headerActions : null}
        onSignOut={() => void signOut()}
      />
      <main className="px-4 pt-6 pb-10 lg:flex lg:min-h-0 lg:flex-1 lg:flex-col lg:px-6 lg:pb-6">
        {error && !isSignedOut(error) ? <ErrorBox error={error} /> : null}
        {!me && !error ? <Loading /> : null}
        {isMine ? (
          <Sections title={SIDE_TITLES[area]} nav={nav} onSignOut={() => void signOut()}>
            {children}
          </Sections>
        ) : null}
      </main>
    </div>
  );
}

/** Dark pill nav: wordmark, role-specific buttons, the user, sign out. */
function ShellHeader({
  name,
  actions,
  onSignOut,
}: Readonly<{
  name: string | undefined;
  actions: ReactNode;
  onSignOut: () => void;
}>): ReactElement {
  return (
    <header className="sticky top-3 z-10 px-3">
      <div className="flex items-center gap-4 rounded-full bg-ink/90 px-5 py-3 text-white shadow-lg backdrop-blur">
        <span className="mr-auto">
          <Wordmark onDark />
        </span>
        {actions}
        {name ? (
          <span className="flex items-center gap-2">
            <Avatar name={name} />
            <span className="hidden text-sm text-white/80 sm:inline">{name}</span>
          </span>
        ) : null}
        <button
          type="button"
          onClick={onSignOut}
          aria-label="Sign out"
          title="Sign out"
          className="flex h-9 w-9 items-center justify-center rounded-full text-white/80 transition hover:bg-white/15 hover:text-white"
        >
          <SignOutIcon />
        </button>
      </div>
    </header>
  );
}

/** Side nav beside the page on large screens; top tabs on phones and tablets. */
function Sections({
  title,
  nav,
  onSignOut,
  children,
}: Readonly<{
  title: string;
  nav: readonly NavItem[];
  onSignOut: () => void;
  children: ReactNode;
}>): ReactElement {
  return (
    <div className="lg:grid lg:min-h-0 lg:flex-1 lg:grid-cols-[13rem_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)] lg:gap-8">
      <aside className="hidden lg:block">
        <SideNav title={title} items={nav} onSignOut={onSignOut} />
      </aside>
      <div className="min-w-0 lg:flex lg:flex-col lg:overflow-y-auto">
        <div className="lg:hidden">
          <PageNav items={nav} />
        </div>
        {children}
      </div>
    </div>
  );
}
