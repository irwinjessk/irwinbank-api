from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.serializers.operations import TransactionSerializer
from apps.operations.models import Transaction


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.select_related('compte')
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
