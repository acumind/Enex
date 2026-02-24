"""Archive protocol — interface for swappable archival providers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ArchiveProtocol(Protocol):
    async def save_url(self, url: str) -> str | None: ...
