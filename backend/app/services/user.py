"""User business logic: role management, banning."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolation, NotFoundError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserResponse


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def list_users(
        self,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[UserResponse]:
        users = await self.repo.list_users(cursor=cursor, limit=limit + 1)
        has_more = len(users) > limit
        if has_more:
            users = users[:limit]

        items = [UserResponse.model_validate(u) for u in users]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[UserResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def change_role(self, user_id, new_role: str) -> UserResponse:  # type: ignore[no-untyped-def]
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        # Last-admin protection
        if user.role == "admin" and new_role != "admin":
            admin_count = await self.repo.count_admins()
            if admin_count <= 1:
                raise BusinessRuleViolation("Cannot demote the last admin")

        await self.repo.update(user, {"role": new_role})
        return UserResponse.model_validate(user)

    async def ban_user(self, user_id, ban_reason: str) -> UserResponse:  # type: ignore[no-untyped-def]
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        await self.repo.update(user, {"is_active": False, "ban_reason": ban_reason})
        return UserResponse.model_validate(user)

    async def unban_user(self, user_id) -> UserResponse:  # type: ignore[no-untyped-def]
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        await self.repo.update(user, {"is_active": True, "ban_reason": None})
        return UserResponse.model_validate(user)

    async def create_admin(self, email: str) -> User:
        """Create a user with admin role. Used by CLI."""
        existing = await self.repo.get_by_email(email)
        if existing is not None:
            if existing.role != "admin":
                await self.repo.update(existing, {"role": "admin"})
            return existing

        user = User(email=email, name="Admin", role="admin")
        return await self.repo.create(user)
