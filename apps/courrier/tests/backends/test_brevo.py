import io
import json
import urllib.error
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.test import SimpleTestCase, override_settings

from apps.courrier.services.envoi import envoyer

BREVO = 'apps.courrier.backends.brevo.BrevoEmailBackend'


class ReponseBrevo(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@override_settings(EMAIL_BACKEND=BREVO, BREVO_API_KEY='cle-test', DEFAULT_FROM_EMAIL='ADA BANK <contact@ada.test>')
class BrevoBackendTests(SimpleTestCase):
    @mock.patch('apps.courrier.backends.brevo.urllib.request.urlopen')
    def test_envoi_via_l_api_https(self, urlopen):
        urlopen.return_value = ReponseBrevo(b'{"messageId": "<1@brevo>"}')
        envoyes = send_mail('Sujet', 'Corps du message', None, ['Awa <awa@example.com>'])
        self.assertEqual(envoyes, 1)
        requete = urlopen.call_args.args[0]
        self.assertEqual(requete.full_url, 'https://api.brevo.com/v3/smtp/email')
        self.assertEqual(requete.get_header('Api-key'), 'cle-test')
        payload = json.loads(requete.data)
        self.assertEqual(payload['sender'], {'email': 'contact@ada.test', 'name': 'ADA BANK'})
        self.assertEqual(payload['to'], [{'email': 'awa@example.com'}])
        self.assertEqual((payload['subject'], payload['textContent']), ('Sujet', 'Corps du message'))

    @mock.patch('apps.courrier.backends.brevo.urllib.request.urlopen')
    def test_refus_de_brevo_devient_un_echec_trace(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            'https://api.brevo.com/v3/smtp/email', 401, 'Unauthorized', {}, io.BytesIO(b'{"message":"Key not found"}')
        )
        with self.assertRaisesMessage(RuntimeError, 'Key not found'):
            send_mail('Sujet', 'Corps', None, ['awa@example.com'])
        self.assertEqual(envoyer('awa@example.com', 'Sujet', 'Corps'), 'ECHEC')

    @override_settings(BREVO_API_KEY='')
    def test_cle_absente(self):
        with self.assertRaises(ImproperlyConfigured):
            send_mail('Sujet', 'Corps', None, ['awa@example.com'])
        self.assertEqual(envoyer('awa@example.com', 'Sujet', 'Corps'), 'ECHEC')
