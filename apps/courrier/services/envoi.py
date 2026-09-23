def envoyer(destinataire, sujet, corps):
    """Point unique d'envoi. Le transport e-mail sera branché ici."""
    return {
        'statut': 'EN_ATTENTE',
        'destinataire': destinataire,
        'sujet': sujet,
        'corps': corps,
    }
