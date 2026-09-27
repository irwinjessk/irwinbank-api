from apps.api.tests.support import ApiTestCase


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

    def test_recherche_par_nom_et_banque(self):
        banque = self.creer_banque()
        autre = self.creer_banque(nom='Autre')
        self.creer_client(banque, email='a@example.com', nom='Kouassi')
        self.creer_client(autre, email='b@example.com', nom='Kouassi')
        response = self.client.get(f'/api/v1/clients/?nom=kouas&banque={banque.id}')
        self.assertEqual(len(response.data), 1)
