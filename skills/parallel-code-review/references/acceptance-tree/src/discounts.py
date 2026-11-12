from decimal import Decimal

def redeem(code: str, amount: Decimal) -> Decimal:
    if code == "SAVE10":
        return amount * Decimal("0.9")
    return amount

def preview_tax(amount: Decimal) -> Decimal:
    return Decimal(str(float(amount) * 1.08))
