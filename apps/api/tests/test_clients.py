from apps.api.tests.support import ApiTestCase
from apps.audit.models import JournalAudit


class ClientsApiTests(ApiTestCase):
    def test_inscription_genere_un_numero(self):
        banque = self.creer_banque()
        response = self.client.post('/api/v1/clients/', {
            'nom': 'Kouassi', 'prenom': 'Aya', 'email': 'aya@example.com', 'banque': banque.id,
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['numero_client'].startswith('CLI-'))

    def test_email_unique(self):
        banque = self.creer_banque()
        self.creer_client(banque)
        response = self.client.post('/api/v1/clients/', {
            'nom': 'Autre', 'prenom': 'Aya', 'email': 'aya@example.com', 'banque': banque.id,
        })
        self.assertEqual(response.status_code, 400)

    def test_fiche_contient_le_nom_de_la_banque(self):
        client = self.creer_client(self.creer_banque(nom='ADA Abidjan'))
        response = self.client.get(f'/api/v1/clients/{client.id}/')
        self.assertEqual(response.data['banque_nom'], 'ADA Abidjan')

    def test_inscription_tracee(self):
        banque = self.creer_banque()
        self.client.post('/api/v1/clients/', {'nom': 'Kouassi', 'prenom': 'Aya', 'email': 'aya@example.com', 'banque': banque.id})
        self.assertTrue(JournalAudit.objects.filter(action='client.cree').exists())

    def test_modification_tracee(self):
        client = self.creer_client(self.creer_banque())
        response = self.client.patch(f'/api/v1/clients/{client.id}/', {'email': 'nouvel@example.com'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'nouvel@example.com')
        journal = JournalAudit.objects.get(action='client.modifie')
        self.assertIn('aya@example.com → nouvel@example.com', journal.resume)

    def test_numero_et_banque_figes(self):
        client = self.creer_client(self.creer_banque())
        autre = self.creer_banque(nom='Autre')
        response = self.client.patch(f'/api/v1/clients/{client.id}/', {'banque': autre.id}, format='json')
        self.assertEqual(response.status_code, 400)
        numero = client.numero_client
        self.client.patch(f'/api/v1/clients/{client.id}/', {'numero_client': 'CLI-PIRATE'}, format='json')
        client.refresh_from_db()
        self.assertEqual(client.numero_client, numero)

    def test_agent_ne_modifie_pas_un_client_hors_banque(self):
        client = self.creer_client(self.creer_banque())
        self.connecter_agent(self.creer_banque(nom='Autre'))
        response = self.client.patch(f'/api/v1/clients/{client.id}/', {'nom': 'X'}, format='json')
        self.assertEqual(response.status_code, 404)

    def test_transactions_filtrees_par_client(self):
        banque = self.creer_banque()
        titulaire = self.creer_client(banque)
        autre = self.creer_client(banque, email='b@example.com')
        for client in (titulaire, autre):
            compte = self.creer_compte(client)
            self.client.post('/api/v1/transactions/', {'type_transaction': 'DEPOT', 'compte': compte.id, 'montant': '10'}, format='json')
        response = self.client.get(f'/api/v1/transactions/?client={titulaire.id}')
        self.assertEqual(len(response.data), 1)

    def test_recherche_par_nom_et_banque(self):
        banque = self.creer_banque()
        autre = self.creer_banque(nom='Autre')
        self.creer_client(banque, email='a@example.com', nom='Kouassi')
        self.creer_client(autre, email='b@example.com', nom='Kouassi')
        response = self.client.get(f'/api/v1/clients/?nom=kouas&banque={banque.id}')
        self.assertEqual(len(response.data), 1)
