import type { ReactElement } from 'react';

import { ButtonLink } from '@/components/ui/ButtonLink';
import { Empty } from '@/components/ui/StateView';

export function NotEligible(): ReactElement {
  return (
    <Empty>
      <p className="mb-3">You can book once you’re interview-ready.</p>
      <ButtonLink href="/student" variant="secondary">
        Back to dashboard
      </ButtonLink>
    </Empty>
  );
}
