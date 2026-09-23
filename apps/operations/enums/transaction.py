from django.db import models


class TypeTransaction(models.TextChoices):
    DEPOT = 'DEPOT', 'Dépôt'
    RETRAIT = 'RETRAIT', 'Retrait'
    VIREMENT = 'VIREMENT', 'Virement'


class Sens(models.TextChoices):
    CREDIT = 'CREDIT', 'Crédit'
    DEBIT = 'DEBIT', 'Débit'
