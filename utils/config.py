"""
Startup configuration validation.

Checks that required and recommended environment variables are set
before the application starts processing requests.
"""

import os
import logging

logger = logging.getLogger("leadfactory.config")

REQUIRED_VARS = {
    "LEADFACTORY_SECRET_KEY": (
        "JWT signing key — without this, all tokens are invalidated on every restart"
    ),
}

RECOMMENDED_VARS = {
    "DATABASE_URL": "Database connection string (defaults to SQLite)",
    "STRIPE_SECRET_KEY": "Required for billing features",
    "HUNTER_API_KEY": "Required for email waterfall verification (Hunter.io)",
    "ZEROBOUNCE_API_KEY": "Required for email waterfall verification (ZeroBounce)",
}


def validate_config() -> list[str]:
    """Check required and recommended env vars. Returns list of warnings."""
    warnings: list[str] = []
    for var, desc in REQUIRED_VARS.items():
        if not os.getenv(var):
            warnings.append(f"MISSING REQUIRED: {var} — {desc}")
    for var, desc in RECOMMENDED_VARS.items():
        if not os.getenv(var):
            warnings.append(f"MISSING RECOMMENDED: {var} — {desc}")
    return warnings
