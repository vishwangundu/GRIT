import type { ReactElement } from 'react';

import { TONE_CLASSES, type Tone } from '@/lib/tones';
import { formatTime } from '@/lib/time';
import type { AvailabilitySlot } from '@/types/models';

const STYLE: Record<AvailabilitySlot['status'], { tone: Tone; label: string }> = {
  open: { tone: 'success', label: 'Open' },
  booked: { tone: 'info', label: 'Booked' },
  blocked: { tone: 'neutral', label: 'Blocked' },
  cancelled: { tone: 'neutral', label: 'Cancelled' },
};

interface Props {
  slot: AvailabilitySlot;
  onTap: (slot: AvailabilitySlot) => void;
}

/** Open → block, blocked → unblock, booked → cancel dialog. */
export function SlotChip({ slot, onTap }: Readonly<Props>): ReactElement {
  const style = STYLE[slot.status];
  const who = slot.student_first_name ? ` · ${slot.student_first_name}` : '';
  const isTappable = slot.status !== 'cancelled' && !(slot.status === 'booked' && !slot.booking_id);
  return (
    <button
      type="button"
      disabled={!isTappable}
      onClick={() => {
        onTap(slot);
      }}
      className={`min-h-10 rounded-lg border px-2 text-xs font-semibold disabled:cursor-default ${TONE_CLASSES[style.tone]} ${slot.status === 'cancelled' ? 'line-through opacity-60' : ''}`}
    >
      {formatTime(slot.start_at)} · {style.label}
      {who}
    </button>
  );
}
