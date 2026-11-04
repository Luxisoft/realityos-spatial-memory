package com.luxisoft.realityos.host

import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.luxisoft.realityos.*
import com.luxisoft.realityos.R
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Profile captures and pending evidence remain available even after Display disconnects. */
@Composable
internal fun MetaExperiencePanel(state: RealityUiState, viewModel: RealityViewModel) {
    val meta = state.meta
    val locked = !MetaDisplayPolicy.canChangeDestination(
        state.wearable.cameraActive || meta.captureForPublication || meta.captureForSearch,
        meta.pendingMime != null,
        state.busy
    )
    LaunchedEffect(Unit) { viewModel.refreshMetaConfiguration() }
    Column(verticalArrangement = Arrangement.spacedBy(14.dp), modifier = Modifier.testTag("meta-experience-panel")) {
        Text(stringResource(R.string.meta_quick_actions), style = MaterialTheme.typography.titleLarge)
        Text(stringResource(R.string.meta_search_mode), style = MaterialTheme.typography.labelLarge)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            MetaSearchScope.entries.forEach { scope ->
                FilterChip(
                    selected = meta.searchScope == scope,
                    enabled = !locked && !state.wearable.speechActive,
                    onClick = { viewModel.selectMetaSearch(scope) },
                    label = { Text(stringResource(if (scope == MetaSearchScope.GALLERY) R.string.meta_search_app else R.string.meta_search_registry)) }
                )
            }
        }
        Text(stringResource(R.string.meta_publication_destination), style = MaterialTheme.typography.labelLarge)
        var choosingGroup by remember { mutableStateOf(false) }
        Box {
            OutlinedButton(onClick = { choosingGroup = true }, enabled = !locked && meta.destinations.isNotEmpty()) {
                Text(MetaDisplayPolicy.publicationDestination(meta.destinations, SocialSession.workWorkspaceId)?.name ?: stringResource(R.string.ui_select_workspace))
            }
            DropdownMenu(expanded = choosingGroup, onDismissRequest = { choosingGroup = false }) {
                meta.destinations.forEach { destination ->
                    DropdownMenuItem(text = { Text(destination.name) }, onClick = {
                        SocialSession.workWorkspaceId = destination.id
                        choosingGroup = false
                    })
                }
            }
        }
        if (meta.destinations.isEmpty() && !meta.loading) Text(stringResource(R.string.publish_needs_group))
        if (meta.loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        if (meta.error != null) {
            NoticeEffect(meta.error, {})
            if (meta.pendingMime == null) TextButton(onClick = viewModel::refreshMetaConfiguration) { Text(stringResource(R.string.display_retry)) }
        }
        if (meta.pendingMime != null) {
            MetaPendingCapture(state, viewModel)
        } else {
            Text(stringResource(R.string.meta_capture_explanation), style = MaterialTheme.typography.bodySmall)
            Button(
                onClick = viewModel::beginMetaCapture,
                enabled = state.wearable.displayReady && MetaDisplayPolicy.publicationDestination(meta.destinations, SocialSession.workWorkspaceId) != null && !locked && !state.wearable.speechActive,
                modifier = Modifier.fillMaxWidth()
            ) { Text(stringResource(R.string.meta_capture)) }
        }
        if (state.recording) Text(stringResource(R.string.meta_recording_duration, meta.recordingSeconds), color = MaterialTheme.colorScheme.secondary)
    }
}

@Composable
private fun MetaPendingCapture(state: RealityUiState, viewModel: RealityViewModel) {
    val meta = state.meta
    val controller = viewModel.metaController
    var classificationValid by remember(controller.previewFile) { mutableStateOf(false) }
    val file = controller.previewFile
    val bitmap by produceState<android.graphics.Bitmap?>(null, file?.absolutePath) {
        value = withContext(Dispatchers.IO) {
            runCatching {
                if (meta.pendingMime == "video/mp4") {
                    MediaMetadataRetriever().use { retriever ->
                        retriever.setDataSource(file?.absolutePath)
                        retriever.getScaledFrameAtTime(0, MediaMetadataRetriever.OPTION_CLOSEST_SYNC, 480, 360)
                    }
                } else {
                    BitmapFactory.decodeFile(file?.absolutePath, BitmapFactory.Options().apply { inSampleSize = 4 })
                }
            }.getOrNull()
        }
    }
    Card(modifier = Modifier.fillMaxWidth().testTag("meta-pending-capture")) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(stringResource(if (meta.uploadStatus == "duplicate") R.string.meta_duplicate else R.string.meta_review_capture), style = MaterialTheme.typography.titleMedium)
            Text(meta.pendingDestination.orEmpty())
            bitmap?.let { Image(it.asImageBitmap(), stringResource(R.string.meta_review_capture), Modifier.fillMaxWidth().heightIn(max = 220.dp), contentScale = ContentScale.Fit) }
            meta.duplicatePreview?.let { path ->
                Text(stringResource(R.string.meta_existing_capture), style = MaterialTheme.typography.labelMedium)
                DatabaseImage(profileImageRequest(LocalContext.current, authorizedMediaUrl(path)), stringResource(R.string.meta_existing_capture), Modifier.fillMaxWidth().height(160.dp), contentScale = ContentScale.Fit)
            }
            if (meta.uploadStatus == null) {
                controller.publicationWorkspaceId?.let { group ->
                    ClassificationFields(group, controller.classification, enabled = !state.busy, onValid = { classificationValid = it }, onChange = controller::classify)
                }
            }
            val statusLabel = when (meta.uploadStatus) {
                "pending" -> R.string.meta_processing
                "duplicate" -> R.string.meta_duplicate_body
                "failed" -> R.string.meta_upload_failed
                null -> R.string.meta_confirm_destination
                else -> R.string.meta_resume_upload
            }
            Text(stringResource(statusLabel), style = MaterialTheme.typography.bodySmall)
            if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
            Button(
                enabled = !state.busy && (meta.uploadStatus != null || classificationValid),
                onClick = {
                    when (meta.uploadStatus) {
                        "duplicate" -> viewModel.replaceMetaPublication()
                        null -> viewModel.publishMetaCapture()
                        else -> viewModel.retryMetaPublication()
                    }
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    stringResource(
                        when (meta.uploadStatus) {
                            "duplicate" -> R.string.meta_replace
                            null -> R.string.meta_publish
                            else -> R.string.display_retry
                        }
                    )
                )
            }
            TextButton(onClick = viewModel::discardMetaCapture, enabled = !state.busy) { Text(stringResource(R.string.meta_discard)) }
        }
    }
}
