package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import java.util.UUID
import kotlinx.coroutines.*
import org.json.JSONObject

internal class PublicationUploader(
    private val scope: CoroutineScope,
    private val onPublished: () -> Unit,
    private val onBusy: (Boolean) -> Unit,
    private val saveId: (String?) -> Unit
) {
    var id by mutableStateOf<String?>(null)
    var result by mutableStateOf<JSONObject?>(null)
    var error by mutableStateOf("")
    var retryAction by mutableStateOf("retry")
    var submitting by mutableStateOf(false)
    private fun update(value: JSONObject) {
        result = value
        if (value.optString("status") == "cancelled") {
            id = null
            saveId(null)
            onBusy(false)
            error = value.optText("error").orEmpty()
        }
        if (value.optString("status") == "published") {
            id = null
            saveId(null)
            onBusy(false)
            onPublished()
        }
    }
    fun submit(photo: PendingPublishPhoto, note: String, source: String, audience: String, workspaceId: String? = null) {
        scope.launch {
            onBusy(true)
            submitting = true
            error = ""
            try {
                val fields = mutableMapOf("request_key" to UUID.randomUUID().toString(), "audience" to audience, "note_text" to note, "note_source" to source)
                workspaceId?.let { fields["workspace_id"] = it }
                val value = withContext(Dispatchers.IO) {
                    JSONObject(SocialSession.requestMultipart("me/publication-uploads", fields, photo.bytes, photo.name, photo.mimeType))
                }
                id = value.getString("id")
                saveId(id)
                update(value)
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                error = e.message.orEmpty()
                if (error.contains("review_busy")) {
                    retryAction = "confirm"
                    error = localizedText(R.string.ui_another_image_is_being_processed_try_confirming_again_shortly)
                } else {
                    retryAction = "retry"
                }
                onBusy(false)
            } finally {
                submitting = false
            }
        }
    }
    suspend fun poll() {
        while (id != null) {
            try {
                val value = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("me/publication-uploads/$id")) }
                error = ""
                update(value)
                if (value.optString("status") != "pending") break
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                error = e.message.orEmpty()
                if (error.contains("review_busy")) {
                    retryAction = "confirm"
                    error = localizedText(R.string.ui_another_image_is_being_processed_try_confirming_again_shortly)
                } else {
                    retryAction = "retry"
                }
                break
            }
            delay(1000)
        }
    }
    fun resumePolling() {
        scope.launch { poll() }
    }
    fun action(action: String) {
        val key = id ?: return
        scope.launch {
            submitting = true
            error = ""
            try {
                val value = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("me/publication-uploads/$key/$action", JSONObject())) }
                update(value)
                if (action == "cancel") {
                    id = null
                    saveId(null)
                    onBusy(false)
                }
                if (action == "retry") {
                    submitting = false
                    poll()
                }
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                error = e.message.orEmpty()
                if (error.contains("review_busy")) {
                    retryAction = "confirm"
                    error = localizedText(R.string.ui_another_image_is_being_processed_try_confirming_again_shortly)
                } else {
                    retryAction = "retry"
                }
            } finally {
                submitting = false
            }
        }
    }
    fun dismissError() {
        if (id == null) {
            error = ""
            onBusy(false)
        }
    }
}

@Composable
internal fun rememberPublicationUploader(onPublished: () -> Unit, onBusy: (Boolean) -> Unit): PublicationUploader {
    val scope = rememberCoroutineScope()
    val latestPublished by rememberUpdatedState(onPublished)
    val latestBusy by rememberUpdatedState(onBusy)
    var savedId by rememberSaveable { mutableStateOf<String?>(null) }
    val state = remember { PublicationUploader(scope, { latestPublished() }, { latestBusy(it) }, { savedId = it }).apply { id = savedId } }
    LaunchedEffect(state.id) { if (state.id != null) state.poll() }
    return state
}

@Composable
internal fun PublicationUploadDialog(state: PublicationUploader) {
    if (state.id == null && !state.submitting && state.error.isBlank()) return
    val value = state.result
    val duplicate = value?.optString("status") == "duplicate"
    val failed = value?.optString("status") == "failed" || state.error.isNotBlank()
    val context = LocalContext.current
    AlertDialog(
        onDismissRequest = {
            if (!state.submitting) {
                if (state.id != null) state.action("cancel") else state.dismissError()
            }
        },
        title = {
            Text(
                if (duplicate) {
                    localizedText(R.string.ui_this_image_already_exists)
                } else if (failed) {
                    localizedText(R.string.ui_analysis_failed)
                } else {
                    localizedText(R.string.ui_analyzing_image)
                }
            )
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                when {
                    failed -> NoticeEffect(state.error.ifBlank { value?.optString("error").orEmpty() }, {})
                    duplicate -> {
                        Text(localizedText(R.string.ui_a_publication_with_this_photo_already_exists_in_the_same_profile_or_group_would_you_l))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            listOf("duplicate_preview_url" to localizedText(R.string.ui_existing), "preview_url" to localizedText(R.string.ui_new)).forEach { (field, label) ->
                                Column(Modifier.weight(1f)) {
                                    Text(label)
                                    DatabaseImage(profileImageRequest(context, authorizedMediaUrl(value!!.getString(field))), label, Modifier.fillMaxWidth().aspectRatio(1f), contentScale = ContentScale.Fit)
                                }
                            }
                        }
                        Text(localizedText(R.string.ui_comments_reactions_and_permissions_will_be_preserved), style = MaterialTheme.typography.bodySmall)
                    }
                    else -> {
                        LinearProgressIndicator(Modifier.fillMaxWidth())
                        Text(localizedText(R.string.ui_meta_checks_for_duplicates_and_locates_objects_the_publication_will_appear_when_finis))
                    }
                }
            }
        },
        confirmButton = {
            if (duplicate) {
                TextButton(onClick = { state.action("confirm") }, enabled = !state.submitting) { Text(localizedText(R.string.ui_confirm_replacement)) }
            } else if (failed && state.id != null) {
                TextButton(onClick = { if (value?.optString("status") in setOf("failed", "duplicate")) state.action(state.retryAction) else state.resumePolling() }, enabled = !state.submitting) { Text(localizedText(R.string.ui_retry)) }
            }
        },
        dismissButton = {
            TextButton(onClick = { if (state.id != null) state.action("cancel") else state.dismissError() }, enabled = !state.submitting) { Text(if (failed && state.id == null) localizedText(R.string.ui_close) else localizedText(R.string.ui_cancel)) }
        }
    )
}
