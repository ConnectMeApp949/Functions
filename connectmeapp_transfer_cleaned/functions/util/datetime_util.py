from datetime import datetime, timezone




def conv_dt_to_utc(dt):
    if dt.tzinfo is None:
        # If you know it's actually in UTC already:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to UTC
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc