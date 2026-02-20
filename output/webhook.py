"""
CRAWL — Webhook Notifier
Sends alerts to Discord/Slack when high-value leads are found.
"""

import json
import asyncio
from typing import Optional

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class WebhookNotifier:
    """
    Sends formatted notifications via webhooks.
    Supports Discord and Slack webhook formats.
    """

    def __init__(self, webhook_url: str = "", platform: str = "discord"):
        """
        Args:
            webhook_url: Discord/Slack webhook URL
            platform: "discord" or "slack"
        """
        self.webhook_url = webhook_url
        self.platform = platform.lower()
        self.enabled = bool(webhook_url)
        self._sent_count = 0

    async def notify_hot_leads(self, leads: list):
        """Send alert for HOT-tier leads."""
        if not self.enabled:
            return

        hot_leads = [l for l in leads if l.lead_score >= 80]
        if not hot_leads:
            return

        if self.platform == "discord":
            await self._send_discord(hot_leads)
        elif self.platform == "slack":
            await self._send_slack(hot_leads)

    async def notify_crawl_complete(self, total: int, new: int, hot: int):
        """Send summary after a crawl completes."""
        if not self.enabled:
            return

        if self.platform == "discord":
            payload = {
                "embeds": [{
                    "title": "🕷️ Crawl Complete",
                    "color": 0x00FF88,
                    "fields": [
                        {"name": "Total Leads", "value": str(total), "inline": True},
                        {"name": "New Leads", "value": str(new), "inline": True},
                        {"name": "🔴 HOT", "value": str(hot), "inline": True},
                    ],
                    "footer": {"text": "CRAWL Engine"},
                }]
            }
        else:
            payload = {
                "text": f"🕷️ *Crawl Complete* — {total} total | {new} new | {hot} 🔴 HOT leads"
            }

        await self._post(payload)

    async def _send_discord(self, leads: list):
        """Format and send leads as Discord embed."""
        # Discord embeds have a max of 25 fields
        for i in range(0, len(leads), 5):
            batch = leads[i:i+5]
            fields = []
            for lead in batch:
                value = (
                    f"**{lead.fund}** — {lead.role}\n"
                    f"📧 {lead.email}\n"
                    f"🎯 {', '.join(lead.focus_areas[:3]) if lead.focus_areas else 'N/A'}\n"
                    f"💰 {lead.check_size} | {lead.stage}\n"
                    f"Score: **{lead.lead_score}** {lead.tier}"
                )
                fields.append({
                    "name": f"🔴 {lead.name}",
                    "value": value[:1024],  # Discord field value limit
                    "inline": False,
                })

            payload = {
                "embeds": [{
                    "title": f"🔥 {len(batch)} Hot Lead{'s' if len(batch) > 1 else ''} Found!",
                    "color": 0xFF4444,
                    "fields": fields,
                    "footer": {"text": "CRAWL Engine — Investor Lead Machine"},
                }]
            }
            await self._post(payload)

    async def _send_slack(self, leads: list):
        """Format and send leads as Slack message."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🔥 {len(leads)} Hot Leads Found!"}
            }
        ]

        for lead in leads[:10]:  # Limit to 10 per message
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*🔴 {lead.name}* — {lead.fund}\n"
                        f"📧 {lead.email} | 🎯 {', '.join(lead.focus_areas[:3]) if lead.focus_areas else 'N/A'}\n"
                        f"💰 {lead.check_size} | {lead.stage} | Score: *{lead.lead_score}*"
                    )
                }
            })

        payload = {"blocks": blocks}
        await self._post(payload)

    async def _post(self, payload: dict):
        """Send webhook POST request."""
        if not HAS_AIOHTTP:
            print("  ⚠️  aiohttp not installed — skipping webhook notification")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status in (200, 204):
                        self._sent_count += 1
                    else:
                        print(f"  ⚠️  Webhook returned status {resp.status}")
        except Exception as e:
            print(f"  ⚠️  Webhook error: {e}")

    @property
    def stats(self) -> dict:
        return {
            "enabled": self.enabled,
            "platform": self.platform,
            "notifications_sent": self._sent_count,
        }
