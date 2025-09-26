from datetime import datetime, timedelta

import pytz

berlin_tz = pytz.timezone("Europe/Berlin")
gmt_tz = pytz.timezone("GMT")


def get_now():
    return datetime.now(tz=berlin_tz)


def get_today():
    now = get_now()
    return datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)


def create_berlin_date(year, month, day, hour=0, minute=0, second=0):
    return berlin_tz.localize(
        datetime(year, month, day, hour=hour, minute=minute, second=second)
    )


def date_parts_are_equal(date1: datetime, date2: datetime) -> bool:
    return (
        date1.year == date2.year
        and date1.month == date2.month
        and date1.day == date2.day
    )


def date_add_time(date, hour=0, minute=0, second=0, tzinfo=None):
    return datetime(
        date.year,
        date.month,
        date.day,
        hour=hour,
        minute=minute,
        second=second,
        tzinfo=tzinfo,
    )


def date_set_begin_of_day(date, remove_tz=False):
    tzinfo = None if remove_tz else date.tzinfo
    return date_add_time(date, tzinfo=tzinfo)


def date_set_end_of_day(date, remove_tz=False):
    tzinfo = None if remove_tz else date.tzinfo
    return date_add_time(date, hour=23, minute=59, second=59, tzinfo=tzinfo)


def round_to_next_day(date):
    new_date = date + timedelta(days=1)
    return date_set_begin_of_day(new_date)


def round_to_next_full_hour(date):
    new_date = date + timedelta(hours=1)
    return date_add_time(date, new_date.hour, tzinfo=date.tzinfo)


def get_next_full_hour():
    now = get_now()
    return round_to_next_full_hour(now)


def form_input_to_date(date_str, hour=0, minute=0, second=0):
    if not date_str:  # pragma: no cover
        return None
    date = datetime.strptime(date_str, "%Y-%m-%d")
    date_time = date_add_time(date, hour=hour, minute=minute, second=second)
    return berlin_tz.localize(date_time)


def form_input_from_date(date):
    return date.strftime("%Y-%m-%d") if date else ""


def is_datetime_older_than_seconds(date_time: datetime, seconds: int) -> bool:
    if not date_time:
        return True

    return (datetime.utcnow() - date_time).total_seconds() > seconds
