from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api import filtres
from apps.api.perimetre import banque_agent
from apps.api.permissions import IsPersonnel
from apps.banques.models import Banque
from apps.comptes.models import Compte
from apps.operations.enums.transaction import Sens, TypeTransaction
from apps.operations.models import Transaction


def _volume(valeur):
    return f'{valeur or 0:.2f}'


class DashboardView(APIView):
    permission_classes = [IsPersonnel]

    def get(self, request):
        agent_banque = banque_agent(request.user)
        params = request.query_params

        # Un virement a deux écritures : seule la ligne débit est comptée.
        transactions = Transaction.objects.exclude(
            Q(type_transaction=TypeTransaction.VIREMENT) & Q(sens=Sens.CREDIT)
        )
        comptes = Compte.objects.all()
        if agent_banque is not None:
            transactions = transactions.filter(compte__client__banque_id=agent_banque)
            comptes = comptes.filter(client__banque_id=agent_banque)
        agence = filtres.entier(params, 'agence')
        if agence:
            transactions = transactions.filter(compte__client__agence_id=agence)
            comptes = comptes.filter(client__agence_id=agence)
        date_min = filtres.jour(params, 'date_min')
        date_max = filtres.jour(params, 'date_max')
        if date_min:
            transactions = transactions.filter(date_transaction__date__gte=date_min)
        if date_max:
            transactions = transactions.filter(date_transaction__date__lte=date_max)

        par_type = {
            ligne['type_transaction']: ligne
            for ligne in transactions.values('type_transaction').annotate(nombre=Count('id'), volume=Sum('montant'))
        }
        par_statut = {
            ligne['statut']: ligne['nombre']
            for ligne in comptes.values('statut').annotate(nombre=Count('id'))
        }
        par_jour = (
            transactions.annotate(jour=TruncDate('date_transaction'))
            .values('jour')
            .annotate(nombre=Count('id'), volume=Sum('montant'))
            .order_by('jour')
        )

        donnees = {
            'transactions_par_type': [
                {
                    'type': code,
                    'nombre': par_type.get(code, {}).get('nombre', 0),
                    'volume': _volume(par_type.get(code, {}).get('volume')),
                }
                for code in TypeTransaction.values
            ],
            'transactions_par_jour': [
                {'jour': ligne['jour'].isoformat(), 'nombre': ligne['nombre'], 'volume': _volume(ligne['volume'])}
                for ligne in par_jour
            ],
            'comptes_par_statut': [
                {'statut': statut, 'nombre': par_statut.get(statut, 0)}
                for statut in ('OUVERT', 'CLOTURE')
            ],
        }
        if agent_banque is None:
            top = Banque.objects.annotate(nombre_clients=Count('clients')).order_by('-nombre_clients', 'nom')[:15]
            donnees['top_banques'] = [
                {'id': banque.id, 'nom': banque.nom, 'nombre_clients': banque.nombre_clients}
                for banque in top
            ]
        return Response(donnees)
