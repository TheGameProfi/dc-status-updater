from typing import Literal

from pydantic import BaseModel, Field


RuntimeMode = Literal["auto", "paused", "static_custom", "static_list"]


class CreateListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class AddQuoteRequest(BaseModel):
    text: str = Field(min_length=1, max_length=128)


class RuntimeUpdateRequest(BaseModel):
    mode: RuntimeMode | None = None
    interval_seconds: int | None = Field(default=None, ge=15, le=86400)
    active_list: str | None = None


class StaticCustomRequest(BaseModel):
    text: str = Field(min_length=1, max_length=128)
    duration_seconds: int | None = Field(default=None, ge=15, le=86400)


class StaticListRequest(BaseModel):
    list_name: str | None = None
    quote_index: int | None = Field(default=None, ge=0)
    duration_seconds: int | None = Field(default=None, ge=15, le=86400)
