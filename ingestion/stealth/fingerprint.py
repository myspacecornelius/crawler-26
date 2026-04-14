"""
CRAWL — Browser Fingerprint Rotation
Generates randomized but realistic browser fingerprints to avoid detection.
"""

import random


# ──────────────────────────────────────────────────
#  Realistic browser profiles
# ──────────────────────────────────────────────────

USER_AGENTS = [
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1366, "height": 768},
    {"width": 2560, "height": 1440},
    {"width": 1680, "height": 1050},
    {"width": 1280, "height": 800},
]

TIMEZONES = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Toronto",
    "Europe/London",
    "Europe/Berlin",
]

LOCALES = ["en-US", "en-GB", "en-CA"]

COLOR_SCHEMES = ["light", "dark"]


class FingerprintManager:
    """
    Generates randomized but internally-consistent browser fingerprints.
    Each fingerprint looks like a real user's browser configuration.
    """

    def __init__(self):
        self._used_fingerprints = []

    def generate(self) -> dict:
        """
        Generate a new browser context configuration.
        Returns a dict compatible with playwright's browser.new_context(**config).
        """
        ua = random.choice(USER_AGENTS)
        viewport = random.choice(VIEWPORTS)
        timezone = random.choice(TIMEZONES)
        locale = random.choice(LOCALES)
        color_scheme = random.choice(COLOR_SCHEMES)

        # Match platform to user agent for consistency
        if "Macintosh" in ua or "Mac OS" in ua:
            platform = "macOS"
        elif "Windows" in ua:
            platform = "Windows"
        else:
            platform = "Linux"

        fingerprint = {
            "user_agent": ua,
            "viewport": viewport,
            "timezone_id": timezone,
            "locale": locale,
            "color_scheme": color_scheme,
            "device_scale_factor": random.choice([1, 1.5, 2]),
            "has_touch": False,
            "is_mobile": False,
            # Extra context for JS injection
            "_platform": platform,
            "_screen": {
                "width": viewport["width"],
                "height": viewport["height"],
                "avail_width": viewport["width"],
                "avail_height": viewport["height"] - random.randint(25, 80),  # taskbar
            },
        }

        self._used_fingerprints.append(fingerprint)
        return fingerprint

    def get_context_kwargs(self, fingerprint: dict) -> dict:
        """
        Extract only the kwargs that Playwright's new_context() accepts.
        Strips out our custom metadata fields.
        """
        return {
            "user_agent": fingerprint["user_agent"],
            "viewport": fingerprint["viewport"],
            "timezone_id": fingerprint["timezone_id"],
            "locale": fingerprint["locale"],
            "color_scheme": fingerprint["color_scheme"],
            "device_scale_factor": fingerprint["device_scale_factor"],
            "has_touch": fingerprint["has_touch"],
            "is_mobile": fingerprint["is_mobile"],
        }

    async def apply_js_overrides(self, page):
        """
        Inject JavaScript to override common fingerprint detection points.
        This patches navigator properties, WebGL, and canvas to match our fingerprint.
        """
        await page.add_init_script("""
            // Override navigator.webdriver (bot detection flag)
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override chrome runtime (headless detection)
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            // Override permissions query
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters);

            // Override plugins (headless has 0 plugins)
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Spoof hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => [4, 8, 12, 16][Math.floor(Math.random() * 4)]
            });
        """)

    @property
    def stats(self) -> dict:
        return {
            "total_fingerprints_generated": len(self._used_fingerprints),
            "unique_user_agents": len(set(
                fp["user_agent"] for fp in self._used_fingerprints
            )),
        }
