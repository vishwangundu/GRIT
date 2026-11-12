import type { ReactElement } from 'react';

import { RoleRedirect } from '@/components/shell/RoleRedirect';

export default function Home(): ReactElement {
  return (
    <main className="mx-auto max-w-md p-4">
      <RoleRedirect />
    </main>
  );
}
