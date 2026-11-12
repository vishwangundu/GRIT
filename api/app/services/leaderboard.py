"""Student leaderboard (FR-S5): top rows of a tier plus the student's own row."""

from app.core.rules import LEADERBOARD_TOP
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import leaderboard
from app.schemas.student import LeaderboardResponse, LeaderboardRow, TierParam


async def get_leaderboard(conn: Conn, actor: Actor, tier: TierParam) -> LeaderboardResponse:
    rows = await leaderboard.tier_rows(conn, tier == "qual", LEADERBOARD_TOP, actor.user_id)
    me = await leaderboard.standing(conn, actor.user_id)
    my_tier: TierParam | None = None
    if me is not None:
        my_tier = "qual" if me.is_qualiflyer else "pre"
    return LeaderboardResponse(
        tier=tier,
        rows=[
            LeaderboardRow(
                rank=r.rank,
                name=r.full_name,
                campus=r.campus,
                miles=r.miles,
                is_me=r.id == actor.user_id,
                is_paused=r.is_paused,
            )
            for r in rows
        ],
        my_tier=my_tier,
        my_rank=me.rank if me else None,
    )
