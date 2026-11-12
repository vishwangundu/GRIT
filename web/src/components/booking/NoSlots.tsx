'use client';

import { type ReactElement, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { Empty } from '@/components/ui/StateView';

/** PRD section 9: empty state with "Tell me when one opens" (waitlist is out of scope). */
export function NoSlots(): ReactElement {
  const [isAsked, setIsAsked] = useState(false);
  return (
    <Empty>
      <p className="mb-3">No open slots in the next 14 days.</p>
      {isAsked ? (
        <p role="status" className="font-semibold">
          Thanks. Check back soon: the interview team is adding slots.
        </p>
      ) : (
        <Button
          variant="secondary"
          onClick={() => {
            setIsAsked(true);
          }}
        >
          Tell me when one opens
        </Button>
      )}
    </Empty>
  );
}
