package com.luxisoft.realityos

import android.Manifest
import android.content.pm.PackageManager
import android.widget.TextView
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.meta.wearable.dat.core.types.Permission
import kotlinx.coroutines.launch

/**
 * Debug-only immersive stage. The official Mock Device Kit renderer owns the
 * body; simulator state and testing controls live in the end drawer.
 */
@Composable
fun DeveloperPreviewStage(
    viewModel: RealityViewModel,
    enabled: Boolean,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val application = context.applicationContext as RealityOsApplication
    val controller = remember(application) { application.developerPreviewController }
    val preview by controller.state.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    var autoStartAttempted by rememberSaveable { mutableStateOf(false) }

    // The Debug host starts Meta's in-app Display simulation once. A failure is
    // deliberately not retried in a loop; the right drawer provides retry and
    // mode selection. No camera, microphone, recording, or upload is started.
    LaunchedEffect(enabled, preview.active) {
        if (enabled && !preview.active && !autoStartAttempted) {
            autoStartAttempted = true
            val deviceId = controller.start(DeveloperPreviewMode.IN_APP) ?: return@LaunchedEffect
            viewModel.connectDisplay(deviceId)
        }
    }

    Box(modifier = modifier.fillMaxSize()) {
        PreviewSurface(
            state = preview,
            controller = controller,
            modifier = Modifier
                .fillMaxSize()
                .padding(bottom = if (preview.active) 82.dp else 0.dp),
        )
        if (preview.active) {
            Surface(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .navigationBarsPadding()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                color = MaterialTheme.colorScheme.surface.copy(alpha = 0.96f),
                shape = MaterialTheme.shapes.large,
            ) {
                Button(
                    onClick = {
                        scope.launch {
                            if (viewModel.disconnectDisplay()) controller.stop()
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("preview-stop-button"),
                ) {
                    Text(stringResource(R.string.preview_stop_virtual))
                }
            }
        }
    }
}

/** Content rendered inside the shared right-side Preview controls drawer. */
@Composable
fun PreviewControlPanel(
    state: RealityUiState,
    viewModel: RealityViewModel,
    onOpenGlasses: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val application = context.applicationContext as RealityOsApplication
    val controller = remember(application) { application.developerPreviewController }
    val preview by controller.state.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    var selectedMode by rememberSaveable { mutableStateOf(DeveloperPreviewMode.IN_APP) }
    var query by rememberSaveable { mutableStateOf("Where is the yellow drill?") }
    var phoneCameraError by rememberSaveable { mutableStateOf<String?>(null) }
    var requestedPhoneCamera by remember { mutableStateOf<PreviewPhoneCamera?>(null) }
    val cameraPermissionRequired = stringResource(R.string.debug_camera_permission_required)
    val startBeforeCamera = stringResource(R.string.debug_start_before_camera)

    val photoPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        controller.setCapturedPhoto(uri)
    }
    val videoPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        controller.setVideoFeed(uri)
    }
    val phoneCameraPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        val facing = requestedPhoneCamera
        requestedPhoneCamera = null
        if (granted && facing != null) {
            phoneCameraError = null
            controller.setPhoneCamera(facing)
        } else {
            phoneCameraError = cameraPermissionRequired
        }
    }

    fun requestPhoneCamera(facing: PreviewPhoneCamera) {
        if (!preview.active) {
            phoneCameraError = startBeforeCamera
            return
        }
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            phoneCameraError = null
            controller.setPhoneCamera(facing)
        } else {
            requestedPhoneCamera = facing
            phoneCameraPermission.launch(Manifest.permission.CAMERA)
        }
    }

    fun startPreview(mode: DeveloperPreviewMode) {
        scope.launch {
            val deviceId = controller.start(mode) ?: return@launch
            viewModel.connectDisplay(deviceId)
        }
    }

    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        PreviewStateStrip(preview)
        Text(
            preview.message,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            style = MaterialTheme.typography.bodySmall,
        )

        if (!preview.active) {
            Text(stringResource(R.string.preview_select_target), style = MaterialTheme.typography.labelLarge)
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                PreviewModeButton(
                    label = stringResource(R.string.preview_in_app),
                    selected = selectedMode == DeveloperPreviewMode.IN_APP,
                    onClick = { selectedMode = DeveloperPreviewMode.IN_APP },
                )
                PreviewModeButton(
                    label = stringResource(R.string.preview_chrome),
                    selected = selectedMode == DeveloperPreviewMode.CHROME,
                    onClick = { selectedMode = DeveloperPreviewMode.CHROME },
                )
            }
            Button(
                onClick = { startPreview(selectedMode) },
                enabled = !state.wearable.sessionActive,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.preview_restart_virtual))
            }
            if (state.wearable.sessionActive) {
                Text(
                    stringResource(R.string.preview_disconnect_first),
                    color = MaterialTheme.colorScheme.secondary,
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        } else {
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            DeviceLifecycleControls(controller, preview)
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            PermissionControls(controller)
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            MediaControls(
                preview = preview,
                onSelectPhoto = { photoPicker.launch(arrayOf("image/jpeg", "image/png")) },
                onSelectVideo = { videoPicker.launch(arrayOf("video/*")) },
                onUsePhoneCamera = ::requestPhoneCamera,
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            SpeechControls(
                query = query,
                onQueryChange = { query = it },
                onPartial = { controller.simulateTranscription(query, isFinal = false) },
                onFinal = { controller.simulateTranscription(query, isFinal = true) },
            )
        }

        preview.chrome?.takeIf { preview.mode == DeveloperPreviewMode.CHROME }?.let { chrome ->
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Text(stringResource(R.string.preview_chrome_title), style = MaterialTheme.typography.labelLarge)
            Text(
                stringResource(R.string.preview_chrome_body),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodySmall,
            )
            CodeLine(chrome.adbForwardCommand)
            CodeLine(chrome.url)
        }

        val issue = preview.error ?: phoneCameraError
        if (issue != null) {
            Text(issue, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            OutlinedButton(
                onClick = {
                    phoneCameraError = null
                    controller.clearError()
                },
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
            disabledLabelColor = if (active) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurfaceVariant,
        ),
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
    onSelectVideo: () -> Unit,
    onUsePhoneCamera: (PreviewPhoneCamera) -> Unit,
) {
    Text(stringResource(R.string.debug_media_inputs), style = MaterialTheme.typography.labelLarge)
    Text(
        stringResource(R.string.debug_media_hint),
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        style = MaterialTheme.typography.bodySmall,
    )
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        LifecycleButton(stringResource(R.string.debug_choose_photo)) { onSelectPhoto() }
        LifecycleButton(stringResource(R.string.debug_choose_video)) { onSelectVideo() }
        LifecycleButton(stringResource(R.string.debug_rear_camera)) { onUsePhoneCamera(PreviewPhoneCamera.BACK) }
        LifecycleButton(stringResource(R.string.debug_front_camera)) { onUsePhoneCamera(PreviewPhoneCamera.FRONT) }
    }
    preview.capturedPhotoName?.let { SelectedMedia(stringResource(R.string.debug_photo), it) }
    preview.videoFeedName?.let { SelectedMedia(stringResource(R.string.debug_video), it) }
    preview.phoneCamera?.let { SelectedMedia(stringResource(R.string.debug_phone_feed), it.name.lowercase()) }
}

@Composable
private fun SelectedMedia(label: String, value: String) {
    Text(
        "$label: $value",
        color = MaterialTheme.colorScheme.tertiary,
        style = MaterialTheme.typography.labelSmall,
        fontFamily = FontFamily.Monospace,
    )
}

@Composable
private fun SpeechControls(
    query: String,
    onQueryChange: (String) -> Unit,
    onPartial: () -> Unit,
    onFinal: () -> Unit,
) {
    Text(stringResource(R.string.debug_speech), style = MaterialTheme.typography.labelLarge)
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        label = { Text(stringResource(R.string.debug_spoken_query)) },
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
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
    modifier: Modifier = Modifier,
) {
    BoxWithConstraints(
        modifier = modifier
            .background(Color(0xFF070B12))
            .background(
                Brush.radialGradient(
                    colors = listOf(Color(0x1A43D99A), Color(0x0CC2F7D5), Color.Transparent),
                ),
            )
            .testTag("meta-display-preview"),
        contentAlignment = Alignment.Center,
    ) {
        val displaySize = minOf(maxWidth, maxHeight, 600.dp)
        when (state.mode) {
            DeveloperPreviewMode.IN_APP -> {
                if (state.active) {
                    key(state.previewGeneration) {
                        AndroidView(
                            factory = { viewContext ->
                                controller.createInAppPreviewView(viewContext) ?: TextView(viewContext).apply {
                                    text = viewContext.getString(R.string.preview_waiting_renderer)
                                    setTextColor(android.graphics.Color.WHITE)
                                    gravity = android.view.Gravity.CENTER
                                }
                            },
                            modifier = Modifier.size(displaySize),
                        )
                    }
                } else {
                    Text(
                        stringResource(R.string.preview_waiting_renderer),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            DeveloperPreviewMode.CHROME -> Text(
                stringResource(R.string.preview_desktop_only),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodyMedium,
            )
            null -> Text(
                stringResource(R.string.preview_waiting_renderer),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Surface(
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(14.dp),
            color = Color.Black.copy(alpha = 0.48f),
            contentColor = MaterialTheme.colorScheme.tertiary,
            shape = MaterialTheme.shapes.small,
        ) {
            Text(
                stringResource(R.string.preview_simulator_title),
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp),
                style = MaterialTheme.typography.labelMedium,
            )
        }
    }
}

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
            .padding(10.dp),
    )
}
