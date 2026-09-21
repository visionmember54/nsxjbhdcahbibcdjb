from __future__ import annotations

from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PageParams:
    def __init__(self, limit: int = Query(default=20, ge=1, le=200), offset: int = Query(default=0, ge=0)):
        self.limit = limit
        self.offset = offset


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
