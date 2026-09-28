from apps.api.tests.support import ApiTestCase
from apps.audit.models import JournalAudit
from apps.banques.models import Agence, Banque
from apps.clients.models import Client


class CrudBanquesTests(ApiTestCase):
    def test_admin_modifie_et_desactive_une_banque(self):
        banque = self.creer_banque()
        response = self.client.patch(f'/api/v1/banques/{banque.id}/', {'ville': 'Yamoussoukro', 'actif': False}, format='json')
        self.assertEqual((response.status_code, response.data['ville'], response.data['actif']), (200, 'Yamoussoukro', False))

    def test_supprimer_une_banque_vide_emporte_son_agence_principale(self):
        banque = self.creer_banque()
        self.assertEqual(self.client.delete(f'/api/v1/banques/{banque.id}/').status_code, 204)
        self.assertFalse(Agence.objects.filter(banque_id=banque.id).exists())

    def test_banque_avec_clients_non_supprimable(self):
        banque = self.creer_banque()
        self.creer_client(banque)
        response = self.client.delete(f'/api/v1/banques/{banque.id}/')
        self.assertEqual(response.status_code, 409)
        self.assertTrue(Banque.objects.filter(pk=banque.id).exists())

    def test_pas_d_inscription_dans_une_banque_desactivee(self):
        banque = self.creer_banque()
        banque.actif = False
        banque.save()
        response = self.client.post('/api/v1/clients/', {'nom': 'K', 'prenom': 'A', 'email': 'a@example.com', 'banque': banque.id}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_agent_ne_modifie_pas_sa_banque(self):
        banque = self.creer_banque()
        self.connecter_agent(banque)
        self.assertEqual(self.client.patch(f'/api/v1/banques/{banque.id}/', {'ville': 'X'}, format='json').status_code, 403)


class CrudAgencesTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.banque = self.creer_banque()
        self.principale = self.agence_principale(self.banque)
        self.cocody = self.creer_agence(self.banque)

    def test_agence_principale_protegee(self):
        renommage = self.client.patch(f'/api/v1/agences/{self.principale.id}/', {'nom': 'Siège'}, format='json')
        desactivation = self.client.patch(f'/api/v1/agences/{self.principale.id}/', {'actif': False}, format='json')
        suppression = self.client.delete(f'/api/v1/agences/{self.principale.id}/')
        self.assertEqual((renommage.status_code, desactivation.status_code, suppression.status_code), (400, 400, 409))
        ville = self.client.patch(f'/api/v1/agences/{self.principale.id}/', {'ville': 'Bouaké'}, format='json')
        self.assertEqual(ville.status_code, 200)

    def test_modifier_desactiver_supprimer_une_agence(self):
        response = self.client.patch(f'/api/v1/agences/{self.cocody.id}/', {'nom': 'Cocody Riviera', 'actif': False}, format='json')
        self.assertEqual((response.data['nom'], response.data['actif']), ('Cocody Riviera', False))
        inscription = self.client.post(
            '/api/v1/clients/',
            {'nom': 'K', 'prenom': 'A', 'email': 'a@example.com', 'banque': self.banque.id, 'agence': self.cocody.id},
            format='json',
        )
        self.assertEqual(inscription.status_code, 400)
        self.assertEqual(self.client.delete(f'/api/v1/agences/{self.cocody.id}/').status_code, 204)

    def test_agence_avec_clients_non_supprimable(self):
        self.creer_client(self.banque, agence=self.cocody)
        self.assertEqual(self.client.delete(f'/api/v1/agences/{self.cocody.id}/').status_code, 409)


class CrudClientsTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.banque = self.creer_banque()

    def test_supprimer_un_client_sans_compte_est_trace(self):
        client = self.creer_client(self.banque)
        self.assertEqual(self.client.delete(f'/api/v1/clients/{client.id}/').status_code, 204)
        self.assertFalse(Client.objects.filter(pk=client.id).exists())
        self.assertTrue(JournalAudit.objects.filter(action='client.supprime', entite_id=client.id).exists())

    def test_client_avec_compte_non_supprimable(self):
        client = self.creer_client(self.banque)
        self.creer_compte(client)
        self.assertEqual(self.client.delete(f'/api/v1/clients/{client.id}/').status_code, 409)

    def test_agent_ne_supprime_pas_un_client_d_une_autre_agence(self):
        client = self.creer_client(self.banque)
        self.connecter_agent(self.banque, self.creer_agence(self.banque))
        self.assertEqual(self.client.delete(f'/api/v1/clients/{client.id}/').status_code, 403)

    def test_recherche_par_email_et_numero(self):
        client = self.creer_client(self.banque, email='unique@example.com')
        self.creer_client(self.banque, email='autre@example.com', nom='Diallo')
        par_email = self.client.get('/api/v1/clients/?email=unique')
        par_numero = self.client.get(f'/api/v1/clients/?numero_client={client.numero_client}')
        self.assertEqual([c['id'] for c in par_email.data], [client.id])
        self.assertEqual([c['id'] for c in par_numero.data], [client.id])
