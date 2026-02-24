import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PredictorScorecard(Base):
    __tablename__ = "predictor_scorecards"

    predictor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("predictors.id"), primary_key=True)
    total_predictions: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    hits: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    misses: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    partial_hits: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    pending: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    accuracy_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    avg_deviation_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    avg_upside_predicted: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    best_sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    worst_sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sector_accuracy: Mapped[dict[str, float]] = mapped_column(JSONB, server_default="{}", nullable=False)
    streak_current: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    last_prediction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    __table_args__ = (
        Index(
            "idx_scorecards_accuracy",
            accuracy_pct.desc(),
            postgresql_where=total_predictions >= 10,
        ),
    )
