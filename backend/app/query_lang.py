"""User-language templates for evidence query answers.

The mobile app sends the device language with each query; templates render in
that language with an English fallback. Stored facts (names, zones, dates) are
never translated, only the surrounding sentence.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "en"

_TEMPLATES: dict[str, dict[str, str]] = {
    "gallery_partial": {
        "en": "These results are partial; some files or search steps still require processing.",
        "es": "Estos resultados son parciales; algunos archivos o pasos de la búsqueda aún requieren procesamiento.",
    },
    "gallery_partial_empty": {
        "en": "I found no annotated matches in the analyzed files. Some files still need processing or review.",
        "es": "No encontré coincidencias señalizadas en los archivos analizados. Algunos archivos aún necesitan procesamiento o revisión.",
    },
    "open_screen": {"en": "Open screen", "es": "Abrir pantalla"},
    "select_post": {
        "en": "Select a publication before performing this action.",
        "es": "Selecciona una publicación antes de realizar esta acción.",
    },
    "confirm_post": {
        "en": "Confirm the action on the selected publication.",
        "es": "Confirma la acción sobre la publicación seleccionada.",
    },
    "register_home": {
        "en": "Register evidence first.",
        "es": "Registra evidencia primero.",
    },
    "accessible_matches": {
        "en": "{count} matches in accessible publications.",
        "es": "{count} coincidencias en las publicaciones accesibles.",
    },
    "gallery_indexing": {
        "en": "The photos and videos are still being indexed. No annotated match is ready yet; please try again shortly.",
        "es": "Las fotos y videos aún se están indexando. Todavía no hay una coincidencia señalizada disponible; vuelve a intentarlo en unos momentos.",
    },
    "gallery_unavailable": {
        "en": "I could not complete the image search right now. Please try again shortly.",
        "es": "No pude completar la búsqueda de imágenes en este momento. Vuelve a intentarlo en unos momentos.",
    },
    "gallery_related": {
        "en": "I found {count} annotated results, including objects from the same family or similar objects. Each result shows the detected label and its relation to your search.",
        "es": "Encontré {count} resultados señalizados, incluyendo objetos de la misma familia o similares. Cada resultado indica qué se detectó y su relación con tu búsqueda.",
    },
    "no_evidence": {
        "en": "There is not enough evidence of that object in this workspace.",
        "es": "No hay suficiente evidencia de ese objeto en este espacio.",
        "pt": "Não há evidência suficiente desse objeto neste espaço.",
        "fr": "Pas assez de preuves de cet objet dans cet espace.",
        "de": "Es gibt nicht genügend Belege für dieses Objekt in diesem Arbeitsbereich.",
        "it": "Non ci sono prove sufficienti di questo oggetto in questo spazio.",
    },
    "several_matches": {
        "en": "There are several matches: {names}. Please specify which one you need.",
        "es": "Hay varias coincidencias: {names}. Especifica cuál necesitas.",
        "pt": "Há várias correspondências: {names}. Especifique qual você precisa.",
        "fr": "Plusieurs correspondances : {names}. Précisez laquelle il vous faut.",
        "de": "Es gibt mehrere Treffer: {names}. Bitte gib an, welchen du brauchst.",
        "it": "Ci sono diverse corrispondenze: {names}. Specifica quale ti serve.",
    },
    "no_observation": {
        "en": "There is no verified observation for {name}.",
        "es": "No hay ninguna observación verificada de {name}.",
        "pt": "Não há observação verificada de {name}.",
        "fr": "Aucune observation vérifiée pour {name}.",
        "de": "Es gibt keine verifizierte Beobachtung für {name}.",
        "it": "Non c'è nessuna osservazione verificata per {name}.",
    },
    "last_seen": {
        "en": "{name} was last seen in {location}, {detail}. Observed on {date}.",
        "es": "{name} fue visto por última vez en {location}, {detail}. Observado el {date}.",
        "pt": "{name} foi visto pela última vez em {location}, {detail}. Observado em {date}.",
        "fr": "{name} a été vu pour la dernière fois à {location}, {detail}. Observé le {date}.",
        "de": "{name} wurde zuletzt in {location} gesehen, {detail}. Beobachtet am {date}.",
        "it": "{name} è stato visto l'ultima volta in {location}, {detail}. Osservato il {date}.",
    },
    "unknown_location": {
        "en": "an unspecified location",
        "es": "un lugar sin especificar",
        "pt": "o local não tem detalhes",
        "fr": "le lieu n'a pas de détail",
        "de": "der Ort hat keine Details",
        "it": "il luogo non ha dettagli",
    },
    "unknown_detail": {
        "en": "no additional spatial detail",
        "es": "sin más detalle espacial",
        "pt": "sem mais detalhes espaciais",
        "fr": "sans autre détail spatial",
        "de": "keine weiteren räumlichen Details",
        "it": "senza altri dettagli spaziali",
    },
    "found_in_publications_one": {
        "en": "No verified evidence, but I found 1 matching photo in your publications.",
        "es": "Sin evidencia verificada, pero encontré 1 foto coincidente en tus publicaciones.",
        "pt": "Sem evidência verificada, mas encontrei 1 foto correspondente em suas publicações.",
        "fr": "Pas de preuve vérifiée, mais j'ai trouvé 1 photo correspondante dans vos publications.",
        "de": "Keine verifizierten Belege, aber ich habe 1 passendes Foto in deinen Veröffentlichungen gefunden.",
        "it": "Nessuna prova verificata, ma ho trovato 1 foto corrispondente nelle tue pubblicazioni.",
    },
    "found_in_publications_other": {
        "en": "No verified evidence, but I found {count} matching photos in your publications.",
        "es": "Sin evidencia verificada, pero encontré {count} fotos coincidentes en tus publicaciones.",
        "pt": "Sem evidência verificada, mas encontrei {count} fotos correspondentes em suas publicações.",
        "fr": "Pas de preuve vérifiée, mais j'ai trouvé {count} photos correspondantes dans vos publications.",
        "de": "Keine verifizierten Belege, aber ich habe {count} passende Fotos in deinen Veröffentlichungen gefunden.",
        "it": "Nessuna prova verificata, ma ho trovato {count} foto corrispondenti nelle tue pubblicazioni.",
    },
    "no_visual_info": {
        "en": "There is not enough visual information to identify an object.",
        "es": "No hay suficiente información visual para identificar un objeto.",
        "pt": "Não há informação visual suficiente para identificar um objeto.",
        "fr": "Pas assez d'informations visuelles pour identifier un objet.",
        "de": "Es gibt nicht genügend visuelle Informationen, um ein Objekt zu identifizieren.",
        "it": "Non ci sono informazioni visive sufficienti per identificare un oggetto.",
    },
}


def normalize_language(tag: str | None) -> str:
    """Reduce a BCP-47 tag to a supported language with English fallback."""

    if not tag:
        return DEFAULT_LANGUAGE
    base = tag.strip().lower().replace("_", "-").split("-")[0]
    options = _TEMPLATES["no_evidence"]
    return base if base in options else DEFAULT_LANGUAGE


def qtext(language: str | None, key: str, **values: object) -> str:
    """Render a query template in the requested language (English fallback)."""

    template = _TEMPLATES[key].get(normalize_language(language), _TEMPLATES[key][DEFAULT_LANGUAGE])
    return template.format(**values)
