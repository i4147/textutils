import datetime
from typing import Union

from excel_dates import AnyDateType, ensure_excel_datetime


def elapsed_seconds(value: AnyDateType) -> float:

    if type(value) == datetime.time:
        return (value.hour * 3600) + (value.minute * 60) + value.second + (value.microsecond / 1000000.0)

    return ensure_excel_datetime(value) * 86400


def elapsed_minutes(value: Union[datetime.datetime, datetime.date, datetime.time]) -> float:
    return elapsed_seconds(value) / 60


def elapsed_hours(value: Union[datetime.datetime, datetime.date, datetime.time]) -> float:
    return elapsed_seconds(value) / 3600
