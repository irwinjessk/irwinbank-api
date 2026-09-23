from rest_framework import serializers

from apps.facturation.models import Facture


class FactureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facture
        fields = (
            'id', 'numero_facture', 'transaction', 'email_destinataire',
            'montant', 'statut_envoi', 'envoye_le', 'cree_le',
        )
