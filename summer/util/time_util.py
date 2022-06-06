import re
from typing import Optional
import numpy as np
import pandas as pd
import datetime


_DURATION_REGX = re.compile(
    r'^\s*((?P<days>[\.\d]+?)d)?\s*((?P<hours>[\.\d]+?)h)?\s*((?P<minutes>[\.\d]+?)m)?\s*((?P<seconds>[\.\d]+?)s)?\s*$')

DAY_SECONDS = 24 * 60 * 60

DATE_MIN = datetime.datetime.fromtimestamp(0.0).replace(tzinfo=datetime.timezone.utc)

def seconds(t: datetime.time):
    return t.hour * 3600 + t.minute*60 + t.second


def duration(t1: datetime.time, t2: datetime.time) -> datetime.timedelta:
    duration_seconds = (seconds(t2) - seconds(t1)) % DAY_SECONDS
    return datetime.timedelta(seconds=duration_seconds)


def is_between(t, start, end) -> bool:
    dist_end = duration(start, end)
    dist_now = duration(start, t)

    return dist_end > dist_now


def parse_duration(time_str)-> datetime.timedelta:
    """
    Parse a time string e.g. (2h13m) into a timedelta object.

    Modified from virhilo's answer at https://stackoverflow.com/a/4628148/851699

    :param time_str: A string identifying a duration.  (eg. 2h13m)
    :return datetime.timedelta: A datetime.timedelta object
    """
    parts = _DURATION_REGX.match(time_str)
    if parts is None:
        raise ValueError(
            "Could not parse any time information from '{}'.  Examples of valid strings: '8h', '2d8h5m20s', '2m4s'".format(time_str))
    time_params = {name: float(param)
                   for name, param in parts.groupdict().items() if param}
    return datetime.timedelta(**time_params)


def parse_time(time_str: str) -> datetime.time:
    return datetime.datetime.strptime(time_str, "%H:%M").time()


def coerce_time(time) -> datetime.time:
    if isinstance(time, datetime.time):
        return time
    if isinstance(time, datetime.datetime):
        return time.time()
    if isinstance(time, (float, int)):
        return datetime.datetime.utcfromtimestamp(time).time()
    if isinstance(time, str):
        return datetime.time.fromisoformat(str)
    raise ValueError(f"can not parse time from \"{time}\"")

def _coerce_datetime_timezone(dt: datetime.datetime) -> datetime.datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt

def _coerce_datetime_no_timezone(dt: datetime.datetime) -> datetime.datetime:
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def _np_datetime64_to_datetime(np_datetime: np.datetime64) -> Optional[datetime.datetime]:
    if np_datetime is None or pd.isna(np_datetime):
        return None
    unix_epoch = np.datetime64(0, 's')
    one_second = np.timedelta64(1, 's')
    seconds_since_epoch = (np_datetime - unix_epoch) / one_second
    return datetime.datetime.utcfromtimestamp(seconds_since_epoch)

def coerce_datetime(time) -> datetime.datetime:
    return _coerce_datetime_no_timezone(_coerce_datetime(time))

def _coerce_datetime(time) -> datetime.datetime:
    if isinstance(time, np.datetime64):
        return _np_datetime64_to_datetime(time)
    if isinstance(time, datetime.datetime):
        return time
    if isinstance(time, (float, int)):
        return datetime.datetime.utcfromtimestamp(time)
    if isinstance(time, str):
        return datetime.datetime.fromisoformat(time)
    raise ValueError(f"can not parse datetime from \"{time}\"")
    

def coerce_duration(duration) -> datetime.timedelta:
    if duration is None:
        return datetime.timedelta(microseconds=0)
    if isinstance(duration, datetime.timedelta):
        return duration
    if isinstance(duration, (float, int)):
        return datetime.timedelta(seconds=duration)
    if isinstance(duration, str):
        return parse_duration(duration)
    raise ValueError(f"can not parse duration from \"{duration}\"")

def time_today(time: datetime.time) -> datetime.datetime:
    return datetime.datetime.combine(datetime.date.today(), time)


def timedelta_between_safe(first_event, second_event, abs=False) -> datetime.timedelta:
    first_event_dt = coerce_datetime(first_event)
    second_event_dt = coerce_datetime(second_event)
    if abs and first_event > second_event:
        first_event, second_event = second_event, first_event
    return second_event_dt - first_event_dt

    
DATE_MIN = _coerce_datetime_timezone(datetime.datetime.fromtimestamp(0.0))