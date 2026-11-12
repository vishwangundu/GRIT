"""Student inbox (FR-S4)."""

from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import notifications
from app.schemas.student import InboxResponse, MarkReadResponse, NotificationItem


async def get_inbox(conn: Conn, actor: Actor) -> InboxResponse:
    items = await notifications.list_for_user(conn, actor.user_id)
    return InboxResponse(
        items=[
            NotificationItem(
                id=n.id,
                template=n.template,
                title=n.title,
                body=n.body,
                tone=n.tone,
                created_at=n.created_at,
                is_read=n.read_at is not None,
            )
            for n in items
        ],
        unread_count=sum(1 for n in items if n.read_at is None),
    )


async def mark_all_read(conn: Conn, actor: Actor) -> MarkReadResponse:
    return MarkReadResponse(marked=await notifications.mark_all_read(conn, actor.user_id))
