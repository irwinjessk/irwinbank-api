from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Envoie un e-mail de test avec la configuration courante (EMAIL_BACKEND).'

    def add_arguments(self, parser):
        parser.add_argument('destinataire')

    def handle(self, destinataire, **options):
        self.stdout.write(f'Moteur : {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Expéditeur : {settings.DEFAULT_FROM_EMAIL}')
        try:
            send_mail(
                'ADA BANK · test d’envoi',
                'Si vous lisez ce message, l’envoi d’e-mails de la plateforme fonctionne.',
                None,
                [destinataire],
                fail_silently=False,
            )
        except Exception as erreur:
            raise CommandError(f'Échec : {erreur}') from erreur
        self.stdout.write(self.style.SUCCESS(f'E-mail envoyé à {destinataire}.'))
