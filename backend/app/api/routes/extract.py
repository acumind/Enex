"""AI extraction routes (auth required)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_extraction_service
from app.core.rate_limit import extract_limiter
from app.schemas.extraction import ExtractionRequest, ExtractionResponse
from app.services.extraction import ExtractionService

router = APIRouter(prefix="/extract", tags=["extraction"])


@router.post("", response_model=ExtractionResponse)
async def extract_predictions(
    data: ExtractionRequest,
    _rate_limit: None = Depends(extract_limiter.dependency()),
    service: ExtractionService = Depends(get_extraction_service),
) -> ExtractionResponse:
    return await service.extract_from_url(data.url)
