package com.luxisoft.realityos

/** Pure routing for AI chat messages. The server classifies intent; guests stay object-only. */
internal object ChatRoutePolicy {
    enum class ResolvedRoute {
        PEOPLE_SEARCH,
        OBJECT_QUERY,
        CHAT,
        ASK,
    }

    enum class PersonReply {
        FACE_SEARCH,
        TEXT_SEARCH,
        EXPIRED,
    }

    /**
     * A "Persona" quick reply keeps an attached probe: identity can only come
     * from the image, so a pending question never diverts it to text search.
     */
    fun resolvePersonReply(hasProbe: Boolean, hasText: Boolean): PersonReply = when {
        hasProbe -> PersonReply.FACE_SEARCH
        hasText -> PersonReply.TEXT_SEARCH
        else -> PersonReply.EXPIRED
    }

    fun peopleAllowed(isGuest: Boolean): Boolean = !isGuest

    fun resolveRoute(serverTarget: String): ResolvedRoute = when (serverTarget) {
        "person" -> ResolvedRoute.PEOPLE_SEARCH
        "object" -> ResolvedRoute.OBJECT_QUERY
        "chat" -> ResolvedRoute.CHAT
        else -> ResolvedRoute.ASK
    }

    /**
     * Automatic routing: ambiguous text goes to object search instead of
     * asking the user to choose. Person, object and chat targets are kept.
     */
    fun resolveAutoRoute(serverTarget: String): ResolvedRoute =
        when (val route = resolveRoute(serverTarget)) {
            ResolvedRoute.ASK -> ResolvedRoute.OBJECT_QUERY
            else -> route
        }

    /**
     * Image-plus-text fallback when probe classification fails: route by the
     * user's own words. Null when there is nothing to route on.
     */
    fun imageFallbackRoute(question: String, serverTarget: String?): ResolvedRoute? {
        if (question.isBlank() || serverTarget == null) return null
        return resolveAutoRoute(serverTarget)
    }

    fun greeting(language: String): String = when (language.lowercase().take(2)) {
        "es" -> "¡Hola! Soy Muse. Puedo buscar personas y objetos en tus espacios. ¿Qué necesitas encontrar?"
        "pt" -> "Olá! Sou Muse. Posso buscar pessoas e objetos nos seus espaços. O que você precisa encontrar?"
        "fr" -> "Salut ! Je suis Muse. Je peux chercher des personnes et des objets dans vos espaces. Que faut-il trouver ?"
        "de" -> "Hallo! Ich bin Muse. Ich kann Personen und Objekte in deinen Bereichen suchen. Was soll ich finden?"
        "it" -> "Ciao! Sono Muse. Posso cercare persone e oggetti nei tuoi spazi. Cosa devo trovare?"
        else -> "Hi! I'm Muse. I can search people and objects across your spaces. What do you need to find?"
    }

    fun canSend(text: String): Boolean = text.trim().length >= 2

    fun showSendButton(hasText: Boolean, hasAttachment: Boolean, recording: Boolean): Boolean =
        recording || hasText || hasAttachment

    fun formatDuration(durationMs: Int): String {
        val totalSeconds = (durationMs.coerceAtLeast(0) + 500) / 1000
        return "${totalSeconds / 60}:${"%02d".format(totalSeconds % 60)}"
    }
}
