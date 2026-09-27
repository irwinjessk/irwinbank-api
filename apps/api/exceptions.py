from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def gestionnaire_exceptions(exc, context):
    if isinstance(exc, ProtectedError):
        return Response(
            {'detail': 'Suppression impossible : des enregistrements liés existent.'},
            status=status.HTTP_409_CONFLICT,
        )
    return exception_handler(exc, context)
