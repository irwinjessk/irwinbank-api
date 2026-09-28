from apps.audit.services.journal import tracer
from apps.courrier.services.envoi import envoyer


def envoyer_bienvenue_banque(banque, acteur=None):
    corps = (
        f'Bonjour,\n\n'
        f'{banque.nom} ({banque.ville}, {banque.pays}) est désormais enregistrée sur la plateforme ADA BANK.\n'
        f'Son agence principale a été créée automatiquement ; vos agents peuvent maintenant être rattachés '
        f'et inscrire vos premiers clients.\n\n'
        f'Bienvenue dans le réseau,\n'
        f'ADA BANK'
    )
    statut = envoyer(banque.email, f'Bienvenue sur ADA BANK · {banque.nom}', corps)
    _tracer(acteur, 'banque', banque.id, banque, banque.email, statut)
    return statut


def envoyer_bienvenue_client(client, acteur=None):
    corps = (
        f'Bonjour {client.prenom} {client.nom},\n\n'
        f'Bienvenue chez {client.banque.nom} !\n\n'
        f'Votre numéro client : {client.numero_client}\n'
        f'Votre agence : {client.agence.nom}\n'
        + (f'Votre conseiller : {client.conseiller.username}\n' if client.conseiller_id else '')
        + f'\nConservez ce numéro : il vous sera demandé à chaque opération au guichet.\n\n'
        f'ADA BANK'
    )
    statut = envoyer(client.email, f'Bienvenue chez {client.banque.nom}', corps)
    _tracer(acteur, 'client', client.id, client.banque, client.email, statut)
    return statut


def _tracer(acteur, entite, entite_id, banque, email, statut):
    resultat = 'envoyé' if statut == 'ENVOYEE' else 'échec d’envoi'
    tracer(
        acteur=acteur,
        action=f'{entite}.bienvenue',
        entite=entite,
        entite_id=entite_id,
        resume=f'E-mail de bienvenue à {email} : {resultat}'[:255],
        banque=banque,
    )
