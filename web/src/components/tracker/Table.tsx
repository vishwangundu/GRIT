import type { ReactElement, ReactNode } from 'react';

import { Empty } from '@/components/ui/StateView';

interface Props {
  headers: readonly string[];
  isEmpty: boolean;
  emptyText: string;
  children: ReactNode;
}

export function Table({ headers, isEmpty, emptyText, children }: Readonly<Props>): ReactElement {
  if (isEmpty) return <Empty>{emptyText}</Empty>;
  return (
    <div className="overflow-x-auto grit-panel">
      <table className="w-full min-w-[40rem] text-sm">
        <thead className="text-left text-xs text-muted uppercase">
          <tr>
            {headers.map((h) => (
              <th key={h} scope="col" className="px-3 py-2">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export const CELL = 'border-t border-ink/10 px-3 py-2 align-top';

export function StudentCell({
  name,
  campus,
}: Readonly<{ name: string; campus: string }>): ReactElement {
  return (
    <td className={CELL}>
      <span className="font-semibold">{name}</span>
      <span className="block text-xs text-muted">{campus}</span>
    </td>
  );
}
