from apps.api.tests.support import ApiTestCase


class ErreursApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.banque = self.creer_banque()
        self.titulaire = self.creer_client(self.banque)

    def test_filtres_invalides_renvoient_400(self):
        for url in (
            '/api/v1/transactions/?montant_min=abc',
            '/api/v1/transactions/?date_min=hier',
            '/api/v1/transactions/?compte=abc',
            '/api/v1/comptes/?client=abc',
            '/api/v1/clients/?banque=abc',
            '/api/v1/factures/?transaction=abc',
            '/api/v1/audit/?date_max=31-12-2026',
            '/api/v1/dashboard/?date_min=pas-une-date',
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 400)

    def test_transaction_compte_non_numerique(self):
        response = self.client.post('/api/v1/transactions/', {
            'type_transaction': 'DEPOT', 'compte': 'abc', 'montant': '10',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('compte', response.data)

    def test_suppression_protegee_renvoie_409(self):
        response = self.client.delete(f'/api/v1/banques/{self.banque.id}/')
        self.assertEqual(response.status_code, 409)
        self.assertIn('désactivez-la', response.data['detail'])

    def test_message_agent_sur_action_admin(self):
        self.connecter_agent(self.banque)
        response = self.client.post('/api/v1/banques/', {'nom': 'X', 'pays': 'CI', 'ville': 'A'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'Action réservée à un administrateur.')
