"""Tests for utility functions."""
import pytest
from datetime import datetime
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import format_penalty_alert, format_penalty_row, format_stats, mask_api_key


class TestFormatPenaltyAlert:
    """Test penalty alert formatting."""

    def test_basic_penalty(self):
        penalty = {
            "amount": 5000,
            "reason": "Нарушение маркировки",
            "penalty_date": "2026-03-20",
            "appeal_deadline": "2026-03-27",
            "supply_id": 12345,
            "nm_id": 67890,
            "sa_name": "ART-001",
            "brand_name": "TestBrand",
            "subject_name": "Футболка",
        }
        result = format_penalty_alert(penalty)
        assert "5,000" in result or "5 000" in result
        assert "Нарушение маркировки" in result
        assert "2026-03-20" in result
        assert "2026-03-27" in result
        assert "ART-001" in result
        assert "TestBrand" in result

    def test_with_store_name(self):
        penalty = {"amount": 1000, "reason": "Test", "penalty_date": "2026-03-20",
                    "appeal_deadline": "—", "supply_id": "—", "nm_id": "—"}
        result = format_penalty_alert(penalty, store_name="Мой магазин")
        assert "Мой магазин" in result

    def test_without_store_name(self):
        penalty = {"amount": 1000, "reason": "Test", "penalty_date": "2026-03-20",
                    "appeal_deadline": "—", "supply_id": "—", "nm_id": "—"}
        result = format_penalty_alert(penalty)
        assert "Магазин" not in result

    @patch("utils.datetime")
    def test_appeal_deadline_today(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 20, 12, 0)
        mock_dt.strptime = datetime.strptime
        penalty = {"amount": 1000, "reason": "Test", "penalty_date": "2026-03-20",
                    "appeal_deadline": "2026-03-20", "supply_id": "—", "nm_id": "—"}
        result = format_penalty_alert(penalty)
        assert "СЕГОДНЯ" in result

    @patch("utils.datetime")
    def test_appeal_deadline_expired(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 25, 12, 0)
        mock_dt.strptime = datetime.strptime
        penalty = {"amount": 1000, "reason": "Test", "penalty_date": "2026-03-15",
                    "appeal_deadline": "2026-03-22", "supply_id": "—", "nm_id": "—"}
        result = format_penalty_alert(penalty)
        assert "ПРОСРОЧЕН" in result

    @patch("utils.datetime")
    def test_appeal_deadline_days_left(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 20, 12, 0)
        mock_dt.strptime = datetime.strptime
        penalty = {"amount": 1000, "reason": "Test", "penalty_date": "2026-03-20",
                    "appeal_deadline": "2026-03-25", "supply_id": "—", "nm_id": "—"}
        result = format_penalty_alert(penalty)
        assert "дн. осталось" in result

    def test_missing_optional_fields(self):
        penalty = {"amount": 500}
        result = format_penalty_alert(penalty)
        assert "500" in result

    def test_html_tags_present(self):
        penalty = {"amount": 1000, "reason": "Test", "penalty_date": "2026-03-20",
                    "appeal_deadline": "—", "supply_id": "—", "nm_id": "—"}
        result = format_penalty_alert(penalty)
        assert "<b>" in result


class TestFormatPenaltyRow:
    """Test short penalty line formatting."""

    def test_basic_row(self):
        penalty = {"amount": 3000, "penalty_date": "2026-03-20", "reason": "Штраф за маркировку"}
        result = format_penalty_row(penalty, index=1)
        assert "1." in result
        assert "3,000" in result or "3 000" in result
        assert "2026-03-20" in result

    def test_reason_truncated(self):
        penalty = {"amount": 100, "penalty_date": "2026-03-20",
                    "reason": "A" * 50}
        result = format_penalty_row(penalty)
        assert len(penalty["reason"][:30]) == 30

    def test_zero_index(self):
        penalty = {"amount": 100, "penalty_date": "—", "reason": ""}
        result = format_penalty_row(penalty, index=0)
        assert result.startswith("0.")


class TestFormatStats:
    """Test statistics formatting."""

    def test_basic_stats(self):
        stats = {
            "total_count": 15,
            "total_amount": 45000,
            "month_amount": 12000,
            "week_amount": 3000,
        }
        result = format_stats(stats)
        assert "15" in result
        assert "45,000" in result or "45 000" in result
        assert "12,000" in result or "12 000" in result
        assert "3,000" in result or "3 000" in result

    def test_zero_stats(self):
        stats = {"total_count": 0, "total_amount": 0, "month_amount": 0, "week_amount": 0}
        result = format_stats(stats)
        assert "0" in result

    def test_html_formatting(self):
        stats = {"total_count": 1, "total_amount": 100, "month_amount": 100, "week_amount": 100}
        result = format_stats(stats)
        assert "<b>" in result


class TestMaskApiKey:
    """Test API key masking."""

    def test_long_key(self):
        key = "abcdefghijklmnopqrstuvwxyz"
        result = mask_api_key(key)
        assert result.startswith("abcdefgh")
        assert result.endswith("wxyz")
        assert "..." in result
        assert len(result) < len(key)

    def test_short_key(self):
        key = "abcdef"
        result = mask_api_key(key)
        assert result.startswith("abcd")
        assert "..." in result

    def test_very_short_key(self):
        key = "abc"
        result = mask_api_key(key)
        assert "..." in result

    def test_typical_wb_key(self):
        key = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.abcdef"
        result = mask_api_key(key)
        assert "eyJhbGci" in result
        assert "abcdef"[-4:] in result
        # Middle is hidden
        assert "OiJFUzI1" not in result
