'use client';

import { type ReactElement, useState } from 'react';

const COPIED_FEEDBACK_MS = 1500;

interface Props {
  command: string;
}

/** One shell command with a copy button. */
export function CommandBlock({ command }: Readonly<Props>): ReactElement {
  const [isCopied, setIsCopied] = useState(false);

  const copy = (): void => {
    void navigator.clipboard.writeText(command).then(() => {
      setIsCopied(true);
      window.setTimeout(() => {
        setIsCopied(false);
      }, COPIED_FEEDBACK_MS);
    });
  };

  return (
    <div className="flex items-start gap-2 rounded-lg border border-line bg-sand px-3 py-2">
      <code className="min-w-0 flex-1 font-mono text-xs break-all whitespace-pre-wrap text-ink">
        {command}
      </code>
      <button
        type="button"
        onClick={copy}
        className="shrink-0 rounded-md px-2 py-0.5 text-xs font-semibold text-grit-blue-strong hover:bg-select"
        aria-label={`Copy command: ${command}`}
      >
        {isCopied ? 'Copied' : 'Copy'}
      </button>
    </div>
  );
}
