"""SMS delivery protocol — interface for swappable SMS providers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SMSProtocol(Protocol):
    async def send_otp(self, phone: str, otp_code: str) -> bool: ...
