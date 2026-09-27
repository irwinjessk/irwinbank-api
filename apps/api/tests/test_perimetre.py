from django.contrib.auth import get_user_model

from apps.api.tests.support import ApiTestCase


class PerimetreAgentTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.sienne = self.creer_banque(nom='Sienne')
        self.autre = self.creer_banque(nom='Autre')
        self.compte_sien = self.creer_compte(self.creer_client(self.sienne, email='a@example.com'), solde='100.00')
        self.compte_autre = self.creer_compte(self.creer_client(self.autre, email='b@example.com'), solde='100.00')
        self.connecter_agent(self.sienne)

    def test_agent_ne_voit_que_sa_banque(self):
        banques = self.client.get('/api/v1/banques/').data
        self.assertEqual([b['nom'] for b in banques], ['Sienne'])
        self.assertEqual(len(self.client.get('/api/v1/clients/').data), 1)
        self.assertEqual(len(self.client.get('/api/v1/comptes/').data), 1)

    def test_agent_ne_cree_pas_de_banque(self):
        response = self.client.post('/api/v1/banques/', {'nom': 'X', 'pays': 'CI', 'ville': 'Abidjan'})
        self.assertEqual(response.status_code, 403)

    def test_agent_ne_cree_pas_de_client_dans_une_autre_banque(self):
        response = self.client.post('/api/v1/clients/', {
            'nom': 'N', 'prenom': 'P', 'email': 'c@example.com', 'banque': self.autre.id,
        })
        self.assertEqual(response.status_code, 403)

    def test_agent_ne_debite_pas_un_compte_hors_banque(self):
        response = self.client.post('/api/v1/transactions/', {
            'type_transaction': 'RETRAIT', 'compte': self.compte_autre.id, 'montant': '10.00',
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_agent_peut_virer_vers_une_autre_banque(self):
        response = self.client.post('/api/v1/transactions/', {
            'type_transaction': 'VIREMENT', 'compte': self.compte_sien.id,
            'compte_contrepartie': self.compte_autre.id, 'montant': '10.00',
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_compte_hors_banque_introuvable(self):
        response = self.client.get(f'/api/v1/comptes/{self.compte_autre.id}/')
        self.assertEqual(response.status_code, 404)

    def test_utilisateur_sans_role_refuse(self):
        anonyme = get_user_model().objects.create_user(username='sansrole', password='MotDePasse2026!')
        self.client.force_authenticate(anonyme)
        self.assertEqual(self.client.get('/api/v1/clients/').status_code, 403)

    def test_superutilisateur_sans_profil_est_admin(self):
        root = get_user_model().objects.create_superuser(username='root', password='MotDePasse2026!')
        self.client.force_authenticate(root)
        self.assertEqual(self.client.get('/api/v1/auth/me').data['role'], 'ADMIN')
        self.assertEqual(len(self.client.get('/api/v1/banques/').data), 2)
