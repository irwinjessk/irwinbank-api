from apps.api.tests.support import ApiTestCase


class BanquesApiTests(ApiTestCase):
    def test_creation_banque(self):
        response = self.client.post('/api/v1/banques/', {'nom': 'ADA', 'pays': 'Sénégal', 'ville': 'Dakar'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nombre_clients'], 0)

    def test_filtre_par_ville(self):
        self.creer_banque(ville='Abidjan')
        self.creer_banque(nom='Autre', ville='Bouaké')
        response = self.client.get('/api/v1/banques/?ville=Bouak')
        self.assertEqual([b['nom'] for b in response.data], ['Autre'])

    def test_top_trie_par_nombre_de_clients(self):
        petite = self.creer_banque(nom='Petite')
        grande = self.creer_banque(nom='Grande')
        self.creer_client(petite, email='a@example.com')
        self.creer_client(grande, email='b@example.com')
        self.creer_client(grande, email='c@example.com')
        response = self.client.get('/api/v1/banques/top/')
        self.assertEqual(response.data[0]['nom'], 'Grande')
        self.assertEqual(response.data[0]['nombre_clients'], 2)

    def test_acces_refuse_sans_authentification(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/v1/banques/').status_code, 401)
