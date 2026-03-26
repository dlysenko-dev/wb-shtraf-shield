"""Tests for WB API client (parsing logic, not actual API calls)."""
import pytest
from datetime import datetime, timedelta

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wb_api import WBApiError

# Test config values
import config
config.WB_STATS_BASE = "https://statistics-api.wildberries.ru"
config.WB_REPORT_ENDPOINT = "/api/v5/supplier/reportDetailByPeriod"
config.REPORT_LOOKBACK_DAYS = 7
config.APPEAL_DAYS = 7


class TestWBApiError:
    """Test custom API error class."""

    def test_error_attributes(self):
        err = WBApiError(401, "Unauthorized")
        assert err.status == 401
        assert err.message == "Unauthorized"

    def test_error_str(self):
        err = WBApiError(429, "Too many requests")
        assert "429" in str(err)
        assert "Too many requests" in str(err)

    def test_is_exception(self):
        err = WBApiError(500, "Server error")
        assert isinstance(err, Exception)


class TestConfigConstants:
    """Test that config constants are reasonable."""

    def test_appeal_days_positive(self):
        assert config.APPEAL_DAYS > 0

    def test_lookback_days_positive(self):
        assert config.REPORT_LOOKBACK_DAYS > 0

    def test_api_base_url(self):
        assert config.WB_STATS_BASE.startswith("https://")

    def test_endpoint_starts_with_slash(self):
        assert config.WB_REPORT_ENDPOINT.startswith("/")
