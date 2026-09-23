from rest_framework import serializers

from apps.comptes.models import Compte


class CompteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compte
        fields = (
            'id', 'numero_compte', 'solde', 'type_compte', 'client',
            'date_ouverture', 'statut', 'date_cloture',
        )
        read_only_fields = ('numero_compte', 'solde', 'date_ouverture', 'statut', 'date_cloture')
