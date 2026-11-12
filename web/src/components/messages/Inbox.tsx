'use client';

import { type ReactElement, useEffect, useRef } from 'react';

import { Empty, ErrorBox, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { PATHS } from '@/lib/endpoints/paths';
import { markAllRead } from '@/lib/endpoints/student';
import { TONE_CLASSES, asTone } from '@/lib/tones';
import { formatDateTime } from '@/lib/time';
import type { Inbox as InboxData, NotificationItem } from '@/types/models';

function Message({ item }: Readonly<{ item: NotificationItem }>): ReactElement {
  return (
    <li className={`rounded-2xl border p-4 ${TONE_CLASSES[asTone(item.tone)]}`}>
      <div className="flex items-start justify-between gap-3">
        <h2 className="font-semibold">
          {item.is_read ? null : (
            <span
              className="mr-2 inline-block size-2 rounded-full bg-grit-red-strong align-middle"
              aria-hidden="true"
            />
          )}
          {item.title}
          {item.is_read ? null : <span className="sr-only"> (unread)</span>}
        </h2>
        <time dateTime={item.created_at} className="shrink-0 text-xs">
          {formatDateTime(item.created_at)}
        </time>
      </div>
      <p className="mt-2 text-sm whitespace-pre-line">{item.body}</p>
    </li>
  );
}

/** Opening the inbox marks everything read; dots stay visible until the next visit. */
export function Inbox(): ReactElement {
  const { data, error, mutate } = useApi<InboxData>(PATHS.notifications);
  const hasMarked = useRef(false);

  useEffect(() => {
    if (!data || data.unread_count === 0 || hasMarked.current) return;
    hasMarked.current = true;
    markAllRead()
      .then(() => mutate({ ...data, unread_count: 0 }, { revalidate: false }))
      .catch((err: unknown) => {
        console.error(err);
      });
  }, [data, mutate]);

  if (error) return <ErrorBox error={error} onRetry={() => void mutate()} />;
  if (!data) return <Loading label="Loading messages…" />;
  return (
    <div className="flex flex-col gap-3">
      <h1 className="text-3xl">Messages</h1>
      {data.items.length === 0 ? (
        <Empty>No messages yet.</Empty>
      ) : (
        <ul className="flex flex-col gap-3">
          {data.items.map((item) => (
            <Message key={item.id} item={item} />
          ))}
        </ul>
      )}
    </div>
  );
}
