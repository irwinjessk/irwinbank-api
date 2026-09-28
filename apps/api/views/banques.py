from django.db import transaction
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.api.exports import Colonne, ExportMixin
from apps.api.perimetre import PerimetreMixin, banque_agent
from apps.api.permissions import IsAdminOrReadOnly
from apps.api.serializers.banques import BanqueSerializer
from apps.banques.models import Banque
from apps.courrier.services.bienvenue import envoyer_bienvenue_banque


class BanqueViewSet(ExportMixin, PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = BanqueSerializer
    permission_classes = [IsAdminOrReadOnly]
    champ_banque = 'id'
    export_nom = 'banques'
    export_titre = 'Banques'
    export_filtres = {'pays': ('Pays', None), 'ville': ('Ville', None)}
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        queryset = self.restreindre(Banque.objects.annotate(nombre_clients=Count('clients')))
        pays = self.request.query_params.get('pays')
        ville = self.request.query_params.get('ville')
        if pays:
            queryset = queryset.filter(pays__icontains=pays)
        if ville:
            queryset = queryset.filter(ville__icontains=ville)
        return queryset

    def export_colonnes(self):
        return [
            Colonne('Nom', lambda b: b.nom, largeur=2),
            Colonne('Pays', lambda b: b.pays, largeur=1.3),
            Colonne('Ville', lambda b: b.ville, largeur=1.3),
            Colonne('E-mail', lambda b: b.email, largeur=2.2),
            Colonne('Clients', lambda b: b.nombre_clients, 'entier', 0.8),
            Colonne('Statut', lambda b: 'Active' if b.actif else 'Désactivée', largeur=1),
            Colonne('Créée le', lambda b: b.date_creation, 'date', 1),
        ]

    def export_resume(self, banques):
        return [('Banques', str(len(banques))), ('Clients au total', str(sum(b.nombre_clients for b in banques)))]

    def perform_create(self, serializer):
        banque = serializer.save()
        acteur = self.request.user
        transaction.on_commit(lambda: envoyer_bienvenue_banque(banque, acteur))

    @action(detail=False, methods=['get'])
    def top(self, request):
        if banque_agent(request.user) is not None:
            raise PermissionDenied('Le classement des banques est réservé à un administrateur.')
        banques = self.get_queryset().order_by('-nombre_clients', 'nom')[:15]
        return Response(self.get_serializer(banques, many=True).data)
