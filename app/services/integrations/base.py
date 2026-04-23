"""Shared types for all outbound integrations."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DispatchItem:
    """Result of a single dispatch action (one ticket or one email)."""
    type: str                       # ticket | email
    ref: str                        # PROJ-123, email@domain.com, etc.
    url: Optional[str] = None       # Link to created ticket / None for email
    status: str = "success"         # success | failed
    error: Optional[str] = None


@dataclass
class DispatchResult:
    """Aggregate outcome of one integration run against one review job."""
    success: bool
    items: list[DispatchItem] = field(default_factory=list)
    error_message: Optional[str] = None

    @property
    def dispatched(self) -> int:
        return sum(1 for i in self.items if i.status == "success")

    @property
    def failed(self) -> int:
        return sum(1 for i in self.items if i.status == "failed")

    def to_json(self) -> list[dict]:
        return [
            {"type": i.type, "ref": i.ref, "url": i.url,
             "status": i.status, "error": i.error}
            for i in self.items
        ]


def mask_secret(value: str, visible: int = 4) -> str:
    """Return a masked credential string safe for API responses."""
    if not value or len(value) <= visible:
        return "***"
    return value[:visible] + "***"
