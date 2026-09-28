from django.db import models


class TypeCompte(models.TextChoices):
    COURANT = 'COURANT', 'Courant'
    EPARGNE = 'EPARGNE', 'Épargne'


class StatutCompte(models.TextChoices):
    OUVERT = 'OUVERT', 'Ouvert'
    CLOTURE = 'CLOTURE', 'Clôturé'


class MotifCloture(models.TextChoices):
    DEMANDE_CLIENT = 'DEMANDE_CLIENT', 'Demande du client'
    DECISION_BANQUE = 'DECISION_BANQUE', 'Décision de la banque'


class ModeRestitution(models.TextChoices):
    VIREMENT = 'VIREMENT', 'Virement vers un autre compte'
    ESPECES = 'ESPECES', 'Remise en espèces'
    CHEQUE = 'CHEQUE', 'Chèque de banque'
