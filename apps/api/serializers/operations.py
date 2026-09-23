from rest_framework import serializers

from apps.operations.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id', 'montant', 'type_transaction', 'sens', 'compte',
            'compte_contrepartie', 'reference_virement', 'date_transaction', 'description',
        )
