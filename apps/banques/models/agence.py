from django.db import models

AGENCE_PRINCIPALE = 'Agence principale'


class Agence(models.Model):
    nom = models.CharField(max_length=120)
    ville = models.CharField(max_length=80)
    banque = models.ForeignKey(
        'banques.Banque',
        on_delete=models.PROTECT,
        related_name='agences',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'agence'
        ordering = ['banque__nom', 'nom']
        constraints = [
            models.UniqueConstraint(fields=['banque', 'nom'], name='agence_nom_unique_par_banque'),
        ]

    @property
    def est_principale(self):
        return self.nom == AGENCE_PRINCIPALE

    def __str__(self):
        return f'{self.banque} · {self.nom}'
