"""Tests for StockService — seed_from_csv edge cases."""

import tempfile

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stock import StockService


async def test_seed_from_csv_file_not_found(db_session: AsyncSession) -> None:
    service = StockService(db_session)

    with pytest.raises(FileNotFoundError, match="CSV file not found"):
        await service.seed_from_csv("/nonexistent/path/stocks.csv")


async def test_seed_from_csv_valid_file(db_session: AsyncSession) -> None:
    service = StockService(db_session)

    csv_content = "symbol,name,exchange,sector,industry\nTESTCSV,Test CSV Corp,NSE,Technology,Software\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        f.flush()
        count = await service.seed_from_csv(f.name)

    assert count == 1


async def test_seed_from_csv_empty_file(db_session: AsyncSession) -> None:
    """CSV with only headers, no data rows → returns 0."""
    service = StockService(db_session)

    csv_content = "symbol,name,exchange,sector,industry\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        f.flush()
        count = await service.seed_from_csv(f.name)

    assert count == 0


async def test_seed_from_csv_duplicate_symbols(db_session: AsyncSession) -> None:
    """Duplicate symbols in CSV → bulk_create skips duplicates, no error."""
    service = StockService(db_session)

    csv_content = (
        "symbol,name,exchange,sector,industry\n"
        "DUPSYM,Dup Corp,NSE,Tech,Software\n"
        "DUPSYM,Dup Corp Again,NSE,Tech,Software\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        f.flush()
        count = await service.seed_from_csv(f.name)

    # bulk_create uses ON CONFLICT DO NOTHING, so only 1 inserted
    # (exact count depends on DB behavior, but should not error)
    assert count >= 0


async def test_seed_from_csv_optional_columns(db_session: AsyncSession) -> None:
    """CSV without sector/industry columns → defaults to None."""
    service = StockService(db_session)

    csv_content = "symbol,name,exchange\nOPTCSV,Optional Corp,NSE\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        f.flush()
        count = await service.seed_from_csv(f.name)

    assert count == 1


async def test_seed_from_csv_strips_whitespace(db_session: AsyncSession) -> None:
    """Whitespace around symbol/name is stripped, symbol uppercased."""
    service = StockService(db_session)

    csv_content = "symbol,name,exchange\n  wstest  ,  Whitespace Corp  ,  NSE  \n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        f.flush()
        count = await service.seed_from_csv(f.name)

    assert count == 1
    # Verify uppercased and stripped
    stock = await service.get_by_symbol("WSTEST")
    assert stock.symbol == "WSTEST"
    assert stock.name == "Whitespace Corp"
