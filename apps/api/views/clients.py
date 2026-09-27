from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.serializers.clients import ClientSerializer
from apps.clients.models import Client


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Client.objects.select_related('banque')
        banque = self.request.query_params.get('banque')
        nom = self.request.query_params.get('nom')
        email = self.request.query_params.get('email')
        numero = self.request.query_params.get('numero_client')
        if banque:
            queryset = queryset.filter(banque_id=banque)
        if nom:
            queryset = queryset.filter(Q(nom__icontains=nom) | Q(prenom__icontains=nom))
        if email:
            queryset = queryset.filter(email__icontains=email)
        if numero:
            queryset = queryset.filter(numero_client__icontains=numero)
        return queryset
