package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.CompositingStrategy
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.zIndex

/** Native controls used over the phone viewfinder in Meta's Debug optical shell. */
@Composable
internal fun PhoneCaptureViewfinder(
    preview: PhonePreviewState,
    recording: Boolean,
    recordingSeconds: Int,
    busy: Boolean,
    photoSearch: Boolean,
    onPhoto: () -> Unit,
    onVideo: () -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier,
    previewContent: @Composable () -> Unit
) {
    Box(
        // AndroidView holders can still hit-test when their pixels are
        // transparent. The native camera must win hit testing as well as drawing.
        modifier = modifier.zIndex(1f).graphicsLayer {
            shape = RoundedCornerShape(18.dp)
            clip = true
            compositingStrategy = CompositingStrategy.Offscreen
        }
    ) {
        previewContent()
        if (preview.phase == PhonePreviewPhase.OPENING) {
            CircularProgressIndicator(modifier = Modifier.align(Alignment.Center).size(28.dp))
        }
        if (preview.phase == PhonePreviewPhase.ERROR) {
            Text(preview.error.orEmpty(), color = Color.White, modifier = Modifier.align(Alignment.Center).padding(12.dp))
        }
        CaptureIconButton(
            image = Icons.Filled.Close,
            contentDescription = stringResource(R.string.display_cancel),
            tint = MaterialTheme.colorScheme.tertiary,
            enabled = true,
            onClick = onClose,
            testTag = "rayban-camera-cancel",
            modifier = Modifier.align(Alignment.TopEnd).padding(8.dp)
        )
        if (recording) {
            Text(
                stringResource(R.string.meta_recording_duration, recordingSeconds),
                color = Color.White,
                modifier = Modifier.align(Alignment.TopCenter).padding(8.dp),
                style = MaterialTheme.typography.labelLarge
            )
        }
        CaptureControlDock(
            recording = recording,
            busy = busy,
            ready = preview.ready,
            photoSearch = photoSearch,
            onTakePhoto = onPhoto,
            onToggleVideo = onVideo,
            modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 10.dp)
        )
    }
}

/** A compact, explicit capture dock; labels remain available to accessibility services. */
@Composable
private fun CaptureControlDock(
    recording: Boolean,
    busy: Boolean,
    ready: Boolean,
    photoSearch: Boolean,
    onTakePhoto: () -> Unit,
    onToggleVideo: () -> Unit,
    modifier: Modifier = Modifier
) {
    // A vertical dock preserves Material's 48 dp touch targets even on the
    // narrow portrait viewfinder. A horizontal pair would overflow its 9:16
    // width on common phone screens.
    Column(
        modifier = modifier.testTag("rayban-camera-controls"),
        verticalArrangement = Arrangement.spacedBy(8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        if (!photoSearch) {
            CaptureIconButton(
                image = if (recording) Icons.Filled.Stop else Icons.Filled.Videocam,
                contentDescription = stringResource(
                    if (recording) R.string.display_stop_video else R.string.display_record_video
                ),
                tint = if (recording) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.tertiary,
                enabled = !busy && (recording || ready),
                onClick = onToggleVideo,
                testTag = if (recording) "rayban-camera-stop-video" else "rayban-camera-record-video"
            )
        }
        if (!recording) {
            CaptureIconButton(
                image = Icons.Filled.PhotoCamera,
                contentDescription = stringResource(R.string.display_take_photo),
                tint = MaterialTheme.colorScheme.tertiary,
                enabled = !busy && ready,
                onClick = onTakePhoto,
                testTag = "rayban-camera-photo"
            )
        }
    }
}

@Composable
private fun CaptureIconButton(
    image: androidx.compose.ui.graphics.vector.ImageVector,
    contentDescription: String,
    tint: Color,
    enabled: Boolean,
    onClick: () -> Unit,
    testTag: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        color = Color.Black.copy(alpha = 0.36f),
        contentColor = tint,
        shape = CircleShape
    ) {
        IconButton(
            onClick = onClick,
            enabled = enabled,
            modifier = Modifier
                .size(CaptureControlSize)
                .testTag(testTag)
        ) {
            Icon(imageVector = image, contentDescription = contentDescription)
        }
    }
}

private val CaptureControlSize = 48.dp
