"""Service-key routes: eligibility recompute (skills service) and demo reset."""

import httpx
from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.db.session import Conn, get_conn
from app.deps.internal import require_internal_key
from app.schemas.internal import RecomputeRequest, RecomputeResponse, ResetResponse
from app.seed.run import seed_demo
from app.seed.users import LocalProvisioner, SupabaseProvisioner
from app.services import eligibility

router = APIRouter(
    prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal_key)]
)


@router.post("/eligibility/recompute")
async def recompute(body: RecomputeRequest, conn: Conn = Depends(get_conn)) -> RecomputeResponse:
    return await eligibility.recompute(conn, body.student_id)


@router.post("/demo/reset")
async def demo_reset(conn: Conn = Depends(get_conn)) -> ResetResponse:
    settings = get_settings()
    async with conn.transaction():
        if not settings.supabase_url:
            return await seed_demo(conn, LocalProvisioner(conn))
        async with httpx.AsyncClient(timeout=30) as client:
            return await seed_demo(conn, SupabaseProvisioner(settings, client))
