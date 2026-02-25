"""Email delivery protocol — interface for swappable email providers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmailProtocol(Protocol):
    async def send_otp(self, to: str, otp_code: str) -> bool: ...

    async def send_notification(self, to: str, subject: str, html_body: str) -> bool: ...
