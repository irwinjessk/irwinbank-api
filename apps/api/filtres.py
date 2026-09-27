from datetime import date
from decimal import Decimal, InvalidOperation

from rest_framework.exceptions import ValidationError


def entier(params, cle):
    valeur = params.get(cle)
    if not valeur:
        return None
    try:
        return int(valeur)
    except (TypeError, ValueError):
        raise ValidationError({cle: ['Identifiant invalide.']})


def decimal(params, cle):
    valeur = params.get(cle)
    if not valeur:
        return None
    try:
        return Decimal(valeur)
    except InvalidOperation:
        raise ValidationError({cle: ['Montant invalide.']})


def jour(params, cle):
    valeur = params.get(cle)
    if not valeur:
        return None
    try:
        return date.fromisoformat(valeur)
    except ValueError:
        raise ValidationError({cle: ['Date invalide, format attendu AAAA-MM-JJ.']})
