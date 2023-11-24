from datetime import datetime, timedelta
import re


def format_time_remaining(end_time):
    time_remaining = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") - datetime.now()
    hours, remainder = divmod(time_remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s remaining"


def parse_duration(duration_str: str):
    """Parses a duration string like '1d 2h 30m' or '1 minute' into a timedelta object."""
    # Regex to match patterns like '1d', '2h', '30m', '1 minute', '2 hours'
    pattern = re.compile(
        r"(\d+)\s*(d|h|m|s|week|second|minute|hour|day)s?\b", re.I
    )
    # Dictionary to map the time unit to the corresponding timedelta keyword
    time_unit_keywords = {
        "d": "days",
        "day": "days",
        "days": "days",
        "h": "hours",
        "hour": "hours",
        "hr": "hours",
        "hrs": "hours",
        "m": "minutes",
        "minute": "minutes",
        "min": "minutes",
        "mins": "minutes",
        "minutes": "minutes",
        "s": "seconds",
        "second": "seconds",
        "sec": "seconds",
        "secs": "seconds",
        "seconds": "seconds",
        "week": "weeks",
        "weeks": "weeks",
    }
    # Initialize the default timedelta
    duration = timedelta()
    # Find all matches and add them to the duration
    for match in pattern.finditer(duration_str):
        value, unit = int(match.group(1)), match.group(2).lower()
        if unit in time_unit_keywords:
            if unit == "week" or unit == "weeks":
                duration += timedelta(days=value*7)  # Convert weeks to days
            else:
                kwargs = {time_unit_keywords[unit]: value}
                duration += timedelta(**kwargs)
    return duration
