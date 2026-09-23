from django.db import models

from apps.clients.services.numeros import generer_numero
from apps.facturation.enums.facture import StatutEnvoi


class Facture(models.Model):
    numero_facture = models.CharField(max_length=24, unique=True, blank=True)
    transaction = models.ForeignKey(
        'operations.Transaction',
        on_delete=models.PROTECT,
        related_name='factures',
    )
    email_destinataire = models.EmailField()
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    statut_envoi = models.CharField(
        max_length=20,
        choices=StatutEnvoi.choices,
        default=StatutEnvoi.EN_ATTENTE,
    )
    envoye_le = models.DateTimeField(null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'facture'
        ordering = ['-cree_le']

    def save(self, *args, **kwargs):
        if not self.numero_facture:
            self.numero_facture = generer_numero('FAC')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero_facture
