from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.api.perimetre import PerimetreMixin, banque_agent
from apps.api.permissions import IsPersonnel
from apps.api.serializers.operations import TransactionSerializer
from apps.comptes.models import Compte
from apps.operations.models import Transaction
from apps.operations.services.enregistrer import enregistrer


class TransactionViewSet(
    PerimetreMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TransactionSerializer
    permission_classes = [IsPersonnel]
    champ_banque = 'compte__client__banque_id'

    def get_queryset(self):
        queryset = self.restreindre(
            Transaction.objects.select_related('compte', 'compte_contrepartie').order_by('-date_transaction', '-id')
        )
        params = self.request.query_params
        if params.get('compte'):
            queryset = queryset.filter(compte_id=params['compte'])
        if params.get('type'):
            queryset = queryset.filter(type_transaction=params['type'])
        if params.get('banque') and banque_agent(self.request.user) is None:
            queryset = queryset.filter(compte__client__banque_id=params['banque'])
        if params.get('date_min'):
            queryset = queryset.filter(date_transaction__date__gte=params['date_min'])
        if params.get('date_max'):
            queryset = queryset.filter(date_transaction__date__lte=params['date_max'])
        if params.get('montant_min'):
            queryset = queryset.filter(montant__gte=params['montant_min'])
        if params.get('montant_max'):
            queryset = queryset.filter(montant__lte=params['montant_max'])
        return queryset

    def create(self, request):
        compte_id = request.data.get('compte')
        agent_banque = banque_agent(request.user)
        if agent_banque is not None and compte_id:
            if not Compte.objects.filter(pk=compte_id, client__banque_id=agent_banque).exists():
                raise PermissionDenied('Ce compte est hors de votre banque.')
        mouvements = enregistrer(
            type_transaction=request.data.get('type_transaction'),
            compte_id=compte_id,
            montant=request.data.get('montant'),
            description=request.data.get('description', ''),
            compte_contrepartie_id=request.data.get('compte_contrepartie'),
            acteur=request.user,
        )
        return Response(self.get_serializer(mouvements, many=True).data, status=status.HTTP_201_CREATED)
