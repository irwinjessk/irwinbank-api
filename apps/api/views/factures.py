from decimal import Decimal

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api import filtres
from apps.api.exports import Colonne, ExportMixin
from apps.api.exports.mixin import choix, libelle_de
from apps.api.perimetre import PerimetreMixin
from apps.comptes.models import Compte
from apps.facturation.enums.facture import StatutEnvoi
from apps.api.permissions import IsPersonnel
from apps.api.serializers.factures import FactureSerializer
from apps.audit.services.journal import tracer
from apps.facturation.models import Facture
from apps.facturation.services.envoi_facture import envoyer_facture


class FactureViewSet(ExportMixin, PerimetreMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = FactureSerializer
    permission_classes = [IsPersonnel]
    champ_banque = 'transaction__compte__client__banque_id'
    export_nom = 'factures'
    export_titre = 'Factures'
    export_filtres = {
        'compte': ('Compte', libelle_de(Compte, 'numero_compte')),
        'statut_envoi': ('Envoi', choix(dict(StatutEnvoi.choices))),
        'numero_facture': ('Numéro', None),
    }

    def get_queryset(self):
        queryset = self.restreindre(
            Facture.objects.select_related('transaction', 'transaction__compte', 'transaction__compte__client__banque')
        )
        params = self.request.query_params
        transaction = filtres.entier(params, 'transaction')
        compte = filtres.entier(params, 'compte')
        if transaction:
            queryset = queryset.filter(transaction_id=transaction)
        if compte:
            queryset = queryset.filter(transaction__compte_id=compte)
        if params.get('statut_envoi'):
            queryset = queryset.filter(statut_envoi=params['statut_envoi'])
        if params.get('numero_facture'):
            queryset = queryset.filter(numero_facture__icontains=params['numero_facture'])
        return queryset

    def export_colonnes(self):
        return [
            Colonne('Numéro', lambda f: f.numero_facture, largeur=1.5),
            Colonne('Date', lambda f: f.cree_le, 'datetime', 1.2),
            Colonne('Opération', lambda f: f.transaction.get_type_transaction_display(), largeur=0.9),
            Colonne('Compte', lambda f: f.transaction.compte.numero_compte, largeur=1.6),
            Colonne('Montant', lambda f: f.montant, 'montant', 1.1),
            Colonne('Destinataire', lambda f: f.email_destinataire, largeur=2),
            Colonne('Envoi', lambda f: f.get_statut_envoi_display(), largeur=0.8),
            Colonne('Envoyée le', lambda f: f.envoye_le, 'datetime', 1.2),
        ]

    def export_resume(self, factures):
        return [
            ('Factures', str(len(factures))),
            ('Montant total', sum((f.montant for f in factures), Decimal('0'))),
            ('Envois en échec', str(sum(1 for f in factures if f.statut_envoi == StatutEnvoi.ECHEC))),
        ]

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
