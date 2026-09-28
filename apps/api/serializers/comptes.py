from decimal import Decimal

from rest_framework import serializers

from apps.comptes.models import Compte


class CompteSerializer(serializers.ModelSerializer):
    agence = serializers.IntegerField(source='client.agence_id', read_only=True)
    agence_nom = serializers.CharField(source='client.agence.nom', read_only=True)
    client_nom = serializers.SerializerMethodField()
    client_numero = serializers.CharField(source='client.numero_client', read_only=True)
    banque_nom = serializers.CharField(source='client.banque.nom', read_only=True)
    motif_cloture_libelle = serializers.CharField(source='get_motif_cloture_display', read_only=True)
    solde_initial = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'), required=False, write_only=True,
        error_messages={'min_value': 'Le solde initial ne peut pas être négatif.'},
    )

    class Meta:
        model = Compte
        fields = (
            'id', 'numero_compte', 'solde', 'type_compte', 'client', 'client_nom', 'client_numero', 'banque_nom', 'agence', 'agence_nom',
            'date_ouverture', 'statut', 'date_cloture', 'motif_cloture', 'motif_cloture_libelle', 'solde_initial',
        )
        read_only_fields = ('numero_compte', 'solde', 'date_ouverture', 'statut', 'date_cloture', 'motif_cloture')

    def get_client_nom(self, compte):
        return f'{compte.client.prenom} {compte.client.nom}'
