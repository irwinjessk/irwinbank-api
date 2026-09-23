def tracer(acteur, action, entite, entite_id, resume, banque=None):
    from apps.audit.models import JournalAudit

    return JournalAudit.objects.create(
        acteur=acteur,
        action=action,
        entite=entite,
        entite_id=entite_id,
        banque=banque,
        resume=resume,
    )
