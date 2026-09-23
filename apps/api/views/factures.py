from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.serializers.factures import FactureSerializer
from apps.facturation.models import Facture


class FactureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Facture.objects.all()
    serializer_class = FactureSerializer
    permission_classes = [IsAuthenticated]
