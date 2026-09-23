from django.db import models


class TypeCompte(models.TextChoices):
    COURANT = 'COURANT', 'Courant'
    EPARGNE = 'EPARGNE', 'Épargne'


class StatutCompte(models.TextChoices):
    OUVERT = 'OUVERT', 'Ouvert'
    CLOTURE = 'CLOTURE', 'Clôturé'
