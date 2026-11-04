from typing import List

from excel_text.tokens import (
    FormatStringToken,
    MonthOrMinuteToken,
    YearToken,
    MonthToken,
    DayToken,
    MinuteToken,
    DateToken,
    AmPmToken,
    HourToken,
    BinaryConditionalToken,
    TernaryConditionalToken,
    VerbatimToken,
)
from excel_text.errors import ValueExcelError


def preprocess(tokens: List[FormatStringToken]) -> None:
    preprocess_conditionals(tokens)
    preprocess_month_minute(tokens)
    preprocess_am_pm(tokens)


def preprocess_conditionals(tokens: List[FormatStringToken]) -> None:
    for t in tokens:
        if isinstance(t, BinaryConditionalToken):
            preprocess(t.true_tokens)
            preprocess(t.false_tokens)
        if isinstance(t, TernaryConditionalToken):
            preprocess(t.lt_tokens)
            preprocess(t.eq_tokens)
            preprocess(t.gt_tokens)
        if isinstance(t, VerbatimToken):
            if t.text == "[":
                raise ValueExcelError("A value used in the formula is of the wrong data type.")


def preprocess_month_minute(tokens: List[FormatStringToken]) -> None:
    last_date_token = None
    for i, token in enumerate(tokens):
        if isinstance(token, MonthOrMinuteToken):
            if isinstance(last_date_token, (YearToken, DayToken)):
                tokens[i] = MonthToken(token.text)
            else:
                tokens[i] = MinuteToken(token.text)

        if isinstance(token, DateToken):
            last_date_token = token

    last_date_token = None
    for i, token in reversed(list(enumerate(tokens))):
        if isinstance(token, (MonthOrMinuteToken, MinuteToken)):
            if isinstance(last_date_token, (YearToken, DayToken)):
                tokens[i] = MonthToken(token.text)

        if isinstance(token, DateToken):
            last_date_token = token


def preprocess_am_pm(tokens: List[FormatStringToken]) -> None:
    last_hour_token = None
    for i, token in enumerate(tokens):
        if isinstance(token, AmPmToken) and last_hour_token:
            last_hour_token.twelve = True

        if isinstance(token, HourToken):
            last_hour_token = token
