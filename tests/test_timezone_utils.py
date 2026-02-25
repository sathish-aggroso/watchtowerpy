import pytest
from app.utils import (
    get_local_timezone,
    normalize_timezone,
    set_user_timezone,
    get_user_timezone,
    to_local_time,
    format_local_time,
    relative_time,
    get_available_timezones,
)
from datetime import datetime, timezone


class TestTimezoneUtils:
    def test_get_local_timezone(self):
        tz = get_local_timezone()
        assert tz is not None
        assert isinstance(tz, str)

    def test_normalize_timezone(self):
        assert normalize_timezone("IST") == "Asia/Kolkata"
        assert normalize_timezone("JST") == "Asia/Tokyo"
        assert normalize_timezone("UTC") == "UTC"
        assert normalize_timezone("Unknown") == "Unknown"
        assert normalize_timezone("PST") == "America/Los_Angeles"
        assert normalize_timezone("EST") == "America/New_York"

    def test_set_and_get_user_timezone(self):
        set_user_timezone("America/New_York")
        assert get_user_timezone() == "America/New_York"

    def test_get_user_timezone_default(self):
        import app.utils

        original = app.utils.USER_TIMEZONE
        app.utils.USER_TIMEZONE = None
        try:
            tz = get_user_timezone()
            assert tz is not None
        finally:
            app.utils.USER_TIMEZONE = original

    def test_to_local_time_with_none(self):
        result = to_local_time(None)
        assert result is None

    def test_to_local_time_with_datetime(self):
        utc_dt = datetime(2024, 1, 1, 12, 0, 0)
        result = to_local_time(utc_dt, "UTC")
        assert result is not None

    def test_to_local_time_with_invalid_tz(self):
        utc_dt = datetime(2024, 1, 1, 12, 0, 0)
        result = to_local_time(utc_dt, "Invalid/Timezone")
        assert result is not None

    def test_to_local_time_with_tzinfo(self):
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = to_local_time(utc_dt, "UTC")
        assert result is not None

    def test_format_local_time_with_none(self):
        result = format_local_time(None)
        assert result == ""

    def test_format_local_time_with_datetime(self):
        utc_dt = datetime(2024, 1, 1, 12, 0, 0)
        result = format_local_time(utc_dt, "UTC")
        assert isinstance(result, str)

    def test_format_local_time_with_custom_format(self):
        utc_dt = datetime(2024, 1, 1, 12, 0, 0)
        result = format_local_time(utc_dt, "UTC", "%Y-%m-%d")
        assert "2024" in result

    def test_relative_time_with_none(self):
        result = relative_time(None)
        assert result == ""

    def test_relative_time_with_datetime(self):
        utc_dt = datetime(2024, 1, 1, 12, 0, 0)
        result = relative_time(utc_dt, "UTC")
        assert isinstance(result, str)

    def test_relative_time_future(self):
        from datetime import timedelta

        future_dt = datetime.now(timezone.utc) + timedelta(hours=1)
        result = relative_time(future_dt, "UTC")
        assert "from now" in result

    def test_relative_time_seconds(self):
        from datetime import timedelta

        recent = datetime.now(timezone.utc) - timedelta(seconds=30)
        result = relative_time(recent, "UTC")
        assert "second" in result

    def test_relative_time_minutes(self):
        from datetime import timedelta

        recent = datetime.now(timezone.utc) - timedelta(minutes=5)
        result = relative_time(recent, "UTC")
        assert "minute" in result

    def test_relative_time_hours(self):
        from datetime import timedelta

        recent = datetime.now(timezone.utc) - timedelta(hours=3)
        result = relative_time(recent, "UTC")
        assert "hour" in result

    def test_relative_time_days(self):
        from datetime import timedelta

        recent = datetime.now(timezone.utc) - timedelta(days=5)
        result = relative_time(recent, "UTC")
        assert "day" in result

    def test_relative_time_weeks(self):
        from datetime import timedelta

        recent = datetime.now(timezone.utc) - timedelta(weeks=2)
        result = relative_time(recent, "UTC")
        assert "week" in result

    def test_relative_time_months(self):
        from datetime import timedelta

        recent = datetime.now(timezone.utc) - timedelta(days=60)
        result = relative_time(recent, "UTC")
        assert "month" in result

    def test_relative_time_years(self):
        from datetime import timedelta

        recent = datetime.now(timezone.utc) - timedelta(days=400)
        result = relative_time(recent, "UTC")
        assert "year" in result

    def test_relative_time_invalid_tz(self):
        utc_dt = datetime(2024, 1, 1, 12, 0, 0)
        result = relative_time(utc_dt, "Invalid/Timezone")
        assert isinstance(result, str)

    def test_get_available_timezones(self):
        timezones = get_available_timezones()
        assert isinstance(timezones, list)
        assert len(timezones) > 0
