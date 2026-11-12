import type { ReactElement } from 'react';

import type { Tracker } from '@/types/models';

type Badge = Tracker['badges'][number];

interface Props {
  badges: Tracker['badges'];
  value: number | null;
  onChange: (badgeId: number | null) => void;
}

interface Option {
  id: number | null;
  marker: string;
  label: string;
}

interface OptionProps {
  option: Option;
  group: string;
  isChecked: boolean;
  onPick: () => void;
}

/** Ladder step (tablet and up). A visually hidden radio gives arrow-key navigation and
 * screen-reader state for free; the styled spans react to it through `peer`. */
function Step({ option, group, isChecked, onPick }: Readonly<OptionProps>): ReactElement {
  return (
    <label className="relative z-10 flex shrink-0 cursor-pointer flex-col items-center gap-1.5">
      <input
        type="radio"
        name={group}
        checked={isChecked}
        onChange={onPick}
        className="peer sr-only"
      />
      <span className="flex h-9 min-w-9 items-center justify-center rounded-full border-2 border-line-strong bg-white px-2 text-sm font-bold text-ink-soft transition peer-checked:border-grit-blue-strong peer-checked:bg-grit-blue-strong peer-checked:text-white peer-hover:border-grit-blue-strong peer-focus-visible:ring-2 peer-focus-visible:ring-grit-blue-strong peer-focus-visible:ring-offset-2">
        {option.marker}
      </span>
      <span className="text-xs font-semibold whitespace-nowrap text-muted peer-checked:text-grit-blue-strong">
        {option.label}
      </span>
    </label>
  );
}

/** Compact pill for phones: number and name side by side, so all six fit in a 3×2 grid. */
function Pill({ option, group, isChecked, onPick }: Readonly<OptionProps>): ReactElement {
  return (
    <label className="flex min-h-11 cursor-pointer items-center gap-1.5 rounded-xl border-2 border-line-strong bg-white px-2 text-xs font-semibold text-ink-soft transition has-checked:border-grit-blue-strong has-checked:bg-grit-blue-strong has-checked:text-white has-focus-visible:ring-2 has-focus-visible:ring-grit-blue-strong has-focus-visible:ring-offset-2">
      <input type="radio" name={group} checked={isChecked} onChange={onPick} className="sr-only" />
      <span className="font-bold">{option.marker}</span>
      <span className="leading-tight">{option.label}</span>
    </label>
  );
}

function optionsFor(badges: readonly Badge[], tracks: readonly string[]): Option[] {
  const levels = badges.map((badge, index) => ({
    id: badge.id,
    marker: String(index + 1),
    label: tracks.length > 1 ? `${badge.track} · ${badge.name}` : badge.name,
  }));
  return [{ id: null, marker: 'All', label: 'Every badge' }, ...levels];
}

/** Badge filter drawn as the level ladder students see on their dashboard: All, then
 * each level in order, joined by a rail. On phones it becomes a 3×2 grid of pills. */
export function BadgeFilter({ badges, value, onChange }: Readonly<Props>): ReactElement {
  const tracks = [...new Set(badges.map((b) => b.track))];
  const options = optionsFor(badges, tracks);
  const pick = (option: Option) => (): void => {
    onChange(option.id);
  };
  return (
    // min-w-0: a fieldset otherwise refuses to shrink below its content and overflows on phones.
    <fieldset className="grit-panel w-full min-w-0 px-4 pt-3 pb-3">
      <legend className="sr-only">Filter by badge</legend>
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-2">
        <span className="text-xs font-semibold text-muted uppercase">Badge level</span>
        {tracks.length === 1 ? <span className="text-xs text-muted">{tracks.at(0)}</span> : null}
      </div>
      <div className="grid grid-cols-3 gap-2 sm:hidden">
        {options.map((option) => (
          <Pill
            key={option.marker}
            option={option}
            group="badge-filter-compact"
            isChecked={value === option.id}
            onPick={pick(option)}
          />
        ))}
      </div>
      <div className="relative hidden pb-1 sm:block">
        <div className="relative flex items-start justify-between gap-4">
          <span aria-hidden="true" className="absolute top-[18px] right-6 left-6 h-0.5 bg-line" />
          {options.map((option) => (
            <Step
              key={option.marker}
              option={option}
              group="badge-filter"
              isChecked={value === option.id}
              onPick={pick(option)}
            />
          ))}
        </div>
      </div>
    </fieldset>
  );
}
