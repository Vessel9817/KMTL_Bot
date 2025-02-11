# utils/utilities.py
from datetime import datetime, timedelta
import re
import math


def format_time_remaining(remaining_seconds: float):
    # Format the remaining time as HH:MM:SS
    remaining_weeks = int(remaining_seconds // 604800)
    remaining_days = int(remaining_seconds // 86400)
    remaining_hours = int(remaining_seconds // 3600)
    remaining_minutes = int(math.ceil((remaining_seconds % 3600) / 60))
    if remaining_minutes == 60:
        remaining_hours += 1
        remaining_minutes = 0

    if remaining_weeks > 0:
        formatted_time = f"{remaining_weeks} weeks {remaining_days}days"
    elif remaining_days > 0:
        formatted_time = f"{remaining_days} days {remaining_hours} hours"
    elif remaining_hours > 0:
        formatted_time = f"{remaining_hours} hours {remaining_minutes} minutes"
    elif remaining_minutes > 1:
        formatted_time = f"{remaining_minutes} minutes"
    else:
        formatted_time = "less than a minute"

    return formatted_time


def parse_duration(duration_str: str):
    """Parses a duration string like '1d 2h 30m' or '1 minute' into a timedelta object."""
    # Regex to match patterns like '1d', '2h', '30m', '1 minute', '2 hours'
    pattern = re.compile(
        r"(\d+)\s*(d|day|h|hour|hr|m|min|minute|s|sec|second|w|week)s?\b", re.I
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
        "hours": "hours",
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
        "w": "weeks",
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
                duration += timedelta(days=value * 7)  # Convert weeks to days
            else:
                kwargs = {time_unit_keywords[unit]: value}
                duration += timedelta(**kwargs)
    return duration
