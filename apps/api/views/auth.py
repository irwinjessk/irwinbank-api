from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(status=204)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profil = getattr(request.user, 'profil', None)
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'role': profil.role if profil else None,
            'banque_id': profil.banque_id if profil else None,
        })
