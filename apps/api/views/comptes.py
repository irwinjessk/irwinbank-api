from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api import filtres
from apps.api.perimetre import PerimetreMixin, verifier_banque
from apps.api.permissions import IsPersonnel
from apps.api.serializers.comptes import CompteSerializer
from apps.comptes.models import Compte
from apps.comptes.services.cloture import cloturer


class CompteViewSet(PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = CompteSerializer
    permission_classes = [IsPersonnel]
    champ_banque = 'client__banque_id'

    def get_queryset(self):
        queryset = self.restreindre(Compte.objects.select_related('client', 'client__banque'))
        client = filtres.entier(self.request.query_params, 'client')
        if client:
            queryset = queryset.filter(client_id=client)
        return queryset

    def perform_create(self, serializer):
        verifier_banque(self.request.user, serializer.validated_data['client'].banque_id)
        serializer.save()

    def perform_update(self, serializer):
        client = serializer.validated_data.get('client')
        if client:
            verifier_banque(self.request.user, client.banque_id)
        serializer.save()

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        compte = cloturer(
            self.get_object(),
            motif=request.data.get('motif'),
            mode_restitution=request.data.get('mode_restitution'),
            compte_destinataire_id=filtres.entier(request.data, 'compte_destinataire'),
            acteur=request.user,
        )
        return Response(self.get_serializer(compte).data)
