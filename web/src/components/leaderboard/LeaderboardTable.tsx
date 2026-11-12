import type { ReactElement } from 'react';

import { Chip } from '@/components/ui/Chip';
import type { LeaderboardRow } from '@/types/models';

function Row({ row }: Readonly<{ row: LeaderboardRow }>): ReactElement {
  return (
    <tr className={row.is_me ? 'bg-select font-semibold' : 'border-t border-ink/10'}>
      <td className="px-3 py-2">#{row.rank}</td>
      <td className="px-3 py-2">
        {row.name}
        {row.is_me ? <span className="ml-2 text-xs text-grit-blue-strong">(you)</span> : null}
        {row.is_paused ? (
          <span className="ml-2">
            <Chip tone="review">Paused</Chip>
          </span>
        ) : null}
      </td>
      <td className="hidden px-3 py-2 sm:table-cell">{row.campus}</td>
      <td className="px-3 py-2 text-right">{row.miles.toLocaleString('en-IN')}</td>
    </tr>
  );
}

export function LeaderboardTable({ rows }: Readonly<{ rows: LeaderboardRow[] }>): ReactElement {
  return (
    <div className="overflow-x-auto grit-panel">
      <table className="w-full text-sm">
        <thead className="text-left text-xs text-muted uppercase">
          <tr>
            <th scope="col" className="px-3 py-2">
              Rank
            </th>
            <th scope="col" className="px-3 py-2">
              Student
            </th>
            <th scope="col" className="hidden px-3 py-2 sm:table-cell">
              Campus
            </th>
            <th scope="col" className="px-3 py-2 text-right">
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
