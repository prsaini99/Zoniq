import datetime


# Convert a datetime object to an ISO 8601 string in UTC, using 'Z' suffix instead of '+00:00'
def format_datetime_into_isoformat(date_time: datetime.datetime) -> str:
    return date_time.replace(tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")
