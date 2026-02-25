import time
from datetime import datetime, timezone
from typing import Optional

import pytz


USER_TIMEZONE: Optional[str] = None

TZ_ALIASES = {
    "IST": "Asia/Kolkata",
    "JST": "Asia/Tokyo",
    "CST": "America/Chicago",
    "PST": "America/Los_Angeles",
    "EST": "America/New_York",
    "MST": "America/Denver",
}


def get_local_timezone() -> str:
    try:
        tz = time.tzname[0] if time.tzname else "UTC"
        tz = normalize_timezone(tz)
        pytz.timezone(tz)
        return tz
    except Exception:
        return "UTC"


def normalize_timezone(tz: str) -> str:
    return TZ_ALIASES.get(tz, tz)


def set_user_timezone(tz: str) -> None:
    global USER_TIMEZONE
    USER_TIMEZONE = tz


def get_user_timezone() -> str:
    global USER_TIMEZONE
    if USER_TIMEZONE is None:
        USER_TIMEZONE = get_local_timezone()
    return USER_TIMEZONE


def to_local_time(
    utc_dt: Optional[datetime], tz: Optional[str] = None
) -> Optional[datetime]:
    if not utc_dt:
        return None
    target_tz_name = tz or get_user_timezone()
    target_tz_name = normalize_timezone(target_tz_name)
    try:
        target_tz = pytz.timezone(target_tz_name)
    except Exception:
        target_tz = pytz.utc

    try:
        if utc_dt.tzinfo is None:
            utc_dt = pytz.utc.localize(utc_dt)
        return utc_dt.astimezone(target_tz)
    except Exception:
        return utc_dt


def format_local_time(
    utc_dt: Optional[datetime],
    tz: Optional[str] = None,
    fmt: str = "%Y-%m-%d %H:%M:%S %Z",
) -> str:
    local_dt = to_local_time(utc_dt, tz)
    if not local_dt:
        return ""
    return local_dt.strftime(fmt)


def relative_time(utc_dt: Optional[datetime], tz: Optional[str] = None) -> str:
    if not utc_dt:
        return ""
    try:
        local_dt = to_local_time(utc_dt, tz)
        if not local_dt:
            return ""

        now = (
            datetime.now(timezone.utc).astimezone(local_dt.tzinfo)
            if local_dt.tzinfo
            else datetime.now(timezone.utc)
        )
        diff = now - local_dt

        seconds = diff.total_seconds()
        if seconds < 0:
            seconds = -seconds
            suffix = "from now"
        else:
            suffix = "ago"

        if seconds < 60:
            return f"{int(seconds)} seconds {suffix}"
        elif seconds < 3600:
            mins = int(seconds / 60)
            return f"{mins} minute{'s' if mins != 1 else ''} {suffix}"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} {suffix}"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} {suffix}"
        elif seconds < 31536000:
            months = int(seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} {suffix}"
        else:
            years = int(seconds / 31536000)
            return f"{years} year{'s' if years != 1 else ''} {suffix}"
    except Exception:
        return ""


def get_available_timezones():
    return list(pytz.all_timezones)[:50]
