'use client';

import { type ReactElement, type ReactNode, useEffect, useRef } from 'react';

const WIDTHS = { md: 'max-w-md', lg: 'max-w-2xl' } as const;

interface Props {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  size?: keyof typeof WIDTHS;
}

/** Native <dialog>: focus trapping, Escape to close and backdrop come from the browser.
 * The title stays put and only the body scrolls, so long forms can pin their actions with
 * a sticky footer (see DIALOG_FOOTER). */
export function Dialog({
  isOpen,
  title,
  onClose,
  children,
  size = 'md',
}: Readonly<Props>): ReactElement {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (isOpen && !dialog.open) dialog.showModal();
    if (!isOpen && dialog.open) dialog.close();
  }, [isOpen]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      aria-labelledby="dialog-title"
      className={`grit-panel m-auto max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] flex-col p-0 open:flex ${WIDTHS[size]}`}
    >
      <h2 id="dialog-title" className="shrink-0 border-b border-line px-5 py-4 text-xl">
        {title}
      </h2>
      <div className="min-h-0 overflow-y-auto px-5 pt-4 pb-5">{children}</div>
    </dialog>
  );
}

/** Actions row that stays visible at the bottom of a scrolling dialog body. */
export const DIALOG_FOOTER =
  'sticky bottom-0 -mx-5 -mb-5 mt-2 border-t border-line bg-white px-5 py-3';
