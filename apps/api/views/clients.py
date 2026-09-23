from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.serializers.clients import ClientSerializer
from apps.clients.models import Client


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.select_related('banque')
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
