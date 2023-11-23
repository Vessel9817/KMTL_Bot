from datetime import datetime, timedelta
import re


def format_time_remaining(end_time):
    time_remaining = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") - datetime.now()
    hours, remainder = divmod(time_remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s remaining"


def parse_duration(duration_str):
    # Regex pattern to match days, hours, and minutes
    pattern = r"((?P<days>\d+)\s*(d|day|days))?\s*((?P<hours>\d+)\s*(h|hour|hours))?\s*((?P<minutes>\d+)\s*(m|min|mins|minute|minutes))?"
    matches = re.match(pattern, duration_str)
    if not matches:
        return None

    time_params = {k: int(v) for k, v in matches.groupdict(default=0).items()}
    return timedelta(**time_params)
