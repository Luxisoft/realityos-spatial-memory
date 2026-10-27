package com.luxisoft.realityos

import android.Manifest
import android.content.pm.PackageManager
import android.widget.TextView
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.meta.wearable.dat.core.types.Permission
import kotlinx.coroutines.launch

/**
 * Debug-only main stage. It preserves both official simulator routes: Meta's
 * in-app renderer and the supplementary Chrome simulator route.
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
    var selectedMode by rememberSaveable { mutableStateOf(DeveloperPreviewMode.IN_APP) }

    Card(
        modifier = modifier,
        shape = MaterialTheme.shapes.extraLarge,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Text(stringResource(R.string.preview_simulator_title), style = MaterialTheme.typography.titleLarge)
            Text(
                stringResource(R.string.preview_simulator_body),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            PreviewStateStrip(preview)
            if (!preview.active) {
                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                Text(
                    stringResource(R.string.preview_select_target),
                    style = MaterialTheme.typography.labelLarge,
                )
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
                    Button(
                        onClick = {
                            scope.launch {
                                val deviceId = controller.start(selectedMode) ?: return@launch
                                viewModel.connectDisplay(deviceId)
                            }
                        },
                        enabled = enabled,
                    ) { Text(stringResource(R.string.preview_start_virtual)) }
                }
                if (!enabled) {
                    Text(
                        stringResource(R.string.preview_disconnect_first),
                        color = MaterialTheme.colorScheme.secondary,
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            } else {
                OutlinedButton(
                    onClick = {
                        scope.launch {
                            if (viewModel.disconnectDisplay()) controller.stop()
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text(stringResource(R.string.preview_stop_virtual)) }
            }
            PreviewSurface(preview, controller)
            preview.error?.let { error ->
                Text(error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                TextButtonClear(controller)
            }
        }
    }
}

/** Debug-only secondary drawer page. It deliberately does not recreate Display UI. */
@Composable
fun DeveloperLabControls(viewModel: RealityViewModel, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val application = context.applicationContext as RealityOsApplication
    val controller = remember(application) { application.developerPreviewController }
    val preview by controller.state.collectAsStateWithLifecycle()
    var query by rememberSaveable { mutableStateOf("Where is the yellow drill?") }
    var phoneCameraError by rememberSaveable { mutableStateOf<String?>(null) }
    var requestedPhoneCamera by remember { mutableStateOf<PreviewPhoneCamera?>(null) }

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
            phoneCameraError = context.getString(R.string.debug_camera_permission_required)
        }
    }

    fun requestPhoneCamera(facing: PreviewPhoneCamera) {
        if (!preview.active) {
            phoneCameraError = context.getString(R.string.debug_start_before_camera)
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

    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionHeading(
            title = stringResource(R.string.debug_lab_title),
            body = stringResource(R.string.debug_lab_body),
        )
        if (!preview.active) {
            Card(shape = MaterialTheme.shapes.large) {
                Text(
                    stringResource(R.string.debug_start_prompt),
                    modifier = Modifier.padding(20.dp),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
            return@Column
        }
        Card(shape = MaterialTheme.shapes.large) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
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
                Text(
                    preview.message,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodySmall,
                )
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
        Button(onClick = onClick, colors = ButtonDefaults.buttonColors()) { Text(label) }
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
    ElevatedButton(onClick = onClick) { Text(label) }
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
    OutlinedButton(onClick = onClick) { Text(label, style = MaterialTheme.typography.labelSmall) }
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
        color = MaterialTheme.colorScheme.primary,
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
private fun PreviewSurface(state: DeveloperPreviewState, controller: DeveloperPreviewController) {
    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
    when (state.mode) {
        DeveloperPreviewMode.IN_APP -> {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(360.dp)
                    .clip(RoundedCornerShape(22.dp))
                    .background(Color.Black),
                contentAlignment = Alignment.Center,
            ) {
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
                            modifier = Modifier.size(320.dp),
                        )
                    }
                } else {
                    Text(
                        stringResource(R.string.preview_waiting_renderer),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
        DeveloperPreviewMode.CHROME -> {
            Text(stringResource(R.string.preview_chrome_title), style = MaterialTheme.typography.titleMedium)
            Text(
                stringResource(R.string.preview_chrome_body),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodySmall,
            )
            state.chrome?.let { chrome ->
                CodeLine(chrome.adbForwardCommand)
                CodeLine(chrome.url)
            }
        }
        null -> Unit
    }
}

@Composable
private fun CodeLine(value: String) {
    Text(
        value,
        color = MaterialTheme.colorScheme.primary,
        style = MaterialTheme.typography.bodySmall,
        fontFamily = FontFamily.Monospace,
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.background, RoundedCornerShape(8.dp))
            .padding(10.dp),
    )
}

@Composable
private fun TextButtonClear(controller: DeveloperPreviewController) {
    OutlinedButton(onClick = controller::clearError) { Text(stringResource(R.string.debug_dismiss)) }
}
