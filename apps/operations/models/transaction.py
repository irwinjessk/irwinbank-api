from django.db import models

from apps.operations.enums.transaction import Sens, TypeTransaction


class Transaction(models.Model):
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    type_transaction = models.CharField(max_length=20, choices=TypeTransaction.choices)
    sens = models.CharField(max_length=10, choices=Sens.choices)
    compte = models.ForeignKey(
        'comptes.Compte',
        on_delete=models.PROTECT,
        related_name='transactions',
    )
    compte_contrepartie = models.ForeignKey(
        'comptes.Compte',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='transactions_contrepartie',
    )
    reference_virement = models.UUIDField(null=True, blank=True, db_index=True)
    date_transaction = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'transaction'
        ordering = ['-date_transaction']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(montant__gt=0),
                name='transaction_montant_positif',
            ),
        ]

    def __str__(self):
        return f'{self.type_transaction} {self.montant}'
