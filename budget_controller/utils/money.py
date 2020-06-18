from decimal import Decimal


def round_money(digit):
    return digit.quantize(Decimal('1.00'))
