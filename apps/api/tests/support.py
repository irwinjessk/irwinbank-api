from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounts.enums.role import Role
from apps.accounts.models import Profil
from apps.banques.models import Agence, Banque
from apps.banques.models.agence import AGENCE_PRINCIPALE
from apps.clients.models import Client
from apps.comptes.models import Compte


class ApiTestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='MotDePasse2026!')
        Profil.objects.create(user=self.user, role=Role.ADMIN)
        self.client.force_authenticate(self.user)

    def connecter_agent(self, banque, agence=None):
        agence = agence or self.agence_principale(banque)
        agent = get_user_model().objects.create_user(username=f'agent{banque.id}-{agence.id}', password='MotDePasse2026!')
        Profil.objects.create(user=agent, role=Role.AGENT, banque=banque, agence=agence)
        self.client.force_authenticate(agent)
        return agent

    def creer_banque(self, nom='ADA BANK', pays='Côte d\'Ivoire', ville='Abidjan'):
        return Banque.objects.create(nom=nom, pays=pays, ville=ville)

    def agence_principale(self, banque):
        return Agence.objects.get(banque=banque, nom=AGENCE_PRINCIPALE)

    def creer_agence(self, banque, nom='Cocody'):
        return Agence.objects.create(banque=banque, nom=nom, ville=banque.ville)

    def creer_client(self, banque, email='aya@example.com', nom='Kouassi', agence=None):
        agence = agence or self.agence_principale(banque)
        return Client.objects.create(nom=nom, prenom='Aya', email=email, banque=banque, agence=agence)

    def creer_compte(self, client, solde='0.00'):
        return Compte.objects.create(client=client, type_compte='COURANT', solde=solde)
