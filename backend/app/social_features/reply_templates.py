"""Bilingual local assistant replies, also recognized in historical messages."""

LOCAL_REPLY_TEMPLATES = {
    "chat_translation_preparing": {
        "en": "Preparing the translation…",
        "es": "Preparando la traducción…",
    },
    "chat_translation_failed": {
        "en": "Could not prepare the translation.",
        "es": "No se pudo preparar la traducción.",
    },
    "chat_translation_retry": {"en": "Retry", "es": "Reintentar"},
    "chat_no_answer": {"en": "No answer.", "es": "Sin respuesta."},
    "chat_no_evidence": {"en": "There is not enough evidence.", "es": "Sin evidencia suficiente."},
    "chat_query_failed": {
        "en": "Could not complete the search. Please try again.",
        "es": "No pude completar la búsqueda. Inténtalo de nuevo.",
    },
    "chat_route_failed": {
        "en": "Could not understand the request. Please try again.",
        "es": "No pude entender la petición. Inténtalo de nuevo.",
    },
    "chat_choose_target": {
        "en": "Are you looking for a person or an object?",
        "es": "¿Buscas una persona o un objeto?",
    },
    "chat_workspace_missing": {
        "en": "No workspace is available yet.",
        "es": "Aún no hay un espacio disponible.",
    },
    "chat_image_question": {
        "en": "What would you like to find in this image? You can also type it.",
        "es": "¿Qué quieres buscar en esta imagen? También puedes escribirlo.",
    },
    "chat_image_failed": {
        "en": "Could not analyze the image. Please try again.",
        "es": "No pude analizar la imagen. Inténtalo de nuevo.",
    },
    "chat_voice_missing": {
        "en": "No speech was recognized in the audio.",
        "es": "No reconocí voz en el audio.",
    },
    "chat_voice_failed": {
        "en": "Could not transcribe the audio. Please try again.",
        "es": "No pude transcribir la voz. Inténtalo de nuevo.",
    },
    "chat_recording_failed": {
        "en": "Could not record audio.",
        "es": "No fue posible grabar la voz.",
    },
    "chat_microphone_permission": {
        "en": "Microphone permission is required.",
        "es": "Se requiere permiso de micrófono.",
    },
    "chat_image_read_failed": {
        "en": "Could not read the image.",
        "es": "No fue posible leer la imagen.",
    },
    "chat_action_failed": {
        "en": "Could not complete the action.",
        "es": "No pude completar la acción.",
    },
    "chat_camera_permission": {
        "en": "Camera permission is required.",
        "es": "Se requiere permiso de cámara.",
    },
    "chat_question_expired": {
        "en": "That question has expired. Please type it again.",
        "es": "Ya venció esa pregunta. Escríbela de nuevo.",
    },
    "chat_image_expired": {
        "en": "That image is no longer available. Please attach it again.",
        "es": "Ya no tengo esa imagen. Adjúntala de nuevo.",
    },
    "chat_face_none": {
        "en": "I didn't find that person in your spaces.",
        "es": "No encontré a esa persona en tus espacios.",
    },
    "ui_guests_cannot_search_for_meta_people": {
        "en": "Guests cannot search for Meta people.",
        "es": "Los invitados no pueden buscar personas de Meta.",
    },
    "chat_greeting": {
        "en": "Hi! I'm Muse. I can search people and objects across your spaces. What do you need to find?",
        "es": "¡Hola! Soy Muse. Puedo buscar personas y objetos en tus espacios. ¿Qué necesitas encontrar?",
    },
    "chat_face_found": {
        "en": "I found {count} person(s): {names}",
        "es": "Encontré {count} persona(s): {names}",
    },
    "chat_face_found_one": {
        "en": "I found {count} person: {names}",
        "es": "Encontré {count} persona: {names}",
    },
    "chat_face_found_other": {
        "en": "I found {count} people: {names}",
        "es": "Encontré {count} personas: {names}",
    },
}
