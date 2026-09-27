from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api import filtres
from apps.api.perimetre import PerimetreMixin
from apps.api.permissions import IsPersonnel
from apps.api.serializers.factures import FactureSerializer
from apps.audit.services.journal import tracer
from apps.facturation.models import Facture
from apps.facturation.services.envoi_facture import envoyer_facture


class FactureViewSet(PerimetreMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = FactureSerializer
    permission_classes = [IsPersonnel]
    champ_banque = 'transaction__compte__client__banque_id'

    def get_queryset(self):
        queryset = self.restreindre(
            Facture.objects.select_related('transaction', 'transaction__compte', 'transaction__compte__client__banque')
        )
        params = self.request.query_params
        transaction = filtres.entier(params, 'transaction')
        if transaction:
            queryset = queryset.filter(transaction_id=transaction)
        if params.get('statut_envoi'):
            queryset = queryset.filter(statut_envoi=params['statut_envoi'])
        if params.get('numero_facture'):
            queryset = queryset.filter(numero_facture__icontains=params['numero_facture'])
        return queryset

    @action(detail=True, methods=['post'])
    def renvoyer(self, request, pk=None):
        facture = envoyer_facture(self.get_object())
        tracer(
            acteur=request.user,
            action='facture.renvoyee',
            entite='facture',
            entite_id=facture.id,
            resume=f'Renvoi de {facture.numero_facture} : {facture.statut_envoi}',
            banque=facture.transaction.compte.client.banque,
        )
        return Response(self.get_serializer(facture).data)
