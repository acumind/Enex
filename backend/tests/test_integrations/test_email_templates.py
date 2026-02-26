"""Tests for email notification templates."""

from app.integrations.email.templates import (
    new_prediction_email,
    prediction_outcome_email,
)


def test_prediction_outcome_email_contains_stock_info() -> None:
    subject, body = prediction_outcome_email("RELIANCE", "Reliance Industries", "hit")
    assert "RELIANCE" in subject
    assert "Hit" in subject
    assert "Reliance Industries" in body
    assert "RELIANCE" in body
    assert "enex.in/stock/RELIANCE" in body
    assert "watchlist" in body.lower()


def test_prediction_outcome_email_formats_status() -> None:
    subject, _ = prediction_outcome_email("TCS", "Tata Consultancy", "partial_hit")
    assert "Partial Hit" in subject


def test_new_prediction_email_contains_predictor_info() -> None:
    subject, body = new_prediction_email("Motilal Oswal", "motilal-oswal", "INFY", "Infosys")
    assert "Motilal Oswal" in subject
    assert "INFY" in subject
    assert "Motilal Oswal" in body
    assert "Infosys" in body
    assert "enex.in/predictor/motilal-oswal" in body
    assert "unfollow" in body.lower()


def test_templates_return_tuple() -> None:
    result1 = prediction_outcome_email("SYM", "Name", "miss")
    result2 = new_prediction_email("Analyst", "analyst-slug", "SYM", "Name")
    assert isinstance(result1, tuple) and len(result1) == 2
    assert isinstance(result2, tuple) and len(result2) == 2
    assert isinstance(result1[0], str) and isinstance(result1[1], str)
    assert isinstance(result2[0], str) and isinstance(result2[1], str)
