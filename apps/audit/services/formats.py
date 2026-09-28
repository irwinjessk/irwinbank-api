from decimal import Decimal


def montant_fr(valeur):
    """20000 → « 20 000,00 F CFA » (espaces insécables)."""
    return f'{Decimal(valeur):,.2f}'.replace(',', '\u00a0').replace('.', ',') + '\u00a0F\u00a0CFA'
