"""Response model for GET /me."""

from uuid import UUID

from pydantic import BaseModel

from app.core.rules import Role


class MeResponse(BaseModel):
    id: UUID
    role: Role
    full_name: str
    email: str
