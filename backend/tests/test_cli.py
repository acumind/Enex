"""Tests for CLI commands — create-admin and seed-stocks."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from app.cli import cli


def test_create_admin_calls_helper() -> None:
    """create-admin --email invokes _create_admin with the email."""
    runner = CliRunner()
    with patch("app.cli._create_admin", new_callable=AsyncMock) as mock_fn:
        result = runner.invoke(cli, ["create-admin", "--email", "admin@example.com"])

    assert result.exit_code == 0
    mock_fn.assert_awaited_once_with("admin@example.com")


def test_create_admin_requires_email() -> None:
    """create-admin without --email fails."""
    runner = CliRunner()
    result = runner.invoke(cli, ["create-admin"])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_seed_stocks_default_path() -> None:
    """seed-stocks without --csv-path uses default CSV path."""
    runner = CliRunner()
    with patch("app.cli._seed_stocks", new_callable=AsyncMock) as mock_fn:
        result = runner.invoke(cli, ["seed-stocks"])

    assert result.exit_code == 0
    mock_fn.assert_awaited_once()
    called_path = mock_fn.call_args[0][0]
    assert called_path.endswith("nse_top_200.csv")


def test_seed_stocks_custom_path() -> None:
    """seed-stocks --csv-path passes custom path."""
    runner = CliRunner()
    custom = str(Path("/tmp/custom_stocks.csv"))
    with patch("app.cli._seed_stocks", new_callable=AsyncMock) as mock_fn:
        result = runner.invoke(cli, ["seed-stocks", "--csv-path", custom])

    assert result.exit_code == 0
    mock_fn.assert_awaited_once_with(custom)
