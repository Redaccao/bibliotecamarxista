from typing import TypeVar, Generic, List, Sequence
from pydantic import BaseModel
import math

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    total_pages: int


def paginate(items: Sequence, total: int, page: int, page_size: int) -> dict:
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    return {
        "items": list(items),
        "total": total,
        "page": page,
        "total_pages": total_pages,
    }
