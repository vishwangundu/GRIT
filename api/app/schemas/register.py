"""Student self-registration."""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    campus: str = Field(min_length=1, max_length=50)
    batch: str = Field(min_length=1, max_length=10)


class RegistrationOptions(BaseModel):
    campuses: list[str]
    batches: list[str]
