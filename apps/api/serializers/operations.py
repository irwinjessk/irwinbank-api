from rest_framework import serializers

from apps.operations.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    compte_numero = serializers.CharField(source='compte.numero_compte', read_only=True)
    contrepartie_numero = serializers.CharField(source='compte_contrepartie.numero_compte', read_only=True, default=None)

    class Meta:
        model = Transaction
        fields = (
            'id', 'montant', 'type_transaction', 'sens', 'compte', 'compte_numero',
            'compte_contrepartie', 'contrepartie_numero', 'reference_virement', 'date_transaction', 'description',
        )
