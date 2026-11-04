package com.luxisoft.realityos

import android.view.View
import android.widget.TextView
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.view.PreviewView
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearOutSlowInEasing
import androidx.compose.animation.core.MutableTransitionState
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.keyframes
import androidx.compose.animation.core.rememberTransition
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.CompositingStrategy
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.imageResource
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Observer
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.meta.wearable.dat.core.types.Permission
import kotlin.math.roundToInt
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * Debug-only immersive stage. The official Mock Device Kit renderer owns the
 * body; simulator state and testing controls live in the end drawer.
 */
@Composable
fun DeveloperPreviewStage(
    viewModel: RealityViewModel,
    enabled: Boolean,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val application = context.applicationContext as RealityOsApplication
    val controller = remember(application) { application.developerPreviewController }
    val preview by controller.state.collectAsStateWithLifecycle()
    val hostState by viewModel.state.collectAsStateWithLifecycle()
    var autoStartAttempted by rememberSaveable { mutableStateOf(false) }
    val phoneCaptureActive =
        hostState.wearable.inputRoute == InputRoute.PHONE && hostState.wearable.cameraActive

    DisposableEffect(viewModel) {
        onDispose { viewModel.onPhonePreviewHidden() }
    }

    // The Debug host starts Meta's in-app Display simulation once. A failure is
    // deliberately not retried in a loop; the right drawer provides retry and
    // mode selection. No camera, microphone, recording, or upload is started.
    LaunchedEffect(
        enabled,
        preview.active,
        hostState.wearable.transportReady
    ) {
        // Localhost changes the API/account realm, not the Debug Display hardware.
        if (enabled && !preview.active && !autoStartAttempted) {
            // DAT cannot create either a real or mock session until the host
            // has completed Bluetooth-gated initialization in MainActivity.
            if (!hostState.wearable.transportReady) {
                return@LaunchedEffect
            }
            // Give a paired physical Display a brief discovery window. The
            // mock remains the automatic fallback for this no-hardware setup.
            delay(450)
            if (viewModel.hasAvailableWearableDisplay()) {
                // If enrollment is still loading, the second effect below
                // will connect the real device as soon as it is available.
                if (hostState.provisioning != null) {
                    autoStartAttempted = true
                    viewModel.connectDisplay()
                }
                return@LaunchedEffect
            }
            val deviceId = controller.start(DeveloperPreviewMode.IN_APP) ?: return@LaunchedEffect
            // Do not make a transient start failure permanent. In particular,
            // profile loading can recompose this stage while the discovery
            // delay is running; setting this only after the mock exists keeps
            // that cancellation from leaving an inert, tappable preview.
            autoStartAttempted = true
            viewModel.connectDisplay(deviceId)
        }
    }

    LaunchedEffect(
        enabled,
        preview.active,
        preview.deviceIdentifier,
        hostState.provisioning,
        hostState.wearable.sessionActive,
        hostState.wearable.transportReady
    ) {
        if (
            enabled &&
            !preview.active &&
            !hostState.wearable.sessionActive &&
            !autoStartAttempted &&
            hostState.wearable.transportReady &&
            hostState.provisioning != null &&
            viewModel.hasAvailableWearableDisplay()
        ) {
            autoStartAttempted = true
            viewModel.connectDisplay()
            return@LaunchedEffect
        }
        // The virtual device may register before the short-lived RealityOS
        // profile finishes loading. Retry the connection once both are ready
        // rather than leaving a navigable-but-inert renderer on screen.
        if (enabled && preview.active && !hostState.wearable.sessionActive && hostState.provisioning != null) {
            preview.deviceIdentifier?.let(viewModel::connectDisplay)
        }
    }

    Box(modifier = modifier.fillMaxSize()) {
        PreviewSurface(
            state = preview,
            controller = controller,
            viewModel = viewModel,
            showPhoneCameraPreview = phoneCaptureActive,
            phoneCaptureRecording = hostState.recording,
            phoneCaptureBusy = hostState.busy,
            modifier = Modifier.fillMaxSize()
        )
    }
}

/** Content rendered inside the shared right-side Preview controls drawer. */
@Composable
fun PreviewControlPanel(
    state: RealityUiState,
    viewModel: RealityViewModel,
    onOpenGlasses: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val application = context.applicationContext as RealityOsApplication
    val controller = remember(application) { application.developerPreviewController }
    val preview by controller.state.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    var selectedMode by rememberSaveable { mutableStateOf(DeveloperPreviewMode.IN_APP) }
    val queryExample = stringResource(R.string.debug_query_example)
    var query by rememberSaveable { mutableStateOf(queryExample) }

    val photoPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        controller.setCapturedPhoto(uri)
    }
    val videoPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        controller.setVideoFeed(uri)
    }
    fun startPreview(mode: DeveloperPreviewMode) {
        if (!state.wearable.transportReady) {
            viewModel.showWearablesNotReady()
            return
        }
        scope.launch {
            val deviceId = controller.start(mode) ?: return@launch
            viewModel.connectDisplay(deviceId)
        }
    }

    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        PreviewStateStrip(preview)
        Text(
            stringResource(preview.messageResource, *preview.messageArguments.map { stringResource(it) }.toTypedArray()),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            style = MaterialTheme.typography.bodySmall
        )

        if (!preview.active) {
            Text(stringResource(R.string.preview_select_target), style = MaterialTheme.typography.labelLarge)
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                PreviewModeButton(
                    label = stringResource(R.string.preview_in_app),
                    selected = selectedMode == DeveloperPreviewMode.IN_APP,
                    onClick = { selectedMode = DeveloperPreviewMode.IN_APP }
                )
                PreviewModeButton(
                    label = stringResource(R.string.preview_chrome),
                    selected = selectedMode == DeveloperPreviewMode.CHROME,
                    onClick = { selectedMode = DeveloperPreviewMode.CHROME }
                )
            }
            Button(
                onClick = { startPreview(selectedMode) },
                enabled = !state.wearable.sessionActive && state.wearable.transportReady,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(stringResource(R.string.preview_restart_virtual))
            }
            if (state.wearable.sessionActive) {
                Text(
                    stringResource(R.string.preview_disconnect_first),
                    color = MaterialTheme.colorScheme.secondary,
                    style = MaterialTheme.typography.bodySmall
                )
            }
        } else {
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            DeviceLifecycleControls(controller, preview)
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            if (state.wearable.inputRoute == InputRoute.PHONE) {
                // The mock owns only the optical Display transport. Showing
                // Mock Device Kit media controls here would imply that their
                // selected feed drives Register/Search, when those actions
                // deliberately use the phone's live camera and microphone.
                Text(
                    stringResource(R.string.preview_phone_input_hint),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodySmall
                )
            } else {
                PermissionControls(controller)
                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                MediaControls(
                    preview = preview,
                    onSelectPhoto = { photoPicker.launch(arrayOf("image/jpeg", "image/png")) },
                    onSelectVideo = { videoPicker.launch(arrayOf("video/*")) }
                )
                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                SpeechControls(
                    query = query,
                    onQueryChange = { query = it },
                    onPartial = { controller.simulateTranscription(query, isFinal = false) },
                    onFinal = { controller.simulateTranscription(query, isFinal = true) }
                )
            }
        }

        preview.chrome?.takeIf { preview.mode == DeveloperPreviewMode.CHROME }?.let { chrome ->
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Text(stringResource(R.string.preview_chrome_title), style = MaterialTheme.typography.labelLarge)
            Text(
                stringResource(R.string.preview_chrome_body),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodySmall
            )
            CodeLine(chrome.adbForwardCommand)
            CodeLine(chrome.url)
        }

        val issue = preview.error
        if (issue != null) {
            Text(issue, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            OutlinedButton(
                onClick = {
                    controller.clearError()
                }
            ) { Text(stringResource(R.string.debug_dismiss)) }
        }

        if (!preview.active && state.provisioning == null) {
            OutlinedButton(onClick = onOpenGlasses, modifier = Modifier.fillMaxWidth()) {
                Text(stringResource(R.string.preview_open_glasses))
            }
        }
    }
}

@Composable
private fun PreviewStateStrip(state: DeveloperPreviewState) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        PreviewBadge(stringResource(R.string.debug_mock), state.active)
        PreviewBadge(stringResource(R.string.debug_power), state.poweredOn)
        PreviewBadge(stringResource(R.string.debug_open), state.unfolded)
        PreviewBadge(stringResource(R.string.debug_worn), state.worn)
        PreviewBadge(state.mode?.name ?: stringResource(R.string.debug_no_target), state.mode != null)
    }
}

@Composable
private fun PreviewBadge(label: String, active: Boolean) {
    AssistChip(
        onClick = {},
        enabled = false,
        label = { Text(label) },
        colors = androidx.compose.material3.AssistChipDefaults.assistChipColors(
            disabledContainerColor = if (active) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
            disabledLabelColor = if (active) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurfaceVariant
        )
    )
}

@Composable
private fun PreviewModeButton(label: String, selected: Boolean, onClick: () -> Unit) {
    if (selected) {
        Button(onClick = onClick) { Text(label) }
    } else {
        OutlinedButton(onClick = onClick) { Text(label) }
    }
}

@Composable
private fun DeviceLifecycleControls(controller: DeveloperPreviewController, state: DeveloperPreviewState) {
    Text(stringResource(R.string.debug_lifecycle), style = MaterialTheme.typography.labelLarge)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        LifecycleButton(stringResource(if (state.poweredOn) R.string.debug_power_off else R.string.debug_power_on)) {
            if (state.poweredOn) controller.powerOff() else controller.powerOn()
        }
        LifecycleButton(stringResource(if (state.unfolded) R.string.debug_fold else R.string.debug_unfold)) {
            if (state.unfolded) controller.fold() else controller.unfold()
        }
        LifecycleButton(stringResource(if (state.worn) R.string.debug_remove else R.string.debug_wear)) {
            if (state.worn) controller.doff() else controller.don()
        }
    }
}

@Composable
private fun LifecycleButton(label: String, onClick: () -> Unit) {
    Button(onClick = onClick) { Text(label) }
}

@Composable
private fun PermissionControls(controller: DeveloperPreviewController) {
    Text(stringResource(R.string.debug_permissions), style = MaterialTheme.typography.labelLarge)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        PermissionButton(stringResource(R.string.debug_camera_allowed)) { controller.setDatPermission(Permission.CAMERA, granted = true) }
        PermissionButton(stringResource(R.string.debug_camera_denied)) { controller.setDatPermission(Permission.CAMERA, granted = false) }
        PermissionButton(stringResource(R.string.debug_mic_allowed)) { controller.setDatPermission(Permission.MICROPHONE, granted = true) }
        PermissionButton(stringResource(R.string.debug_mic_denied)) { controller.setDatPermission(Permission.MICROPHONE, granted = false) }
    }
}

@Composable
private fun PermissionButton(label: String, onClick: () -> Unit) {
    Button(onClick = onClick) { Text(label, style = MaterialTheme.typography.labelSmall) }
}

@Composable
private fun MediaControls(
    preview: DeveloperPreviewState,
    onSelectPhoto: () -> Unit,
    onSelectVideo: () -> Unit
) {
    Text(stringResource(R.string.debug_media_inputs), style = MaterialTheme.typography.labelLarge)
    Text(
        stringResource(R.string.debug_media_hint),
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        style = MaterialTheme.typography.bodySmall
    )
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        LifecycleButton(stringResource(R.string.debug_choose_photo)) { onSelectPhoto() }
        LifecycleButton(stringResource(R.string.debug_choose_video)) { onSelectVideo() }
    }
    preview.capturedPhotoName?.let { SelectedMedia(stringResource(R.string.debug_photo), it) }
    preview.videoFeedName?.let { SelectedMedia(stringResource(R.string.debug_video), it) }
}

@Composable
private fun SelectedMedia(label: String, value: String) {
    Text(
        "$label: $value",
        color = MaterialTheme.colorScheme.tertiary,
        style = MaterialTheme.typography.labelSmall,
        fontFamily = FontFamily.Monospace
    )
}

@Composable
private fun SpeechControls(
    query: String,
    onQueryChange: (String) -> Unit,
    onPartial: () -> Unit,
    onFinal: () -> Unit
) {
    Text(stringResource(R.string.debug_speech), style = MaterialTheme.typography.labelLarge)
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        label = { Text(stringResource(R.string.debug_spoken_query)) },
        modifier = Modifier.fillMaxWidth(),
        singleLine = true
    )
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        LifecycleButton(stringResource(R.string.debug_send_partial)) { onPartial() }
        Button(onClick = onFinal) { Text(stringResource(R.string.debug_send_final)) }
    }
}

@Composable
private fun PreviewSurface(
    state: DeveloperPreviewState,
    controller: DeveloperPreviewController,
    viewModel: RealityViewModel,
    showPhoneCameraPreview: Boolean,
    phoneCaptureRecording: Boolean,
    phoneCaptureBusy: Boolean,
    modifier: Modifier = Modifier
) {
    BoxWithConstraints(
        modifier = modifier
            .background(Color(0xFF070B12))
            .testTag("meta-display-preview"),
        contentAlignment = Alignment.Center
    ) {
        // The supplied office image remains underneath every optical layer.
        // The frame PNG and the Debug renderer are intentionally translucent,
        // so this scene shows through the lens rather than becoming a black
        // void around the physical glasses.
        Image(
            painter = painterResource(R.drawable.realityos_workspace_bokeh),
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = Modifier.matchParentSize()
        )
        Box(
            modifier = Modifier
                .matchParentSize()
                .background(
                    Brush.verticalGradient(
                        colors = listOf(Color(0x24070B12), Color(0x12070B12), Color(0x24070B12))
                    )
                )
        )
        // The stage intentionally uses the full available width. The entrance
        // begins with the complete glasses photo, then its focused final state
        // consumes the screen with only the right-lens rim remaining.
        val density = LocalDensity.current
        val lensStage = with(density) {
            RayBanLensGeometry.stageFor(maxWidth.toPx(), maxHeight.toPx())
        }
        val stageWidth = with(density) { lensStage.width.toDp() }
        val stageHeight = with(density) { lensStage.height.toDp() }
        when (state.mode) {
            DeveloperPreviewMode.IN_APP -> {
                if (state.active) {
                    RayBanLensPreview(
                        state = state,
                        controller = controller,
                        viewModel = viewModel,
                        showPhoneCameraPreview = showPhoneCameraPreview,
                        phoneCaptureRecording = phoneCaptureRecording,
                        phoneCaptureBusy = phoneCaptureBusy,
                        modifier = Modifier.size(stageWidth, stageHeight)
                    )
                } else {
                    Text(
                        stringResource(R.string.preview_waiting_renderer),
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            DeveloperPreviewMode.CHROME -> Text(
                stringResource(R.string.preview_desktop_only),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodyMedium
            )
            null -> Text(
                stringResource(R.string.preview_waiting_renderer),
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

/**
 * Keeps Meta's Debug renderer intact inside the supplied panoramic Ray-Ban
 * lens. This Debug-only optical shell does not alter pairing,
 * permissions, capture, or the Display session.
 */
@Composable
private fun RayBanLensPreview(
    state: DeveloperPreviewState,
    controller: DeveloperPreviewController,
    viewModel: RealityViewModel,
    showPhoneCameraPreview: Boolean,
    phoneCaptureRecording: Boolean,
    phoneCaptureBusy: Boolean,
    modifier: Modifier = Modifier
) {
    val density = LocalDensity.current
    val captureState by viewModel.state.collectAsStateWithLifecycle()
    val phonePreview = captureState.phonePreview
    val resources = LocalContext.current.resources
    val lensFrame = remember(resources) {
        ImageBitmap.imageResource(resources, R.drawable.rayban_display_lens_frame)
    }
    val apertureMask = remember(resources) {
        ImageBitmap.imageResource(resources, R.drawable.rayban_display_lens_aperture)
    }

    // A fresh composable instance runs on every entry to Preview, while a new
    // virtual-device generation also restarts the sequence after a restart.
    // The target is deliberately set only after the stage receives its real
    // constraints. Setting it while `remember` is created skips the false ->
    // true segment on some Compose versions, leaving the frame frozen at its
    // initial transform.
    val entranceState = remember(state.previewGeneration) { MutableTransitionState(false) }
    val entrance = rememberTransition(entranceState, label = "rayban-lens-entrance")
    LaunchedEffect(showPhoneCameraPreview, phonePreview.generation, phonePreview.phase) {
        if (showPhoneCameraPreview && phonePreview.phase == PhonePreviewPhase.OPENING) {
            delay(10_000)
            if (viewModel.state.value.phonePreview.phase == PhonePreviewPhase.OPENING) {
                viewModel.onPhonePreviewFailure(phonePreview.generation, viewModel.copy(R.string.meta_camera_unavailable))
            }
        }
    }
    BoxWithConstraints(modifier = modifier.clipToBounds()) {
        val stage = with(density) {
            RayBanLensGeometry.stageFor(maxWidth.toPx(), maxHeight.toPx())
        }
        LaunchedEffect(state.previewGeneration, stage.width, stage.height) {
            if (stage.width > 0f && stage.height > 0f) entranceState.targetState = true
        }

        val frameAlpha by entrance.animateFloat(
            transitionSpec = {
                keyframes {
                    durationMillis = LENS_ENTRANCE_DURATION_MILLIS
                    0f at 0
                    1f at LENS_FRAME_FADE_IN_MILLIS using LinearOutSlowInEasing
                }
            },
            label = "rayban-lens-frame-alpha"
        ) { entered -> if (entered) 1f else 0f }
        val sourceCropProgress by entrance.animateFloat(
            transitionSpec = {
                keyframes {
                    durationMillis = LENS_ENTRANCE_DURATION_MILLIS
                    0f at 0
                    0f at LENS_FRAME_FADE_IN_MILLIS
                    1f at LENS_ZOOM_END_MILLIS using FastOutSlowInEasing
                    1f at LENS_ENTRANCE_DURATION_MILLIS
                }
            },
            label = "rayban-lens-source-crop"
        ) { entered -> if (entered) 1f else 0f }
        val softwareAlpha by entrance.animateFloat(
            transitionSpec = {
                keyframes {
                    durationMillis = LENS_ENTRANCE_DURATION_MILLIS
                    0f at 0
                    0f at LENS_SOFTWARE_FADE_START_MILLIS
                    1f at LENS_SOFTWARE_FADE_END_MILLIS using LinearOutSlowInEasing
                    1f at LENS_ENTRANCE_DURATION_MILLIS
                }
            },
            label = "rayban-display-software-alpha"
        ) { entered -> if (entered) 1f else 0f }

        val sourceCrop = RayBanLensGeometry.sourceCrop(sourceCropProgress)
        val frameDestination = RayBanLensGeometry.frameDestination(stage, sourceCrop)
        val finalFrameDestination = RayBanLensGeometry.finalFrameDestination(stage)
        val rendererBounds = RayBanLensGeometry.rendererBounds(stage)

        val frameSourceLeft = sourceCrop.left.roundToInt().coerceIn(0, lensFrame.width - 1)
        val frameSourceTop = sourceCrop.top.roundToInt().coerceIn(0, lensFrame.height - 1)
        val frameSourceRight = sourceCrop.right.roundToInt().coerceIn(frameSourceLeft + 1, lensFrame.width)
        val frameSourceBottom = sourceCrop.bottom.roundToInt().coerceIn(frameSourceTop + 1, lensFrame.height)
        val frameSourceOffset = IntOffset(frameSourceLeft, frameSourceTop)
        val frameSourceSize = IntSize(
            width = frameSourceRight - frameSourceLeft,
            height = frameSourceBottom - frameSourceTop
        )
        val frameDestinationOffset = IntOffset(
            x = frameDestination.left.roundToInt(),
            y = frameDestination.top.roundToInt()
        )
        val frameDestinationSize = IntSize(
            width = frameDestination.width.roundToInt().coerceAtLeast(1),
            height = frameDestination.height.roundToInt().coerceAtLeast(1)
        )

        val finalFrameCrop = RayBanLensGeometry.finalFrameCrop
        val apertureSourceOffset = IntOffset(
            x = finalFrameCrop.left.roundToInt(),
            y = finalFrameCrop.top.roundToInt()
        )
        val apertureSourceSize = IntSize(
            width = finalFrameCrop.width.roundToInt(),
            height = finalFrameCrop.height.roundToInt()
        )
        val apertureDestinationOffset = IntOffset(
            x = finalFrameDestination.left.roundToInt(),
            y = finalFrameDestination.top.roundToInt()
        )
        val apertureDestinationSize = IntSize(
            width = finalFrameDestination.width.roundToInt().coerceAtLeast(1),
            height = finalFrameDestination.height.roundToInt().coerceAtLeast(1)
        )
        // CameraX owns a portrait card in the lens, not the entire aperture.
        // Its 9:16 ViewPort remains clear of the rim and matches photo/video.
        val cameraPreviewBounds = RayBanLensGeometry.cameraPreviewBounds(stage)
        val cameraPreviewLeft = with(density) { cameraPreviewBounds.left.toDp() }
        val cameraPreviewTop = with(density) { cameraPreviewBounds.top.toDp() }
        val cameraPreviewWidth = with(density) { cameraPreviewBounds.width.toDp() }
        val cameraPreviewHeight = with(density) { cameraPreviewBounds.height.toDp() }
        val rendererLeft = with(density) { rendererBounds.left.toDp() }
        val rendererTop = with(density) { rendererBounds.top.toDp() }
        val rendererWidth = with(density) { rendererBounds.width.toDp() }
        val rendererHeight = with(density) { rendererBounds.height.toDp() }

        // The stage never moves or resizes. The frame is fitted into a
        // transparent vertical reveal while its source crop zooms; Meta's
        // square view stays static in the enlarged, lens-bound viewport so
        // its own responsive overview scaling can fit the complete UI.
        Box(modifier = Modifier.matchParentSize()) {
            // CameraX uses a TextureView-backed PreviewView. It is clipped by
            // its own portrait card instead of a full-size mask layer, so a
            // not-yet-streaming surface can never black out or escape the lens.
            if (showPhoneCameraPreview) {
                PhoneCaptureViewfinder(
                    preview = phonePreview,
                    recording = phoneCaptureRecording,
                    recordingSeconds = captureState.meta.recordingSeconds,
                    busy = phoneCaptureBusy,
                    photoSearch = captureState.meta.captureForSearch,
                    onPhoto = viewModel::capturePhotoFromPreview,
                    onVideo = viewModel::togglePreviewVideo,
                    onClose = viewModel::cancelPhoneCapture,
                    modifier = Modifier
                        .offset(x = cameraPreviewLeft, y = cameraPreviewTop)
                        .size(width = cameraPreviewWidth, height = cameraPreviewHeight)
                ) {
                    LensCameraPreview(
                        viewModel = viewModel,
                        generation = phonePreview.generation,
                        modifier = Modifier.fillMaxSize()
                    )
                }
            }
            // Keep Meta's renderer attached across camera entries. Its hidden
            // Android view must not intercept the native viewfinder controls.
            run {
                Box(
                    modifier = Modifier
                        .matchParentSize()
                        .graphicsLayer {
                            compositingStrategy = CompositingStrategy.Offscreen
                            alpha = if (showPhoneCameraPreview) 0f else softwareAlpha * LENS_RENDERER_GLASS_OPACITY
                        }
                        .drawWithCache {
                            onDrawWithContent {
                                drawContent()
                                drawImage(
                                    image = apertureMask,
                                    srcOffset = apertureSourceOffset,
                                    srcSize = apertureSourceSize,
                                    dstOffset = apertureDestinationOffset,
                                    dstSize = apertureDestinationSize,
                                    blendMode = BlendMode.DstIn,
                                    filterQuality = FilterQuality.High
                                )
                            }
                        }
                ) {
                    key(state.previewGeneration) {
                        AndroidView(
                            factory = { viewContext ->
                                controller.createInAppPreviewView(viewContext) ?: TextView(viewContext).apply {
                                    text = viewContext.getString(R.string.preview_waiting_renderer)
                                    setTextColor(android.graphics.Color.WHITE)
                                    gravity = android.view.Gravity.CENTER
                                }
                            },
                            update = { it.visibility = if (showPhoneCameraPreview) View.INVISIBLE else View.VISIBLE },
                            modifier = Modifier
                                .offset(x = rendererLeft, y = rendererTop)
                                .size(width = rendererWidth, height = rendererHeight)
                                .clipToBounds()
                        )
                    }
                }
            }
            Canvas(
                modifier = Modifier
                    .matchParentSize()
                    .graphicsLayer { alpha = frameAlpha }
                    .testTag("rayban-display-lens-mask")
            ) {
                drawImage(
                    image = lensFrame,
                    srcOffset = frameSourceOffset,
                    srcSize = frameSourceSize,
                    dstOffset = frameDestinationOffset,
                    dstSize = frameDestinationSize,
                    filterQuality = FilterQuality.High
                )
            }
        }
    }
}

/**
 * Compose owns this surface; CameraX receives only its provider and viewport.
 * The COMPATIBLE mode is deliberate: a SurfaceView would ignore the lens alpha
 * mask and appear above the transparent Meta renderer on many devices.
 */
@Composable
private fun LensCameraPreview(
    viewModel: RealityViewModel,
    generation: Long,
    modifier: Modifier = Modifier
) {
    var previewView by remember { mutableStateOf<PreviewView?>(null) }
    val activePreviewView = previewView
    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(activePreviewView, lifecycleOwner, viewModel, generation) {
        val view = activePreviewView
        if (view == null) {
            onDispose {}
        } else {
            val streamObserver = Observer<PreviewView.StreamState> { streamState ->
                val isStreaming = streamState == PreviewView.StreamState.STREAMING
                viewModel.onPhonePreviewStreaming(generation, isStreaming)
            }
            fun attachSurface() {
                if (view.width > 0 && view.height > 0) {
                    viewModel.setPhonePreviewSurface(view.surfaceProvider, view.viewPort, generation)
                }
            }
            val layoutListener = View.OnLayoutChangeListener { _, left, top, right, bottom, oldLeft, oldTop, oldRight, oldBottom ->
                if (right - left != oldRight - oldLeft || bottom - top != oldBottom - oldTop) attachSurface()
            }
            view.addOnLayoutChangeListener(layoutListener)
            view.previewStreamState.observe(lifecycleOwner, streamObserver)
            attachSurface()
            onDispose {
                view.removeOnLayoutChangeListener(layoutListener)
                view.previewStreamState.removeObserver(streamObserver)
                viewModel.setPhonePreviewSurface(null, generation = generation)
            }
        }
    }
    AndroidView(
        factory = { viewContext ->
            PreviewView(viewContext).apply {
                implementationMode = PreviewView.ImplementationMode.COMPATIBLE
                scaleType = PreviewView.ScaleType.FILL_CENTER
                previewView = this
            }
        },
        modifier = modifier
            .testTag("rayban-phone-camera-preview")
    )
}

private const val LENS_ENTRANCE_DURATION_MILLIS = 1_180
private const val LENS_FRAME_FADE_IN_MILLIS = 160
private const val LENS_ZOOM_END_MILLIS = 900
private const val LENS_SOFTWARE_FADE_START_MILLIS = LENS_ZOOM_END_MILLIS
private const val LENS_SOFTWARE_FADE_END_MILLIS = LENS_ENTRANCE_DURATION_MILLIS
private const val LENS_RENDERER_GLASS_OPACITY = 0.84f

@Composable
private fun CodeLine(value: String) {
    Text(
        value,
        color = MaterialTheme.colorScheme.tertiary,
        style = MaterialTheme.typography.bodySmall,
        fontFamily = FontFamily.Monospace,
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant, MaterialTheme.shapes.small)
            .padding(10.dp)
    )
}
