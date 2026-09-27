from apps.api.tests.support import ApiTestCase


class ComptesApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.titulaire = self.creer_client(self.creer_banque())

    def test_ouverture_compte(self):
        response = self.client.post('/api/v1/comptes/', {'client': self.titulaire.id, 'type_compte': 'EPARGNE'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['statut'], 'OUVERT')
        self.assertEqual(response.data['solde'], '0.00')

    def test_cloture_refusee_si_solde_non_nul(self):
        compte = self.creer_compte(self.titulaire, solde='50.00')
        response = self.client.post(f'/api/v1/comptes/{compte.id}/cloturer/')
        self.assertEqual(response.status_code, 400)

    def test_cloture_si_solde_nul(self):
        compte = self.creer_compte(self.titulaire)
        response = self.client.post(f'/api/v1/comptes/{compte.id}/cloturer/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statut'], 'CLOTURE')

    def test_liste_par_client(self):
        self.creer_compte(self.titulaire)
        autre = self.creer_client(self.creer_banque(nom='Autre'), email='b@example.com')
        self.creer_compte(autre)
        response = self.client.get(f'/api/v1/comptes/?client={self.titulaire.id}')
        self.assertEqual(len(response.data), 1)
