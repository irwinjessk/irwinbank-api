from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api import filtres
from apps.api.perimetre import PerimetreMixin, verifier_agence, verifier_banque
from apps.api.permissions import IsPersonnel
from apps.api.serializers.comptes import CompteSerializer
from apps.comptes.models import Compte
from apps.comptes.services.cloture import cloturer


class CompteViewSet(PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = CompteSerializer
    permission_classes = [IsPersonnel]
    champ_banque = 'client__banque_id'

    def get_queryset(self):
        queryset = self.restreindre(Compte.objects.select_related('client', 'client__banque', 'client__agence'))
        client = filtres.entier(self.request.query_params, 'client')
        if client:
            queryset = queryset.filter(client_id=client)
        return queryset

    def perform_create(self, serializer):
        client = serializer.validated_data['client']
        verifier_banque(self.request.user, client.banque_id)
        verifier_agence(self.request.user, client.agence_id)
        serializer.save()

    def perform_update(self, serializer):
        verifier_agence(self.request.user, serializer.instance.client.agence_id)
        client = serializer.validated_data.get('client')
        if client:
            verifier_banque(self.request.user, client.banque_id)
            verifier_agence(self.request.user, client.agence_id)
        serializer.save()

    def perform_destroy(self, instance):
        verifier_agence(self.request.user, instance.client.agence_id)
        instance.delete()

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        compte = self.get_object()
        verifier_agence(request.user, compte.client.agence_id)
        compte = cloturer(
            compte,
            motif=request.data.get('motif'),
            mode_restitution=request.data.get('mode_restitution'),
            compte_destinataire_id=filtres.entier(request.data, 'compte_destinataire'),
            acteur=request.user,
        )
        return Response(self.get_serializer(compte).data)
