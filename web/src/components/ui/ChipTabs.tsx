import type { ReactElement } from 'react';

export interface ChipOption<K extends string> {
  key: K;
  label: string;
  /** Optional count shown in a small badge inside the chip. */
  count?: number;
}

interface Props<K extends string> {
  options: readonly ChipOption<K>[];
  value: K;
  onChange: (key: K) => void;
  /** Names the group for screen readers, e.g. "Leaderboard tier". */
  label: string;
}

/** A row of pill buttons for switching views; the selected one is filled GRIT blue. */
export function ChipTabs<K extends string>({
  options,
  value,
  onChange,
  label,
}: Readonly<Props<K>>): ReactElement {
  return (
    <div role="group" aria-label={label} className="flex shrink-0 flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option.key}
          type="button"
          aria-pressed={value === option.key}
          onClick={() => {
            onChange(option.key);
          }}
          className="inline-flex min-h-9 items-center gap-2 rounded-full border border-line-strong bg-white px-3.5 text-sm font-semibold text-ink-soft transition hover:border-grit-blue-strong aria-pressed:border-grit-blue-strong aria-pressed:bg-grit-blue-strong aria-pressed:text-white"
        >
          {option.label}
          {option.count === undefined ? null : (
            <span className="rounded-full bg-ink/10 px-1.5 text-xs">{option.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}
