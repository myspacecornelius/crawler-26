"""
Tests for enrichment/email_waterfall.py

Verifies:
- Individual provider verify() behavior (deliverable/undeliverable/inconclusive/error)
- Waterfall cascade logic (falls through providers until definitive answer)
- Batch verification filtering + status updates
- Provider init from env vars
- Edge cases: no providers, empty leads, no candidates
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from enrichment.email_waterfall import (
    EmailWaterfall,
    HunterVerifier,
    ZeroBounceVerifier,
    MillionVerifier,
    VerificationProvider,
    PROVIDER_CLASSES,
)


# ── Fixtures ─────────────────────────────────────

class FakeLead:
    """Minimal lead-like object for testing."""
    def __init__(self, email="test@example.com", email_status="unknown"):
        self.email = email
        self.email_status = email_status
        self.name = "Test Lead"


# ── Provider Unit Tests ──────────────────────────

class TestHunterVerifier:
    @pytest.mark.asyncio
    async def test_no_api_key_returns_none(self):
        v = HunterVerifier(api_key=None)
        session = MagicMock()
        result = await v.verify(session, "test@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_deliverable_response(self):
        v = HunterVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "data": {"result": "deliverable", "score": 95, "status": "valid_address"}
        })

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "test@example.com")
        assert result is not None
        assert result["deliverable"] is True
        assert result["provider"] == "hunter"
        assert result["confidence"] == 0.95
        assert v.calls_made == 1

    @pytest.mark.asyncio
    async def test_undeliverable_response(self):
        v = HunterVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "data": {"result": "undeliverable", "status": "mailbox_not_found"}
        })

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "bad@example.com")
        assert result["deliverable"] is False
        assert result["provider"] == "hunter"

    @pytest.mark.asyncio
    async def test_risky_returns_inconclusive(self):
        v = HunterVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "data": {"result": "risky", "status": "accept_all"}
        })

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "risky@example.com")
        assert result["deliverable"] is None
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_rate_limited_returns_none(self):
        v = HunterVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 429

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "test@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        v = HunterVerifier(api_key="fake-key")
        session = MagicMock()
        session.get = MagicMock(side_effect=Exception("Network error"))

        result = await v.verify(session, "test@example.com")
        assert result is None


class TestZeroBounceVerifier:
    @pytest.mark.asyncio
    async def test_valid_response(self):
        v = ZeroBounceVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "status": "valid", "sub_status": ""
        })

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "test@example.com")
        assert result["deliverable"] is True
        assert result["provider"] == "zerobounce"

    @pytest.mark.asyncio
    async def test_invalid_response(self):
        v = ZeroBounceVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "status": "invalid", "sub_status": "mailbox_not_found"
        })

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "bad@example.com")
        assert result["deliverable"] is False

    @pytest.mark.asyncio
    async def test_catch_all_returns_inconclusive(self):
        v = ZeroBounceVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "status": "catch-all", "sub_status": ""
        })

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "test@catchall.com")
        assert result["deliverable"] is None


class TestMillionVerifier:
    @pytest.mark.asyncio
    async def test_ok_result(self):
        v = MillionVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"resultcode": 1, "result": "ok"})

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "test@example.com")
        assert result["deliverable"] is True
        assert result["provider"] == "millionverifier"

    @pytest.mark.asyncio
    async def test_invalid_result(self):
        v = MillionVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"resultcode": 6, "result": "invalid"})

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "bad@example.com")
        assert result["deliverable"] is False

    @pytest.mark.asyncio
    async def test_disposable_result(self):
        v = MillionVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"resultcode": 5, "result": "disposable"})

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "trash@tempmail.com")
        assert result["deliverable"] is False

    @pytest.mark.asyncio
    async def test_catch_all_result(self):
        v = MillionVerifier(api_key="fake-key")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"resultcode": 2, "result": "catch_all"})

        session = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(return_value=cm)

        result = await v.verify(session, "test@catchall.com")
        assert result["deliverable"] is None


# ── Waterfall Orchestrator Tests ─────────────────

class TestEmailWaterfallInit:
    def test_no_providers_without_env_keys(self):
        with patch.dict(os.environ, {}, clear=True):
            wf = EmailWaterfall()
            assert len(wf.providers) == 0

    def test_picks_up_env_keys(self):
        with patch.dict(os.environ, {
            "HUNTER_API_KEY": "h_key",
            "ZEROBOUNCE_API_KEY": "zb_key",
        }):
            wf = EmailWaterfall()
            names = [p.name for p in wf.providers]
            assert "hunter" in names
            assert "zerobounce" in names
            assert "millionverifier" not in names

    def test_provider_classes_list(self):
        assert len(PROVIDER_CLASSES) == 3
        assert PROVIDER_CLASSES[0] == HunterVerifier
        assert PROVIDER_CLASSES[1] == ZeroBounceVerifier
        assert PROVIDER_CLASSES[2] == MillionVerifier


class TestWaterfallVerifySingle:
    @pytest.mark.asyncio
    async def test_returns_first_definitive_answer(self):
        wf = EmailWaterfall.__new__(EmailWaterfall)
        p1 = MagicMock(spec=VerificationProvider)
        p1.verify = AsyncMock(return_value=None)
        p2 = MagicMock(spec=VerificationProvider)
        p2.verify = AsyncMock(return_value={
            "deliverable": True, "provider": "p2", "confidence": 0.9, "reason": "ok"
        })
        p3 = MagicMock(spec=VerificationProvider)
        p3.verify = AsyncMock(return_value={
            "deliverable": False, "provider": "p3", "confidence": 0.8, "reason": "bad"
        })
        wf.providers = [p1, p2, p3]

        session = MagicMock()
        result = await wf.verify_single(session, "test@example.com")
        assert result["deliverable"] is True
        assert result["provider"] == "p2"
        p3.verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_through_all_when_all_inconclusive(self):
        wf = EmailWaterfall.__new__(EmailWaterfall)
        p1 = MagicMock(spec=VerificationProvider)
        p1.verify = AsyncMock(return_value={
            "deliverable": None, "provider": "p1", "confidence": 0.3, "reason": "risky"
        })
        p2 = MagicMock(spec=VerificationProvider)
        p2.verify = AsyncMock(return_value=None)
        wf.providers = [p1, p2]

        session = MagicMock()
        result = await wf.verify_single(session, "test@example.com")
        assert result["deliverable"] is None
        assert result["provider"] == "waterfall"
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_empty_providers_returns_fallback(self):
        wf = EmailWaterfall.__new__(EmailWaterfall)
        wf.providers = []
        session = MagicMock()
        result = await wf.verify_single(session, "test@example.com")
        assert result["deliverable"] is None


class TestWaterfallVerifyBatch:
    @pytest.mark.asyncio
    async def test_no_providers_returns_leads_unchanged(self):
        wf = EmailWaterfall.__new__(EmailWaterfall)
        wf.providers = []
        leads = [FakeLead("a@b.com", "unknown"), FakeLead("c@d.com", "guessed")]
        result = await wf.verify_batch(leads)
        assert len(result) == 2
        assert result[0].email_status == "unknown"

    @pytest.mark.asyncio
    async def test_filters_candidates_correctly(self):
        wf = EmailWaterfall.__new__(EmailWaterfall)
        p = MagicMock(spec=VerificationProvider)
        p.name = "mock"
        p.calls_made = 0
        wf.providers = [p]

        async def fake_verify_single(session, email):
            return {"deliverable": True, "provider": "mock", "confidence": 0.9, "reason": "ok"}
        wf.verify_single = fake_verify_single

        leads = [
            FakeLead("valid@example.com", "unknown"),
            FakeLead("guessed@example.com", "guessed"),
            FakeLead("verified@example.com", "verified"),
            FakeLead("N/A", "unknown"),
            FakeLead("", "unknown"),
            FakeLead("no-at-sign", "unknown"),
        ]

        result = await wf.verify_batch(leads)
        assert result[0].email_status == "verified"
        assert result[1].email_status == "verified"
        assert result[2].email_status == "verified"
        assert result[3].email_status == "unknown"

    @pytest.mark.asyncio
    async def test_batch_updates_status_on_rejection(self):
        wf = EmailWaterfall.__new__(EmailWaterfall)
        p = MagicMock(spec=VerificationProvider)
        p.name = "mock"
        p.calls_made = 0
        wf.providers = [p]

        async def fake_verify_single(session, email):
            return {"deliverable": False, "provider": "mock", "confidence": 0.9, "reason": "bad"}
        wf.verify_single = fake_verify_single

        leads = [FakeLead("bad@example.com", "catch_all")]
        result = await wf.verify_batch(leads)
        assert result[0].email_status == "undeliverable"

    @pytest.mark.asyncio
    async def test_batch_leaves_inconclusive_unchanged(self):
        wf = EmailWaterfall.__new__(EmailWaterfall)
        p = MagicMock(spec=VerificationProvider)
        p.name = "mock"
        p.calls_made = 0
        wf.providers = [p]

        async def fake_verify_single(session, email):
            return {"deliverable": None, "provider": "mock", "confidence": 0.0, "reason": "dunno"}
        wf.verify_single = fake_verify_single

        leads = [FakeLead("maybe@example.com", "unknown")]
        result = await wf.verify_batch(leads)
        assert result[0].email_status == "unknown"

    @pytest.mark.asyncio
    async def test_no_candidates_returns_early(self):
        wf = EmailWaterfall.__new__(EmailWaterfall)
        p = MagicMock(spec=VerificationProvider)
        p.name = "mock"
        p.calls_made = 0
        wf.providers = [p]

        leads = [
            FakeLead("verified@example.com", "verified"),
            FakeLead("N/A", "unknown"),
        ]
        result = await wf.verify_batch(leads)
        assert len(result) == 2
