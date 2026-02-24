import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    predictor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("predictors.id"), nullable=False)
    stock_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)

    target_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_at_prediction: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    default_eval_date: Mapped[date] = mapped_column(Date, nullable=False)

    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_archive_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    raw_quote: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(30), server_default="manual", nullable=False)
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="pending_review", nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_predictions_predictor", "predictor_id", prediction_date.desc()),
        Index("idx_predictions_stock", "stock_id", prediction_date.desc()),
        Index("idx_predictions_status", "status"),
        Index("idx_predictions_date", prediction_date.desc()),
        Index(
            "idx_predictions_approved_pending",
            "default_eval_date",
            postgresql_where=status == "approved",
        ),
    )


class PredictionOutcome(Base):
    __tablename__ = "prediction_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=False, unique=True
    )

    outcome_status: Mapped[str] = mapped_column(String(20), nullable=False)
    actual_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    highest_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    lowest_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    deviation_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)

    evaluated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    evaluation_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (Index("idx_outcomes_status", "outcome_status"),)


class PredictionSuggestion(Base):
    __tablename__ = "prediction_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False)
    promoted_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_suggestions_status", "status", created_at.desc()),)
