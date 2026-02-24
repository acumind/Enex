"""Predictor business logic: CRUD, slug generation, parent validation."""

import re
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolation, NotFoundError
from app.models.predictor import Predictor
from app.repositories.predictor import PredictorRepository
from app.schemas.common import PaginatedResponse
from app.schemas.predictor import PredictorCreate, PredictorResponse, PredictorUpdate

# Predictor types that can be parents
_ORG_TYPES = {"brokerage", "research_firm", "media_house"}


def _generate_slug(name: str) -> str:
    """Simple regex-based slug: lowercase, strip special chars, replace spaces with -."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


class PredictorService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = PredictorRepository(session)

    async def _unique_slug(self, base_slug: str) -> str:
        slug = base_slug
        suffix = 2
        while await self.repo.slug_exists(slug):
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        return slug

    async def create(self, data: PredictorCreate) -> PredictorResponse:
        # Validate parent
        if data.parent_id is not None:
            parent = await self.repo.get_by_id(data.parent_id)
            if parent is None:
                raise NotFoundError("Parent predictor not found")
            if parent.type not in _ORG_TYPES:
                raise BusinessRuleViolation(
                    f"Parent must be one of: {', '.join(sorted(_ORG_TYPES))}"
                )

        slug = await self._unique_slug(_generate_slug(data.name))

        predictor = Predictor(
            name=data.name,
            slug=slug,
            type=data.type,
            parent_id=data.parent_id,
            designation=data.designation,
            bio=data.bio,
            avatar_url=data.avatar_url,
            website=data.website,
            social_links=data.social_links,
            sebi_reg_no=data.sebi_reg_no,
        )
        predictor = await self.repo.create(predictor)
        return PredictorResponse.model_validate(predictor)

    async def update(self, predictor_id: uuid.UUID, data: PredictorUpdate) -> PredictorResponse:
        predictor = await self.repo.get_by_id(predictor_id)
        if predictor is None:
            raise NotFoundError("Predictor not found")

        update_data = data.model_dump(exclude_unset=True)

        # Re-generate slug if name changes
        if "name" in update_data:
            new_slug = _generate_slug(update_data["name"])
            if new_slug != predictor.slug:
                update_data["slug"] = await self._unique_slug(new_slug)

        await self.repo.update(predictor, update_data)
        return PredictorResponse.model_validate(predictor)

    async def get_by_slug(self, slug: str) -> PredictorResponse:
        predictor = await self.repo.get_by_slug(slug)
        if predictor is None:
            raise NotFoundError("Predictor not found")
        return PredictorResponse.model_validate(predictor)

    async def list_members(self, slug: str) -> list[PredictorResponse]:
        predictor = await self.repo.get_by_slug(slug)
        if predictor is None:
            raise NotFoundError("Predictor not found")
        members = await self.repo.list_members(predictor.id)
        return [PredictorResponse.model_validate(m) for m in members]

    async def get_predictions(
        self,
        slug: str,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse:  # type: ignore[type-arg]
        """Get predictions for a predictor. Delegates to PredictionRepository."""
        from app.repositories.prediction import PredictionRepository
        from app.schemas.prediction import PredictionResponse

        predictor = await self.repo.get_by_slug(slug)
        if predictor is None:
            raise NotFoundError("Predictor not found")

        pred_repo = PredictionRepository(self.repo.session)
        predictions = await pred_repo.list_by_predictor(
            predictor.id, cursor=cursor, limit=limit + 1
        )
        has_more = len(predictions) > limit
        if has_more:
            predictions = predictions[:limit]

        items = [PredictionResponse.model_validate(p) for p in predictions]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)
