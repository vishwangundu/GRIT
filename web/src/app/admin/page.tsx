import { type ReactElement, Suspense } from 'react';

import { TrackerView } from '@/components/tracker/TrackerView';
import { Loading } from '@/components/ui/StateView';

export default function AdminPage(): ReactElement {
  return (
    <Suspense fallback={<Loading />}>
      <TrackerView />
    </Suspense>
  );
}
