"""
CRAWL — Proxy Rotation Manager
Handles proxy rotation for requests to avoid IP-based blocking.
"""

import random
import yaml
from pathlib import Path
from typing import Optional


class ProxyManager:
    """
    Manages proxy rotation for browser contexts.
    
    Supports:
    - Provider-based proxies (BrightData, SmartProxy)
    - Custom proxy lists
    - Rotation modes: per_request, per_site, sticky_session
    """

    def __init__(self, config_path: str = "config/proxies.yaml"):
        self.config = self._load_config(config_path)
        self.enabled = self.config.get("enabled", False)
        self._current_proxy = None
        self._request_count = 0

    def _load_config(self, path: str) -> dict:
        config_file = Path(path)
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f) or {}
        return {"enabled": False}

    def get_proxy(self, site_name: str = "") -> Optional[dict]:
        """
        Get the next proxy to use based on rotation mode.
        
        Returns:
            Dict with 'server', 'username', 'password' for Playwright,
            or None if proxies are disabled.
        """
        if not self.enabled:
            return None

        rotation_mode = self.config.get("rotation", {}).get("mode", "per_request")

        if rotation_mode == "sticky_session" and self._current_proxy:
            return self._current_proxy

        if rotation_mode == "per_site" and self._current_proxy and site_name:
            # Reuse same proxy for entire site crawl
            return self._current_proxy

        # Build proxy from provider config
        creds = self.config.get("credentials", {})
        if creds.get("host"):
            country = random.choice(
                self.config.get("rotation", {}).get("country_targets", ["US"])
            )
            # BrightData format: add country and session to username
            session_id = random.randint(100000, 999999)
            proxy = {
                "server": f"http://{creds['host']}:{creds.get('port', 22225)}",
                "username": f"{creds.get('username', '')}-country-{country.lower()}-session-{session_id}",
                "password": creds.get("password", ""),
            }
            self._current_proxy = proxy
            self._request_count += 1
            return proxy

        # Fallback to proxy list
        fallback = self.config.get("fallback_proxies", [])
        if fallback:
            proxy_url = random.choice(fallback)
            # Parse proxy URL
            proxy = {"server": proxy_url}
            self._current_proxy = proxy
            return proxy

        return None

    def rotate(self):
        """Force rotation to a new proxy on next get_proxy() call."""
        self._current_proxy = None

    @property
    def stats(self) -> dict:
        return {
            "enabled": self.enabled,
            "provider": self.config.get("provider", "none"),
            "total_requests_proxied": self._request_count,
        }
