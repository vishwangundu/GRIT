import type { ReactElement, ReactNode } from 'react';

import { Skyline } from '@/components/shell/Skyline';

/** Sign-in screens: the blue wash from grit.niatindia.com, with a skyline of landmarks
 * from GRIT destination countries pinned to the bottom of the window, behind the form. */
export default function AuthLayout({ children }: Readonly<{ children: ReactNode }>): ReactElement {
  return (
    <div className="min-h-dvh bg-gradient-to-b from-white to-wash">
      <Skyline />
      <div className="relative z-10 flex min-h-dvh flex-col">{children}</div>
    </div>
  );
}
