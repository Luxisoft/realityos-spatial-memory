package com.luxisoft.realityos

import androidx.compose.runtime.*
import androidx.compose.runtime.snapshots.SnapshotStateList
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties

internal fun authorizedMediaUrl(path: String): String {
    if (path.startsWith("http")) return path
    val base = BuildConfig.DEFAULT_REALITYOS_API_BASE_URL.trimEnd('/')
    val origin = base.removeSuffix("/v1")
    return if (path.startsWith("/v1/")) origin + path else "$base/${path.trimStart('/')}"
}

/** Search panel root: AI chat with automatic person/object routing plus evidence overlays. */
@Composable
internal fun UnifiedSearch(
    messages: SnapshotStateList<ChatMessage>,
    viewModel: RealityViewModel? = null
) {
    var evidenceSelection by remember { mutableStateOf<Pair<List<GalleryThumb>, Int>?>(null) }

    evidenceSelection?.let { (items, index) ->
        Dialog(
            onDismissRequest = { evidenceSelection = null },
            properties = DialogProperties(usePlatformDefaultWidth = false, decorFitsSystemWindows = false)
        ) {
            SearchEvidenceCarousel(items, index, onClose = { evidenceSelection = null })
        }
        return
    }
    AiChat(
        messages = messages,
        viewModel = viewModel,
        onOpenEvidence = { items, index ->
            val chosen = items.getOrNull(index)?.let(::evidenceIdentity)
            val ordered = orderedEvidence(items)
            evidenceSelection = ordered to ordered.indexOfFirst { evidenceIdentity(it) == chosen }.coerceAtLeast(0)
        }
    )
}
