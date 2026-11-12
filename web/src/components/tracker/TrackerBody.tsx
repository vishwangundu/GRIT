import type { ReactElement } from 'react';

import { Tabs } from '@/components/ui/Tabs';
import type { Tracker, TrackerTab } from '@/types/models';

import { AwaitingTable } from './AwaitingTable';
import { BookedTable } from './BookedTable';
import { NotBookedTable } from './NotBookedTable';
import { ResultsTable } from './ResultsTable';
import { TrackerTiles } from './TrackerTiles';

const TABS = [
  { key: 'notbooked', label: 'Not booked' },
  { key: 'booked', label: 'Booked' },
  { key: 'awaiting', label: 'Awaiting result' },
  { key: 'results', label: 'Results' },
] as const;

interface Props {
  data: Tracker;
  slowAfterDays: number;
  onTab: (tab: TrackerTab) => void;
  onChanged: () => Promise<unknown>;
}

function ActiveTable({
  data,
  slowAfterDays,
  onChanged,
}: Readonly<Omit<Props, 'onTab'>>): ReactElement {
  switch (data.tab) {
    case 'notbooked':
      return (
        <NotBookedTable
          rows={data.not_booked_rows}
          slowAfterDays={slowAfterDays}
          onChanged={onChanged}
        />
      );
    case 'booked':
      return <BookedTable rows={data.booked_rows} onChanged={onChanged} />;
    case 'awaiting':
      return <AwaitingTable rows={data.awaiting_rows} />;
    case 'results':
      return <ResultsTable rows={data.result_rows} onChanged={onChanged} />;
  }
}

export function TrackerBody(props: Readonly<Props>): ReactElement {
  const { data, onTab } = props;
  return (
    <>
      <TrackerTiles tiles={data.tiles} active={data.tab} onSelect={onTab} />
      <Tabs tabs={TABS} active={data.tab} onChange={onTab} label="Tracker tabs" />
      <ActiveTable {...props} />
    </>
  );
}
