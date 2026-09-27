from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounts.enums.role import Role
from apps.accounts.models import Profil
from apps.banques.models import Banque
from apps.clients.models import Client
from apps.comptes.models import Compte


class ApiTestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='MotDePasse2026!')
        Profil.objects.create(user=self.user, role=Role.ADMIN)
        self.client.force_authenticate(self.user)

    def creer_banque(self, nom='ADA BANK', pays='Côte d\'Ivoire', ville='Abidjan'):
        return Banque.objects.create(nom=nom, pays=pays, ville=ville)

    def creer_client(self, banque, email='aya@example.com', nom='Kouassi'):
        return Client.objects.create(nom=nom, prenom='Aya', email=email, banque=banque)

    def creer_compte(self, client, solde='0.00'):
        return Compte.objects.create(client=client, type_compte='COURANT', solde=solde)
