from django.db.models import Q
from rest_framework import viewsets

from apps.api.perimetre import PerimetreMixin, verifier_banque
from apps.api.permissions import IsPersonnel
from apps.api.serializers.clients import ClientSerializer
from apps.clients.models import Client


class ClientViewSet(PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsPersonnel]

    def get_queryset(self):
        queryset = self.restreindre(Client.objects.select_related('banque'))
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

    def perform_create(self, serializer):
        verifier_banque(self.request.user, serializer.validated_data['banque'].id)
        serializer.save()

    def perform_update(self, serializer):
        banque = serializer.validated_data.get('banque')
        if banque:
            verifier_banque(self.request.user, banque.id)
        serializer.save()
