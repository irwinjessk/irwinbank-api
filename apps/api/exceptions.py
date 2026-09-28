from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


class Conflit(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Opération impossible dans l’état actuel.'
    default_code = 'conflit'


def gestionnaire_exceptions(exc, context):
    if isinstance(exc, ProtectedError):
        return Response(
            {'detail': 'Suppression impossible : des enregistrements liés existent.'},
            status=status.HTTP_409_CONFLICT,
        )
    return exception_handler(exc, context)
