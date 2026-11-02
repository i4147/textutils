import decimal

decimal.getcontext().prec = 16


def obj_to_decimal(time, message=None):
    if isinstance(time, decimal.Decimal):
        return time
    elif isinstance(time, (int, float)):
        return decimal.Decimal(str(time))
    elif isinstance(time, str):
        return decimal.Decimal(time)
    else:
        message = "time parameter must be int, float, str or decimal.Decimal"
        raise TypeError(message)
