"""Email notification templates for Enex."""

SITE_URL = "https://enex.in"


def prediction_outcome_email(
    stock_symbol: str,
    stock_name: str,
    outcome_status: str,
) -> tuple[str, str]:
    """Return (subject, html_body) for a prediction outcome notification."""
    status_label = outcome_status.replace("_", " ").title()
    subject = f"Prediction outcome for {stock_symbol}: {status_label}"
    btn = (
        "display:inline-block;background:#2563eb;color:#fff;"
        "padding:10px 24px;border-radius:6px;text-decoration:none;font-size:14px"
    )
    html_body = f"""\
<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;">
  <h2 style="color:#0f172a;margin-bottom:16px;">Prediction Outcome</h2>
  <p style="color:#334155;font-size:16px;line-height:1.6;">
    A prediction for <strong>{stock_name} ({stock_symbol})</strong> has been evaluated.
  </p>
  <p style="color:#334155;font-size:16px;line-height:1.6;">
    Result: <strong style="color:#2563eb;">{status_label}</strong>
  </p>
  <p style="margin-top:24px;">
    <a href="{SITE_URL}/stock/{stock_symbol}" style="{btn}">
      View on Enex
    </a>
  </p>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:32px 0 16px;" />
  <p style="color:#94a3b8;font-size:12px;">
    You received this because you are watching {stock_symbol} on Enex.
    To stop receiving these emails, remove the stock from your watchlist.
  </p>
</div>"""
    return subject, html_body


def new_prediction_email(
    predictor_name: str,
    predictor_slug: str,
    stock_symbol: str,
    stock_name: str,
) -> tuple[str, str]:
    """Return (subject, html_body) for a new prediction notification."""
    subject = f"New prediction by {predictor_name} for {stock_symbol}"
    btn = (
        "display:inline-block;background:#2563eb;color:#fff;"
        "padding:10px 24px;border-radius:6px;text-decoration:none;font-size:14px"
    )
    html_body = f"""\
<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;">
  <h2 style="color:#0f172a;margin-bottom:16px;">New Prediction</h2>
  <p style="color:#334155;font-size:16px;line-height:1.6;">
    <strong>{predictor_name}</strong> made a new prediction for
    <strong>{stock_name} ({stock_symbol})</strong>.
  </p>
  <p style="margin-top:24px;">
    <a href="{SITE_URL}/predictor/{predictor_slug}" style="{btn}">
      View Analyst Profile
    </a>
  </p>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:32px 0 16px;" />
  <p style="color:#94a3b8;font-size:12px;">
    You received this because you follow {predictor_name} on Enex.
    To stop receiving these emails, unfollow the analyst.
  </p>
</div>"""
    return subject, html_body
