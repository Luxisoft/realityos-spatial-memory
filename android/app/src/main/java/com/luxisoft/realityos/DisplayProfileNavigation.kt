package com.luxisoft.realityos

import androidx.lifecycle.viewModelScope
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

internal data class DisplayProfileTarget(val userId: String, val name: String, val confidence: Double?)
internal data class DisplayProfileRequest(val owner: String, val targets: List<DisplayProfileTarget>)

internal fun normalizedProfileId(value: String?): String? = value?.let {
    runCatching { UUID.fromString(it).toString() }.getOrNull()?.takeIf { canonical -> canonical.equals(it, ignoreCase = true) }
}

internal fun displayProfileTargets(matches: List<GalleryThumb>): List<DisplayProfileTarget> = matches.mapNotNull { match ->
    normalizedProfileId(match.profileUserId)?.let { DisplayProfileTarget(it, match.caption, match.confidence) }
}.distinctBy { it.userId }

internal fun RealityViewModel.openMatchedProfiles(profileId: String? = null, revision: Long = metaController.generation.revision) {
    viewModelScope.launch(Dispatchers.Main.immediate) {
        val owner = metaController.profileOwner()
        if (owner == null || SocialSession.isGuest || !metaController.generation.accepts(revision)) return@launch
        val targets = displayProfileTargets(metaController.matches).filter { profileId == null || it.userId == profileId }
        if (targets.isEmpty()) {
            showStatus(copy(R.string.meta_match_profile_missing))
            return@launch
        }
        stopSpeak()
        displayProfileRequest.value = DisplayProfileRequest(owner, targets)
    }
}

internal fun RealityViewModel.closeMatchedProfiles() {
    displayProfileRequest.value = null
}

internal fun RealityViewModel.canShowMatchedProfile(request: DisplayProfileRequest): Boolean = !SocialSession.isGuest && metaController.profileOwner() == request.owner
