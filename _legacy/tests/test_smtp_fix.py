"""Tests for SMTP verification fixes in enrichment/email_validator.py"""

import asyncio
import os
import socket
import smtplib
from unittest.mock import patch, MagicMock, call

import pytest

from enrichment.email_validator import EmailValidator


@pytest.fixture
def validator():
    """Fresh EmailValidator instance with self-test state reset."""
    v = EmailValidator()
    v._smtp_available = None
    return v


def run(coro):
    """Helper to run async coroutines in tests."""
    return asyncio.run(coro)


def _make_mock_smtp(ehlo_code=250):
    """Create a mock smtplib.SMTP instance with configurable EHLO response."""
    mock = MagicMock()
    mock.connect.return_value = (220, b"Ready")
    mock.ehlo.return_value = (ehlo_code, b"Hello")
    mock.quit.return_value = (221, b"Bye")
    return mock


# ── 1. smtp_self_test returns a boolean ──

class TestSmtpSelfTest:
    def test_returns_true_when_smtp_handshake_succeeds(self, validator):
        mock_smtp = _make_mock_smtp(ehlo_code=250)
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = run(validator.smtp_self_test())
            assert result is True
            assert validator._smtp_available is True
            mock_smtp.ehlo.assert_called_once()
            mock_smtp.quit.assert_called_once()

    def test_returns_false_when_all_ports_blocked(self, validator):
        mock_smtp = MagicMock()
        mock_smtp.connect.side_effect = OSError("Connection refused")
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = run(validator.smtp_self_test())
            assert result is False
            assert validator._smtp_available is False

    def test_caches_result_on_subsequent_calls(self, validator):
        validator._smtp_available = True
        with patch("smtplib.SMTP") as mock_cls:
            result = run(validator.smtp_self_test())
            assert result is True
            mock_cls.assert_not_called()  # should use cached value

    def test_proxy_host_used_when_set(self):
        with patch.dict(os.environ, {"SMTP_PROXY_HOST": "proxy.example.com", "SMTP_PROXY_PORT": "2525"}):
            v = EmailValidator()
            v._smtp_available = None
            mock_smtp = _make_mock_smtp()
            with patch("smtplib.SMTP", return_value=mock_smtp):
                run(v.smtp_self_test())
                # Should connect to the proxy host
                mock_smtp.connect.assert_called_once_with("proxy.example.com", 2525)


# ── 2. verify_smtp with invalid email format ──

class TestVerifySmtpInvalid:
    def test_empty_email(self, validator):
        result = run(validator.verify_smtp(""))
        assert result["deliverable"] is False

    def test_no_at_sign(self, validator):
        result = run(validator.verify_smtp("notanemail"))
        assert result["deliverable"] is False

    def test_none_email(self, validator):
        result = run(validator.verify_smtp(None))
        assert result["deliverable"] is False


# ── 3. verify_smtp timeout handling (mock socket to simulate timeout) ──

class TestVerifySmtpTimeout:
    def test_timeout_returns_none(self, validator):
        validator._smtp_available = True
        validator._mx_host_cache["example.com"] = "mx.example.com"

        with patch.object(validator, "_smtp_connect", side_effect=socket.timeout("timed out")):
            result = run(validator.verify_smtp("user@example.com"))
            # Timeout in _smtp_check → code -1 → deliverable=None
            assert result["deliverable"] is None

    def test_connection_refused_returns_none(self, validator):
        validator._smtp_available = True
        validator._mx_host_cache["example.com"] = "mx.example.com"

        with patch.object(validator, "_smtp_connect", side_effect=ConnectionRefusedError("refused")):
            result = run(validator.verify_smtp("user@example.com"))
            assert result["deliverable"] is None


# ── 3b. MX resolution fallback ──

class TestMxResolutionFallback:
    def test_dnspython_success(self, validator):
        mock_mx = MagicMock()
        mock_mx.preference = 10
        mock_mx.exchange = "mx.example.com."

        with patch("dns.resolver.resolve", return_value=[mock_mx]):
            result = validator._resolve_mx_host_sync("example.com")
            assert result == "mx.example.com"

    def test_nslookup_fallback_when_dnspython_missing(self, validator):
        mock_result = MagicMock()
        mock_result.stdout = "example.com\tmail exchanger = 10 mx.fallback.com.\n"
        mock_result.returncode = 0

        with patch.dict("sys.modules", {"dns": None, "dns.resolver": None}):
            with patch("subprocess.run", return_value=mock_result):
                result = validator._resolve_mx_host_sync("example.com")
                assert result == "mx.fallback.com"

    def test_a_record_fallback_when_all_else_fails(self, validator):
        with patch.dict("sys.modules", {"dns": None, "dns.resolver": None}):
            with patch("subprocess.run", side_effect=FileNotFoundError("nslookup not found")):
                with patch("socket.getaddrinfo", return_value=[(2, 1, 6, '', ('1.2.3.4', 25))]):
                    result = validator._resolve_mx_host_sync("example.com")
                    assert result == "example.com"

    def test_returns_none_when_all_fail(self, validator):
        with patch.dict("sys.modules", {"dns": None, "dns.resolver": None}):
            with patch("subprocess.run", side_effect=FileNotFoundError):
                with patch("socket.getaddrinfo", side_effect=socket.gaierror("not found")):
                    result = validator._resolve_mx_host_sync("nonexistent.invalid")
                    assert result is None


# ── 3c. EHLO/HELO fallback and MAIL FROM retry ──

class TestEhloAndMailFromHandling:
    def test_ehlo_fallback_to_helo(self, validator):
        validator._smtp_available = True
        validator._mx_host_cache["example.com"] = "mx.example.com"

        mock_smtp = MagicMock()
        mock_smtp.ehlo.return_value = (500, b"EHLO not supported")
        mock_smtp.helo.return_value = (250, b"Hello")
        mock_smtp.mail.return_value = (250, b"OK")
        mock_smtp.rcpt.return_value = (250, b"OK")
        mock_smtp.quit.return_value = (221, b"Bye")

        # catch-all check mock
        mock_smtp2 = MagicMock()
        mock_smtp2.ehlo.return_value = (250, b"Hello")
        mock_smtp2.helo.return_value = (250, b"Hello")
        mock_smtp2.mail.return_value = (250, b"OK")
        mock_smtp2.rcpt.return_value = (550, b"No such user")
        mock_smtp2.quit.return_value = (221, b"Bye")

        calls = [0]
        def side_effect(h, p):
            calls[0] += 1
            return mock_smtp if calls[0] == 1 else mock_smtp2

        with patch.object(validator, "_smtp_connect", side_effect=side_effect):
            result = run(validator.verify_smtp("user@example.com"))
            assert result["deliverable"] is True
            mock_smtp.helo.assert_called()  # HELO was used as fallback

    def test_mail_from_retry_with_empty_sender(self, validator):
        validator._smtp_available = True
        validator._mx_host_cache["example.com"] = "mx.example.com"

        mock_smtp = MagicMock()
        mock_smtp.ehlo.return_value = (250, b"Hello")
        # First MAIL FROM rejected, empty sender accepted
        mock_smtp.mail.side_effect = [(550, b"Sender rejected"), (250, b"OK")]
        mock_smtp.rset.return_value = (250, b"OK")
        mock_smtp.rcpt.return_value = (550, b"No such user")
        mock_smtp.quit.return_value = (221, b"Bye")

        with patch.object(validator, "_smtp_connect", return_value=mock_smtp):
            result = run(validator.verify_smtp("bad@example.com"))
            assert result["deliverable"] is False
            # MAIL FROM was called twice (original + empty sender retry)
            assert mock_smtp.mail.call_count == 2
            mock_smtp.rset.assert_called_once()


# ── 4. Port 587 fallback when port 25 fails ──

class TestPort587Fallback:
    def test_fallback_to_587(self, validator):
        call_log = []

        original_smtp_init = smtplib.SMTP.__init__
        original_smtp_connect = smtplib.SMTP.connect

        def mock_smtp_init(self_smtp, *args, **kwargs):
            self_smtp._host = ""
            self_smtp.timeout = kwargs.get("timeout", 10)
            self_smtp.esmtp_features = {}
            self_smtp.ehlo_resp = None
            self_smtp.ehlo_msg = b""
            self_smtp.does_esmtp = 0
            self_smtp.local_hostname = "localhost"

        def mock_smtp_connect(self_smtp, host, port, **kwargs):
            call_log.append((host, port))
            if port == 25:
                raise OSError("port 25 blocked")
            return (220, b"OK")

        with patch.object(smtplib.SMTP, "__init__", mock_smtp_init):
            with patch.object(smtplib.SMTP, "connect", mock_smtp_connect):
                smtp = validator._smtp_connect("mx.example.com", 25)
                # Should have tried port 25 first, then 587
                assert (("mx.example.com", 25) in call_log)
                assert (("mx.example.com", 587) in call_log)

    def test_no_fallback_for_non_25_port(self, validator):
        call_log = []

        def mock_smtp_init(self_smtp, *args, **kwargs):
            self_smtp._host = ""
            self_smtp.timeout = kwargs.get("timeout", 10)
            self_smtp.esmtp_features = {}
            self_smtp.ehlo_resp = None
            self_smtp.ehlo_msg = b""
            self_smtp.does_esmtp = 0
            self_smtp.local_hostname = "localhost"

        def mock_smtp_connect(self_smtp, host, port, **kwargs):
            call_log.append((host, port))
            raise OSError("connection failed")

        with patch.object(smtplib.SMTP, "__init__", mock_smtp_init):
            with patch.object(smtplib.SMTP, "connect", mock_smtp_connect):
                with pytest.raises(OSError):
                    validator._smtp_connect("mx.example.com", 2525)
                # Should only try the specified port, no 587 fallback
                assert call_log == [("mx.example.com", 2525)]


# ── 5. HELO domain configuration from env var ──

class TestHeloDomainConfig:
    def test_default_helo_domain(self):
        with patch.dict(os.environ, {}, clear=False):
            # Remove SMTP_HELO_DOMAIN if set
            os.environ.pop("SMTP_HELO_DOMAIN", None)
            v = EmailValidator()
            # Should be either the machine's FQDN or the fallback
            assert v._smtp_helo_domain
            assert v._smtp_helo_domain != ""

    def test_custom_helo_domain(self):
        with patch.dict(os.environ, {"SMTP_HELO_DOMAIN": "custom.example.com"}):
            v = EmailValidator()
            assert v._smtp_helo_domain == "custom.example.com"

    def test_custom_timeout(self):
        with patch.dict(os.environ, {"SMTP_TIMEOUT": "20"}):
            v = EmailValidator()
            assert v._smtp_timeout == 20


# ── 6. Graceful degradation warning when SMTP blocked ──

class TestGracefulDegradation:
    def test_batch_skips_when_blocked(self, validator):
        mock_smtp = MagicMock()
        mock_smtp.connect.side_effect = OSError("blocked")
        with patch("smtplib.SMTP", return_value=mock_smtp):
            results = run(validator.verify_smtp_batch(
                ["a@example.com", "b@example.com"]
            ))
            # All should be unknown/None
            assert len(results) == 2
            for email, res in results.items():
                assert res["deliverable"] is None
                assert res["smtp_code"] == 0

    def test_verify_smtp_skips_when_blocked(self, validator):
        validator._smtp_available = False
        result = run(validator.verify_smtp("user@example.com"))
        assert result["deliverable"] is None
        assert result["smtp_code"] == 0

    def test_warning_logged_when_blocked(self, validator, caplog):
        import logging
        mock_smtp = MagicMock()
        mock_smtp.connect.side_effect = OSError("blocked")
        with caplog.at_level(logging.WARNING, logger="enrichment.email_validator"):
            with patch("smtplib.SMTP", return_value=mock_smtp):
                run(validator.smtp_self_test())
        assert "SMTP" in caplog.text
        assert "blocked" in caplog.text.lower() or "appears blocked" in caplog.text.lower()


# ── 7. Full SMTP flow with mocked SMTP server ──

class TestSmtpFullFlow:
    def test_deliverable_email(self, validator):
        validator._smtp_available = True
        validator._mx_host_cache["example.com"] = "mx.example.com"

        mock_smtp = MagicMock()
        mock_smtp.ehlo.return_value = (250, b"Hello")
        mock_smtp.mail.return_value = (250, b"OK")
        mock_smtp.rcpt.return_value = (250, b"OK")
        mock_smtp.quit.return_value = (221, b"Bye")
        # catch-all check: reject fake address
        mock_smtp_catchall = MagicMock()
        mock_smtp_catchall.ehlo.return_value = (250, b"Hello")
        mock_smtp_catchall.mail.return_value = (250, b"OK")
        mock_smtp_catchall.rcpt.return_value = (550, b"No such user")
        mock_smtp_catchall.quit.return_value = (221, b"Bye")

        call_count = [0]
        def mock_connect(host, port):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_smtp
            return mock_smtp_catchall

        with patch.object(validator, "_smtp_connect", side_effect=mock_connect):
            result = run(validator.verify_smtp("user@example.com"))
            assert result["deliverable"] is True
            assert result["smtp_code"] == 250
            assert result["catch_all"] is False

    def test_undeliverable_email(self, validator):
        validator._smtp_available = True
        validator._mx_host_cache["example.com"] = "mx.example.com"

        mock_smtp = MagicMock()
        mock_smtp.ehlo.return_value = (250, b"Hello")
        mock_smtp.mail.return_value = (250, b"OK")
        mock_smtp.rcpt.return_value = (550, b"User unknown")
        mock_smtp.quit.return_value = (221, b"Bye")

        with patch.object(validator, "_smtp_connect", return_value=mock_smtp):
            result = run(validator.verify_smtp("bad@example.com"))
            assert result["deliverable"] is False
            assert result["smtp_code"] == 550
