from decimal import Decimal

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api import filtres
from apps.api.exceptions import Conflit
from apps.api.exports import Colonne, ExportMixin
from apps.api.perimetre import PerimetreMixin, verifier_agence, verifier_banque
from apps.api.permissions import IsPersonnel
from apps.api.serializers.comptes import CompteSerializer
from apps.clients.models import Client
from apps.comptes.enums.compte import StatutCompte
from apps.comptes.models import Compte
from apps.comptes.services.cloture import cloturer


class CompteViewSet(ExportMixin, PerimetreMixin, viewsets.ModelViewSet):
    serializer_class = CompteSerializer
    permission_classes = [IsPersonnel]
    champ_banque = 'client__banque_id'
    export_nom = 'comptes'
    export_titre = 'Comptes'
    export_filtres = {'client': ('Client', lambda valeur: str(Client.objects.filter(pk=valeur).first() or f'#{valeur}'))}
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        queryset = self.restreindre(Compte.objects.select_related('client', 'client__banque', 'client__agence'))
        client = filtres.entier(self.request.query_params, 'client')
        if client:
            queryset = queryset.filter(client_id=client)
        return queryset

    def export_colonnes(self):
        return [
            Colonne('Numéro', lambda c: c.numero_compte, largeur=1.6),
            Colonne('Type', lambda c: c.get_type_compte_display(), largeur=0.8),
            Colonne('Titulaire', lambda c: f'{c.client.prenom} {c.client.nom}', largeur=1.6),
            Colonne('N° client', lambda c: c.client.numero_client, largeur=1.4),
            Colonne('Banque', lambda c: c.client.banque.nom, largeur=1.3),
            Colonne('Agence', lambda c: c.client.agence.nom, largeur=1.3),
            Colonne('Solde', lambda c: c.solde, 'montant', 1.2),
            Colonne('Statut', lambda c: c.get_statut_display(), largeur=0.8),
            Colonne('Ouvert le', lambda c: c.date_ouverture, 'date', 0.9),
            Colonne('Clôturé le', lambda c: c.date_cloture, 'date', 0.9),
            Colonne('Motif de clôture', lambda c: c.get_motif_cloture_display() if c.motif_cloture else '', largeur=1.3),
        ]

    def export_resume(self, comptes):
        ouverts = [c for c in comptes if c.statut == StatutCompte.OUVERT]
        return [
            ('Comptes', str(len(comptes))),
            ('dont ouverts', str(len(ouverts))),
            ('Encours des comptes ouverts', sum((c.solde for c in ouverts), Decimal('0'))),
        ]

    def perform_create(self, serializer):
        client = serializer.validated_data['client']
        verifier_banque(self.request.user, client.banque_id)
        verifier_agence(self.request.user, client.agence_id)
        if client.archive:
            raise Conflit('Ce client est archivé : restaurez sa fiche avant d’ouvrir un compte.')
        serializer.save()

    def perform_update(self, serializer):
        verifier_agence(self.request.user, serializer.instance.client.agence_id)
        client = serializer.validated_data.get('client')
        if client:
            verifier_banque(self.request.user, client.banque_id)
            verifier_agence(self.request.user, client.agence_id)
        serializer.save()

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
