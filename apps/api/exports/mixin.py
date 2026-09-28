import json
from datetime import date

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response

from apps.api.exports.fichiers import Document, generer_pdf, generer_xlsx
from apps.api.perimetre import banque_agent
from apps.audit.services.journal import tracer

EXPORT_MAX_LIGNES = 5000


class _FichierRenderer(BaseRenderer):
    charset = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, (bytes, bytearray)):
            return data
        return json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')


class PdfRenderer(_FichierRenderer):
    media_type = 'application/pdf'
    format = 'pdf'


class XlsxRenderer(_FichierRenderer):
    media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    format = 'xlsx'


def jour_fr(valeur):
    return date.fromisoformat(valeur).strftime('%d/%m/%Y')


def libelle_de(modele, champ='nom'):
    def resoudre(valeur):
        objet = modele.objects.filter(pk=valeur).first()
        return getattr(objet, champ) if objet else f'#{valeur}'
    return resoudre


def choix(libelles):
    return lambda valeur: libelles.get(valeur, valeur)


class ExportMixin:
    """Ajoute `GET …/export?format=pdf|xlsx`, filtré exactement comme la liste."""

    export_nom = 'export'
    export_titre = 'Export'
    export_filtres = {}

    def export_colonnes(self):
        raise NotImplementedError

    def export_resume(self, objets):
        return []

    @action(detail=False, methods=['get'], url_path='export', renderer_classes=[PdfRenderer, XlsxRenderer])
    def export(self, request, *args, **kwargs):
        format_fichier = request.accepted_renderer.format
        objets = list(self.get_queryset()[:EXPORT_MAX_LIGNES + 1])
        tronque = len(objets) > EXPORT_MAX_LIGNES
        objets = objets[:EXPORT_MAX_LIGNES]

        maintenant = timezone.localtime()
        document = Document(
            titre=self.export_titre,
            colonnes=self.export_colonnes(),
            lignes=objets,
            meta=self._meta(request, maintenant, len(objets), tronque),
            resume=self.export_resume(objets),
        )
        contenu = generer_pdf(document) if format_fichier == 'pdf' else generer_xlsx(document)

        agent_banque = banque_agent(request.user)
        tracer(
            acteur=request.user,
            action='export.genere',
            entite=self.export_nom,
            entite_id=0,
            resume=f'Export {format_fichier.upper()} « {self.export_titre} » : {len(objets)} ligne(s)'[:255],
            banque=request.user.profil.banque if agent_banque else None,
        )
        nom_fichier = f'{self.export_nom}-{maintenant:%Y-%m-%d-%H%M}.{format_fichier}'
        return Response(contenu, headers={'Content-Disposition': f'attachment; filename="{nom_fichier}"'})

    def _meta(self, request, maintenant, nombre, tronque):
        lignes = [f'Exporté le {maintenant:%d/%m/%Y à %H:%M} par {request.user.username}']
        if banque_agent(request.user):
            profil = request.user.profil
            lignes.append(f'Périmètre : {profil.banque.nom} · agence {profil.agence.nom if profil.agence_id else "—"}')
        filtres = []
        for cle, (libelle, resoudre) in self.export_filtres.items():
            valeur = request.query_params.get(cle)
            if not valeur:
                continue
            try:
                affichage = resoudre(valeur) if resoudre else valeur
            except (ValueError, TypeError):
                affichage = valeur
            filtres.append(f'{libelle} = {affichage}')
        lignes.append('Filtres : ' + ('; '.join(filtres) if filtres else 'aucun (liste complète)'))
        total = f'{nombre} ligne(s)'
        if tronque:
            total += f' — limité aux {EXPORT_MAX_LIGNES} premières lignes, affinez les filtres'
        lignes.append(total)
        return lignes
