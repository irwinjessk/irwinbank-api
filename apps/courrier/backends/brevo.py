import json
import urllib.error
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

BREVO_URL = 'https://api.brevo.com/v3/smtp/email'


class BrevoEmailBackend(BaseEmailBackend):
    """Envoi via l'API HTTPS de Brevo : les ports SMTP sont bloqués sur Render (plan gratuit)."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')
        self.timeout = getattr(settings, 'EMAIL_TIMEOUT', None) or 10

    def send_messages(self, email_messages):
        if not self.api_key:
            if self.fail_silently:
                return 0
            raise ImproperlyConfigured('BREVO_API_KEY est vide : impossible d’envoyer des e-mails.')
        envoyes = 0
        for message in email_messages:
            try:
                self._envoyer(message)
                envoyes += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return envoyes

    def _envoyer(self, message):
        nom, adresse = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)
        payload = {
            'sender': {'email': adresse, **({'name': nom} if nom else {})},
            'to': [{'email': parseaddr(destinataire)[1]} for destinataire in message.to],
            'subject': message.subject,
        }
        if message.cc:
            payload['cc'] = [{'email': parseaddr(adresse_cc)[1]} for adresse_cc in message.cc]
        if message.bcc:
            payload['bcc'] = [{'email': parseaddr(adresse_bcc)[1]} for adresse_bcc in message.bcc]
        html = next((contenu for contenu, type_mime in getattr(message, 'alternatives', []) if type_mime == 'text/html'), None)
        if message.content_subtype == 'html':
            payload['htmlContent'] = message.body
        else:
            payload['textContent'] = message.body
            if html:
                payload['htmlContent'] = html

        requete = urllib.request.Request(
            BREVO_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'api-key': self.api_key, 'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(requete, timeout=self.timeout) as reponse:
                return json.loads(reponse.read() or b'{}')
        except urllib.error.HTTPError as erreur:
            detail = erreur.read().decode('utf-8', errors='replace')
            raise RuntimeError(f'Brevo a refusé l’envoi ({erreur.code}) : {detail}') from erreur
