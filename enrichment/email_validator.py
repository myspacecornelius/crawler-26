"""
CRAWL — Email Validator
Validates email addresses via format checks and MX record lookups.
"""

import re
import asyncio
from typing import Optional


# ── Known disposable/temporary email domains ──
DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwaway.email", "guerrillamail.com", "mailinator.com",
    "yopmail.com", "trashmail.com", "fakeinbox.com", "sharklasers.com",
    "grr.la", "dispostable.com", "10minutemail.com",
}

# ── Known generic/role-based prefixes (lower priority) ──
ROLE_PREFIXES = {
    "info", "contact", "hello", "admin", "support", "team", "office",
    "press", "media", "sales", "marketing", "noreply", "no-reply",
}


class EmailValidator:
    """
    Multi-layer email validation:
    1. Format validation (regex)
    2. Disposable domain detection
    3. Role-based address detection
    4. MX record verification (async DNS lookup)
    """

    def __init__(self):
        self._mx_cache: dict[str, bool] = {}  # domain → has_mx
        self._pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )

    def validate(self, email: str) -> dict:
        """
        Validate an email address.
        
        Returns:
            {
                "email": str,
                "valid_format": bool,
                "is_disposable": bool,
                "is_role_based": bool,
                "quality": "high" | "medium" | "low" | "invalid"
            }
        """
        result = {
            "email": email,
            "valid_format": False,
            "is_disposable": False,
            "is_role_based": False,
            "quality": "invalid",
        }

        if not email or email == "N/A":
            return result

        email = email.strip().lower()

        # Format check
        if not self._pattern.match(email):
            return result
        result["valid_format"] = True

        local, domain = email.rsplit("@", 1)

        # Disposable check
        if domain in DISPOSABLE_DOMAINS:
            result["is_disposable"] = True
            result["quality"] = "low"
            return result

        # Role-based check
        if local in ROLE_PREFIXES:
            result["is_role_based"] = True
            result["quality"] = "medium"
            return result

        result["quality"] = "high"
        return result

    async def verify_mx(self, email: str) -> bool:
        """
        Check if the email's domain has valid MX records.
        Uses async DNS resolution with caching.
        """
        if not email or "@" not in email:
            return False

        domain = email.rsplit("@", 1)[1].lower()

        # Check cache
        if domain in self._mx_cache:
            return self._mx_cache[domain]

        try:
            import dns.resolver
            
            loop = asyncio.get_event_loop()
            answers = await loop.run_in_executor(
                None, lambda: dns.resolver.resolve(domain, "MX")
            )
            has_mx = len(answers) > 0
        except Exception:
            # If dns.resolver not available or lookup fails, assume valid
            # (we don't want to reject emails just because DNS is slow)
            has_mx = True

        self._mx_cache[domain] = has_mx
        return has_mx

    async def validate_batch(self, emails: list[str]) -> list[dict]:
        """Validate a batch of emails concurrently."""
        results = []
        for email in emails:
            result = self.validate(email)
            if result["valid_format"]:
                result["has_mx"] = await self.verify_mx(email)
            else:
                result["has_mx"] = False
            results.append(result)
        return results

    @property
    def cache_stats(self) -> dict:
        return {
            "domains_cached": len(self._mx_cache),
            "domains_with_mx": sum(1 for v in self._mx_cache.values() if v),
        }
