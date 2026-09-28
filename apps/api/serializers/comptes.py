from rest_framework import serializers

from apps.comptes.models import Compte


class CompteSerializer(serializers.ModelSerializer):
    agence = serializers.IntegerField(source='client.agence_id', read_only=True)
    agence_nom = serializers.CharField(source='client.agence.nom', read_only=True)

    class Meta:
        model = Compte
        fields = (
            'id', 'numero_compte', 'solde', 'type_compte', 'client', 'agence', 'agence_nom',
            'date_ouverture', 'statut', 'date_cloture',
        )
        read_only_fields = ('numero_compte', 'solde', 'date_ouverture', 'statut', 'date_cloture')
