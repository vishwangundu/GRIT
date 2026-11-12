import type { ReactElement } from 'react';

import { PersonName } from '@/components/ui/Avatar';
import { Chip } from '@/components/ui/Chip';
import type { LeaderboardRow } from '@/types/models';

function Row({ row }: Readonly<{ row: LeaderboardRow }>): ReactElement {
  return (
    <tr className={row.is_me ? 'bg-select font-semibold' : 'border-t border-ink/10'}>
      <td className="px-3 py-2">#{row.rank}</td>
      <td className="px-3 py-2">
        <span className="flex flex-wrap items-center gap-2">
          <PersonName name={row.name} nameClassName="" />
          {row.is_me ? <span className="text-xs text-grit-blue-strong">(you)</span> : null}
          {row.is_paused ? <Chip tone="review">Paused</Chip> : null}
        </span>
      </td>
      <td className="hidden px-3 py-2 sm:table-cell">{row.campus}</td>
      <td className="px-3 py-2 text-right">{row.miles.toLocaleString('en-IN')}</td>
    </tr>
  );
}

export function LeaderboardTable({ rows }: Readonly<{ rows: LeaderboardRow[] }>): ReactElement {
  return (
    <div className="grit-scroll overflow-x-auto grit-panel">
      <table className="w-full text-sm">
        <thead className="bg-ink text-left text-xs tracking-wide text-white/85 uppercase">
          <tr>
            <th scope="col" className="px-3 py-3.5 font-semibold">
              Rank
            </th>
            <th scope="col" className="px-3 py-3.5 font-semibold">
              Student
            </th>
            <th scope="col" className="hidden px-3 py-3.5 font-semibold sm:table-cell">
              Campus
            </th>
            <th scope="col" className="px-3 py-3.5 font-semibold text-right">
              Miles
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <Row key={`${String(row.rank)}-${row.name}`} row={row} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
