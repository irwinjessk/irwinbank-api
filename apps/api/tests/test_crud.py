from apps.api.tests.support import ApiTestCase
from apps.audit.models import JournalAudit
from apps.banques.models import Banque
from apps.comptes.services.cloture import cloturer


class CrudBanquesTests(ApiTestCase):
    def test_admin_modifie_et_desactive_une_banque(self):
        banque = self.creer_banque()
        response = self.client.patch(f'/api/v1/banques/{banque.id}/', {'ville': 'Yamoussoukro', 'actif': False}, format='json')
        self.assertEqual((response.status_code, response.data['ville'], response.data['actif']), (200, 'Yamoussoukro', False))

    def test_aucune_suppression_definitive(self):
        banque = self.creer_banque()
        client = self.creer_client(banque)
        compte = self.creer_compte(client)
        agence = self.agence_principale(banque)
        for url in (f'/api/v1/banques/{banque.id}/', f'/api/v1/agences/{agence.id}/', f'/api/v1/clients/{client.id}/', f'/api/v1/comptes/{compte.id}/'):
            self.assertEqual(self.client.delete(url).status_code, 405, url)
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
        self.assertEqual((renommage.status_code, desactivation.status_code), (400, 400))
        ville = self.client.patch(f'/api/v1/agences/{self.principale.id}/', {'ville': 'Bouaké'}, format='json')
        self.assertEqual(ville.status_code, 200)

    def test_modifier_et_desactiver_une_agence(self):
        response = self.client.patch(f'/api/v1/agences/{self.cocody.id}/', {'nom': 'Cocody Riviera', 'actif': False}, format='json')
        self.assertEqual((response.data['nom'], response.data['actif']), ('Cocody Riviera', False))
        inscription = self.client.post(
            '/api/v1/clients/',
            {'nom': 'K', 'prenom': 'A', 'email': 'a@example.com', 'banque': self.banque.id, 'agence': self.cocody.id},
            format='json',
        )
        self.assertEqual(inscription.status_code, 400)


class CrudClientsTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.banque = self.creer_banque()

    def archiver(self, client, motif='Départ du client'):
        return self.client.post(f'/api/v1/clients/{client.id}/archiver/', {'motif': motif}, format='json')

    def test_archiver_masque_le_client_et_trace(self):
        client = self.creer_client(self.banque)
        compte = self.creer_compte(client)
        cloturer(compte, motif='DEMANDE_CLIENT')
        response = self.archiver(client)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['archive'])
        self.assertEqual((response.data['motif_archivage'], response.data['archive_par_nom']), ('Départ du client', 'admin'))
        self.assertEqual(self.client.get('/api/v1/clients/').data, [])
        self.assertEqual([c['id'] for c in self.client.get('/api/v1/clients/?statut=archives').data], [client.id])
        self.assertEqual(len(self.client.get('/api/v1/clients/?statut=tous').data), 1)
        self.assertEqual(self.client.get(f'/api/v1/clients/{client.id}/').status_code, 200)
        self.assertTrue(JournalAudit.objects.filter(action='client.archive', entite_id=client.id).exists())

    def test_archivage_refuse_sans_motif_ou_avec_compte_ouvert(self):
        client = self.creer_client(self.banque)
        self.assertEqual(self.archiver(client, motif='  ').status_code, 400)
        self.creer_compte(client)
        self.assertEqual(self.archiver(client).status_code, 409)

    def test_client_archive_en_lecture_seule_puis_restaure(self):
        client = self.creer_client(self.banque)
        self.archiver(client)
        self.assertEqual(self.client.patch(f'/api/v1/clients/{client.id}/', {'nom': 'X'}, format='json').status_code, 409)
        self.assertEqual(self.client.post('/api/v1/comptes/', {'client': client.id, 'type_compte': 'COURANT'}, format='json').status_code, 409)
        self.assertEqual(self.archiver(client).status_code, 409)
        restauration = self.client.post(f'/api/v1/clients/{client.id}/restaurer/')
        self.assertEqual((restauration.status_code, restauration.data['archive']), (200, False))
        self.assertTrue(JournalAudit.objects.filter(action='client.restaure', entite_id=client.id).exists())
        self.assertEqual(self.client.patch(f'/api/v1/clients/{client.id}/', {'nom': 'X'}, format='json').status_code, 200)

    def test_agent_n_archive_pas_un_client_d_une_autre_agence(self):
        client = self.creer_client(self.banque)
        self.connecter_agent(self.banque, self.creer_agence(self.banque))
        self.assertEqual(self.archiver(client).status_code, 403)

    def test_recherche_par_email_et_numero(self):
        client = self.creer_client(self.banque, email='unique@example.com')
        self.creer_client(self.banque, email='autre@example.com', nom='Diallo')
        par_email = self.client.get('/api/v1/clients/?email=unique')
        par_numero = self.client.get(f'/api/v1/clients/?numero_client={client.numero_client}')
        self.assertEqual([c['id'] for c in par_email.data], [client.id])
        self.assertEqual([c['id'] for c in par_numero.data], [client.id])
