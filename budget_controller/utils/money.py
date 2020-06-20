from decimal import Decimal


def round_digit(digit):
    """
    Округление числа до 2 знаков после запятой

    params: digit - число для округления
    return: округленное число
    """
    return digit.quantize(Decimal('1.00'))
