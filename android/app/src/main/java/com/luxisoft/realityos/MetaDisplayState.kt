package com.luxisoft.realityos

/** Phone configuration and the visible state shared by physical and Debug Display. */
data class MetaDestination(val id: String, val name: String)
enum class MetaSearchScope(val wire: String) { GALLERY("gallery"), REGISTRY("registry") }

/** Photo search sense: both kinds open the same camera, only the backend differs. */
enum class MetaPhotoSearchKind { OBJECT, PERSON }

/** Voice search outcome after the server classifies the request. */
enum class MetaVoiceSearch { PERSON_TEXT, OBJECT_QUERY, CHAT, PERSON_BLOCKED }
data class MetaDisplayState(
    val destination: MetaDestination? = null,
    val destinations: List<MetaDestination> = emptyList(),
    val searchScope: MetaSearchScope = MetaSearchScope.GALLERY,
    val photoSearchKind: MetaPhotoSearchKind = MetaPhotoSearchKind.OBJECT,
    val loading: Boolean = false,
    val error: String? = null,
    val captureForPublication: Boolean = false,
    val captureForSearch: Boolean = false,
    val pendingMime: String? = null,
    val uploadStatus: String? = null,
    val publicationRevision: Long = 0,
    val pendingDestination: String? = null,
    val duplicatePreview: String? = null,
    val recordingSeconds: Int = 0,
    val resultIndex: Int = 0,
    val resultCount: Int = 0
)

internal object MetaDisplayPolicy {
    /** Every capture needs an explicitly selected group, or the sole available group. */
    fun publicationDestination(choices: List<MetaDestination>, activeId: String?): MetaDestination? {
        val groups = choices.filter { it.id != "home" && it.id.isNotBlank() }
        return groups.find { it.id == activeId } ?: groups.singleOrNull()
    }

    fun canChangeDestination(capturing: Boolean, pending: Boolean, busy: Boolean): Boolean = !capturing && !pending && !busy

    /** Object photos query gallery evidence; person photos run the 1:N face arm. */
    fun photoSearchPath(kind: MetaPhotoSearchKind): String = when (kind) {
        MetaPhotoSearchKind.OBJECT -> "queries/image"
        MetaPhotoSearchKind.PERSON -> "faces/search"
    }

    fun photoSearchCaptureTitle(kind: MetaPhotoSearchKind): Int = when (kind) {
        MetaPhotoSearchKind.OBJECT -> R.string.meta_search_photo_object
        MetaPhotoSearchKind.PERSON -> R.string.meta_search_photo_person
    }

    /** Account matches expose only the public avatar; references stay private. */
    fun faceDisplayKind(): String = "avatar"

    /** Group probe palette: one color per distinct face, cycling past eight. */
    fun faceGroupPalette(): List<String> = listOf(
        "#F0BF24",
        "#22D3EE",
        "#F472B6",
        "#A3E635",
        "#FB923C",
        "#C084FC",
        "#F87171",
        "#60A5FA"
    )

    fun faceMarkColorName(colorIndex: Int): Int {
        val names = listOf(
            R.string.meta_face_color_1,
            R.string.meta_face_color_2,
            R.string.meta_face_color_3,
            R.string.meta_face_color_4,
            R.string.meta_face_color_5,
            R.string.meta_face_color_6,
            R.string.meta_face_color_7,
            R.string.meta_face_color_8
        )
        return names[((colorIndex % names.size) + names.size) % names.size]
    }

    /** Group rows shown before the overflow line. */
    const val FACE_GROUP_MAX_ROWS = 8

    /**
     * Voice follows the server classification: person descriptions go to
     * people search (blocked for guests, as in the app), greetings stay in
     * chat, and objects plus ambiguous text go to object search.
     */
    fun voiceSearchRoute(serverTarget: String, isGuest: Boolean): MetaVoiceSearch {
        val route = ChatRoutePolicy.resolveAutoRoute(serverTarget)
        return when {
            route == ChatRoutePolicy.ResolvedRoute.PEOPLE_SEARCH && isGuest -> MetaVoiceSearch.PERSON_BLOCKED
            route == ChatRoutePolicy.ResolvedRoute.PEOPLE_SEARCH -> MetaVoiceSearch.PERSON_TEXT
            route == ChatRoutePolicy.ResolvedRoute.CHAT -> MetaVoiceSearch.CHAT
            else -> MetaVoiceSearch.OBJECT_QUERY
        }
    }
}

/** Invalidate responses from a disconnected or previous account/session. */
internal class MetaDisplayGeneration {
    var revision: Long = 0
        private set
    fun invalidate() {
        revision++
    }
    fun accepts(expected: Long): Boolean = expected == revision
}
