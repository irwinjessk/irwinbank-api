from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.api import filtres
from apps.api.perimetre import PerimetreMixin, agence_agent, banque_agent
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
        compte = filtres.entier(params, 'compte')
        client = filtres.entier(params, 'client')
        banque = filtres.entier(params, 'banque')
        date_min = filtres.jour(params, 'date_min')
        date_max = filtres.jour(params, 'date_max')
        montant_min = filtres.decimal(params, 'montant_min')
        montant_max = filtres.decimal(params, 'montant_max')
        if compte:
            queryset = queryset.filter(compte_id=compte)
        if client:
            queryset = queryset.filter(compte__client_id=client)
        if params.get('type'):
            queryset = queryset.filter(type_transaction=params['type'])
        if banque and banque_agent(self.request.user) is None:
            queryset = queryset.filter(compte__client__banque_id=banque)
        if date_min:
            queryset = queryset.filter(date_transaction__date__gte=date_min)
        if date_max:
            queryset = queryset.filter(date_transaction__date__lte=date_max)
        if montant_min is not None:
            queryset = queryset.filter(montant__gte=montant_min)
        if montant_max is not None:
            queryset = queryset.filter(montant__lte=montant_max)
        return queryset

    def create(self, request):
        compte_id = filtres.entier(request.data, 'compte')
        contrepartie_id = filtres.entier(request.data, 'compte_contrepartie')
        agent_banque = banque_agent(request.user)
        if agent_banque is not None and compte_id:
            compte = Compte.objects.filter(pk=compte_id, client__banque_id=agent_banque).select_related('client').first()
            if compte is None:
                raise PermissionDenied('Ce compte est hors de votre banque.')
            if request.data.get('type_transaction') == 'VIREMENT' and compte.client.agence_id != agence_agent(request.user):
                raise PermissionDenied('Un virement doit être initié par l’agence du client : seuls dépôts et retraits sont possibles au guichet.')
        mouvements = enregistrer(
            type_transaction=request.data.get('type_transaction'),
            compte_id=compte_id,
            montant=request.data.get('montant'),
            description=request.data.get('description', ''),
            compte_contrepartie_id=contrepartie_id,
            acteur=request.user,
        )
        return Response(self.get_serializer(mouvements, many=True).data, status=status.HTTP_201_CREATED)
