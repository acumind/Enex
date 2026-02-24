"""CLI commands for admin operations and data seeding."""

import asyncio
from pathlib import Path

import click

from app.core.database import async_session


async def _create_admin(email: str) -> None:
    from app.services.user import UserService

    async with async_session() as session:
        service = UserService(session)
        user = await service.create_admin(email)
        await session.commit()
        click.echo(f"Admin user ready: {user.email} (id={user.id})")


async def _seed_stocks(csv_path: str) -> None:
    from app.services.stock import StockService

    async with async_session() as session:
        service = StockService(session)
        count = await service.seed_from_csv(csv_path)
        await session.commit()
        click.echo(f"Inserted {count} new stocks from {csv_path}")


@click.group()
def cli() -> None:
    """Enex management CLI."""


@cli.command()
@click.option("--email", required=True, help="Admin user email address")
def create_admin(email: str) -> None:
    """Create or promote a user to admin role."""
    asyncio.run(_create_admin(email))


@cli.command()
@click.option(
    "--csv-path",
    default=str(Path(__file__).resolve().parent.parent / "data" / "nse_top_200.csv"),
    help="Path to CSV file with stock data",
)
def seed_stocks(csv_path: str) -> None:
    """Bulk insert stocks from a CSV file."""
    asyncio.run(_seed_stocks(csv_path))
