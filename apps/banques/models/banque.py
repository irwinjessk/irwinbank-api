from django.db import models


class Banque(models.Model):
    nom = models.CharField(max_length=150)
    pays = models.CharField(max_length=80, db_index=True)
    ville = models.CharField(max_length=80, db_index=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'banque'
        ordering = ['nom']

    def __str__(self):
        return self.nom
