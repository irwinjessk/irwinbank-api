from apps.api.tests.support import ApiTestCase
from apps.audit.models import JournalAudit
from apps.banques.models import Agence


class AgencesTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.banque = self.creer_banque()
        self.principale = self.agence_principale(self.banque)
        self.cocody = self.creer_agence(self.banque)

    def test_une_banque_cree_son_agence_principale(self):
        self.assertEqual(self.principale.ville, 'Abidjan')
        self.assertEqual(Agence.objects.filter(banque=self.banque).count(), 2)

    def test_admin_cree_une_agence_et_refuse_un_doublon(self):
        response = self.client.post('/api/v1/agences/', {'nom': 'Plateau', 'ville': 'Abidjan', 'banque': self.banque.id}, format='json')
        self.assertEqual(response.status_code, 201)
        doublon = self.client.post('/api/v1/agences/', {'nom': 'plateau', 'ville': 'Abidjan', 'banque': self.banque.id}, format='json')
        self.assertEqual(doublon.status_code, 400)

    def test_agent_lit_les_agences_de_sa_banque_sans_les_modifier(self):
        autre = self.creer_banque(nom='Autre')
        self.connecter_agent(self.banque)
        response = self.client.get('/api/v1/agences/')
        self.assertEqual({agence['banque'] for agence in response.data}, {self.banque.id})
        self.assertEqual(self.client.post('/api/v1/agences/', {'nom': 'X', 'ville': 'Y', 'banque': self.banque.id}, format='json').status_code, 403)
        self.assertEqual(self.client.get(f'/api/v1/agences/{self.agence_principale(autre).id}/').status_code, 404)

    def test_client_cree_par_un_agent_est_rattache_a_son_agence(self):
        agent = self.connecter_agent(self.banque, self.cocody)
        response = self.client.post('/api/v1/clients/', {'nom': 'Koné', 'prenom': 'Awa', 'email': 'awa@example.com', 'banque': self.banque.id}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual((response.data['agence'], response.data['agence_nom']), (self.cocody.id, 'Cocody'))
        self.assertEqual(response.data['conseiller'], agent.id)

    def test_client_cree_par_admin_va_a_l_agence_principale(self):
        response = self.client.post('/api/v1/clients/', {'nom': 'Koné', 'prenom': 'Awa', 'email': 'awa@example.com', 'banque': self.banque.id}, format='json')
        self.assertEqual(response.data['agence'], self.principale.id)
        self.assertIsNone(response.data['conseiller'])

    def test_agent_ne_modifie_pas_un_client_d_une_autre_agence(self):
        client = self.creer_client(self.banque)
        self.connecter_agent(self.banque, self.cocody)
        self.assertEqual(self.client.get(f'/api/v1/clients/{client.id}/').status_code, 200)
        response = self.client.patch(f'/api/v1/clients/{client.id}/', {'nom': 'Pirate'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post('/api/v1/comptes/', {'client': client.id, 'type_compte': 'COURANT'}, format='json').status_code, 403)

    def test_guichet_depot_et_retrait_possibles_mais_pas_virement(self):
        client = self.creer_client(self.banque)
        compte = self.creer_compte(client, '100.00')
        cible = self.creer_compte(self.creer_client(self.banque, email='b@example.com', agence=self.cocody))
        self.connecter_agent(self.banque, self.cocody)
        depot = self.client.post('/api/v1/transactions/', {'type_transaction': 'DEPOT', 'compte': compte.id, 'montant': '50.00'}, format='json')
        retrait = self.client.post('/api/v1/transactions/', {'type_transaction': 'RETRAIT', 'compte': compte.id, 'montant': '20.00'}, format='json')
        virement = self.client.post(
            '/api/v1/transactions/',
            {'type_transaction': 'VIREMENT', 'compte': compte.id, 'compte_contrepartie': cible.id, 'montant': '10.00'},
            format='json',
        )
        self.assertEqual((depot.status_code, retrait.status_code, virement.status_code), (201, 201, 403))

    def test_changer_d_agence_garde_numero_et_comptes_et_trace(self):
        client = self.creer_client(self.banque)
        compte = self.creer_compte(client)
        agent = self.connecter_agent(self.banque)
        client.conseiller = agent
        client.save()
        numero = client.numero_client
        response = self.client.post(f'/api/v1/clients/{client.id}/changer-agence/', {'agence': self.cocody.id}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.data['agence'], response.data['numero_client']), (self.cocody.id, numero))
        self.assertIsNone(response.data['conseiller'])
        compte.refresh_from_db()
        self.assertEqual(compte.client_id, client.id)
        self.assertTrue(JournalAudit.objects.filter(action='client.agence_changee', entite_id=client.id).exists())
        retour = self.client.post(f'/api/v1/clients/{client.id}/changer-agence/', {'agence': self.principale.id}, format='json')
        self.assertEqual(retour.status_code, 403)

    def test_changer_d_agence_refuse_une_autre_banque(self):
        client = self.creer_client(self.banque)
        autre = self.creer_banque(nom='Autre')
        response = self.client.post(f'/api/v1/clients/{client.id}/changer-agence/', {'agence': self.agence_principale(autre).id}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_conseiller_doit_appartenir_a_l_agence_du_client(self):
        client = self.creer_client(self.banque)
        agent_cocody = self.connecter_agent(self.banque, self.cocody)
        self.client.force_authenticate(self.user)
        response = self.client.patch(f'/api/v1/clients/{client.id}/', {'conseiller': agent_cocody.id}, format='json')
        self.assertEqual(response.status_code, 400)
        agents = self.client.get(f'/api/v1/agences/{self.cocody.id}/agents/')
        self.assertEqual([agent['id'] for agent in agents.data], [agent_cocody.id])

    def test_me_expose_l_agence_de_l_agent(self):
        self.connecter_agent(self.banque, self.cocody)
        response = self.client.get('/api/v1/auth/me')
        self.assertEqual((response.data['agence_id'], response.data['agence_nom']), (self.cocody.id, 'Cocody'))

    def test_designer_un_conseiller_aux_clients_sans_conseiller(self):
        sans = self.creer_client(self.banque, agence=self.cocody)
        agent = self.connecter_agent(self.banque, self.cocody)
        suivi = self.creer_client(self.banque, email='suivi@example.com', agence=self.cocody)
        suivi.conseiller = agent
        suivi.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(f'/api/v1/clients/?agence={self.cocody.id}&sans_conseiller=1')
        self.assertEqual([client['id'] for client in response.data], [sans.id])
        designation = self.client.patch(f'/api/v1/clients/{sans.id}/', {'conseiller': agent.id}, format='json')
        self.assertEqual((designation.status_code, designation.data['conseiller_nom']), (200, agent.username))
        self.assertTrue(JournalAudit.objects.filter(action='client.modifie', entite_id=sans.id).exists())

    def test_dashboard_filtre_par_agence(self):
        compte = self.creer_compte(self.creer_client(self.banque, agence=self.cocody), '0.00')
        self.creer_compte(self.creer_client(self.banque, email='p@example.com'), '0.00')
        self.client.post('/api/v1/transactions/', {'type_transaction': 'DEPOT', 'compte': compte.id, 'montant': '40.00'}, format='json')
        response = self.client.get(f'/api/v1/dashboard/?agence={self.cocody.id}')
        depots = next(ligne for ligne in response.data['transactions_par_type'] if ligne['type'] == 'DEPOT')
        self.assertEqual((depots['nombre'], depots['volume']), (1, '40.00'))
        ouverts = next(ligne for ligne in response.data['comptes_par_statut'] if ligne['statut'] == 'OUVERT')
        self.assertEqual(ouverts['nombre'], 1)
