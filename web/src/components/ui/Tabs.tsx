'use client';

import type { ReactElement } from 'react';

interface Tab<K extends string> {
  key: K;
  label: string;
}

interface Props<K extends string> {
  tabs: readonly Tab<K>[];
  active: K;
  onChange: (key: K) => void;
  label: string;
}

export function Tabs<K extends string>({
  tabs,
  active,
  onChange,
  label,
}: Readonly<Props<K>>): ReactElement {
  return (
    <div
      role="tablist"
      aria-label={label}
      className="flex shrink-0 gap-1 overflow-x-auto overflow-y-hidden shadow-[inset_0_-1px_0_var(--color-line)]"
    >
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          role="tab"
          aria-selected={tab.key === active}
          onClick={() => {
            onChange(tab.key);
          }}
          className={`min-h-10 border-b-2 px-3 text-sm font-semibold whitespace-nowrap ${
            tab.key === active
              ? 'border-grit-blue-strong text-grit-blue-strong'
              : 'border-transparent text-muted hover:text-ink'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
