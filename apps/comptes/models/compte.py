from django.db import models

from apps.clients.services.numeros import generer_numero
from apps.comptes.enums.compte import StatutCompte, TypeCompte


class Compte(models.Model):
    numero_compte = models.CharField(max_length=24, unique=True, blank=True)
    solde = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    type_compte = models.CharField(max_length=20, choices=TypeCompte.choices)
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        related_name='comptes',
    )
    date_ouverture = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=20,
        choices=StatutCompte.choices,
        default=StatutCompte.OUVERT,
    )
    date_cloture = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compte'
        ordering = ['-date_ouverture']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(solde__gte=0),
                name='compte_solde_non_negatif',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.numero_compte:
            self.numero_compte = generer_numero('CPT')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero_compte
