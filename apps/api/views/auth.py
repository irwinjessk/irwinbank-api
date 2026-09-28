from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.perimetre import agence_agent, banque_agent, client_de, role_de


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(status=204)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = agence_agent(request.user)
        client = client_de(request.user)
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'role': role_de(request.user),
            'banque_id': banque_agent(request.user),
            'agence_id': agence_id,
            'agence_nom': request.user.profil.agence.nom if agence_id else None,
            'client': {
                'id': client.id,
                'nom_complet': f'{client.prenom} {client.nom}',
                'numero_client': client.numero_client,
                'banque_nom': client.banque.nom,
                'archive': client.archive,
            } if client else None,
        })
