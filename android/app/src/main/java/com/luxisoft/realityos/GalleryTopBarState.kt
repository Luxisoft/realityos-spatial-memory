package com.luxisoft.realityos

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

data class WorkspaceOption(val id: String, val name: String, val role: String)

/**
 * Labels for the work-gallery workspace selector. A blank selection shows
 * every member workspace at once.
 */
object GalleryWorkspaceLabels {
    const val ALL_SPACES = "All workspaces"

    fun selectedName(options: List<WorkspaceOption>, selectedId: String?, fallback: String = ALL_SPACES): String = options.firstOrNull { it.id == selectedId }?.name?.ifBlank { null } ?: fallback
}

/**
 * State shared between the host top bar and the work gallery: the gallery
 * populates workspaces and actions, the top bar renders the selector.
 */
class GalleryTopBarState {
    internal var filters by mutableStateOf(GalleryFilterSelection())
    internal var onFilters: (GalleryFilterSelection) -> Unit = {}
    var loading by mutableStateOf(true)
    var options by mutableStateOf<List<WorkspaceOption>>(emptyList())
    var selectedId by mutableStateOf<String?>(null)
    var publishEnabled by mutableStateOf(true)
    var showInvite by mutableStateOf(false)
    var showAdmin by mutableStateOf(false)
    var onCreate: () -> Unit = {}
    var onRecords: () -> Unit = {}
    var onImport: () -> Unit = {}
    var onSelect: (String?) -> Unit = {}
    var onPublish: () -> Unit = {}
    var onInvite: () -> Unit = {}
    var onAdmin: () -> Unit = {}
}
