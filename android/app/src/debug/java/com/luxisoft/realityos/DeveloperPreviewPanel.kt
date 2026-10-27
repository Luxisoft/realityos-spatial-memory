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
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.meta.wearable.dat.core.types.Permission
import kotlinx.coroutines.launch

// Keep the Debug lab recognisable while using the same high-contrast field
// palette as the production host. The simulated controls should not look like
// a separate, unfinished application.
private val LabInk = Color(0xFF142033)
private val LabSlate = Color(0xFF1C2D45)
private val LabSignal = Color(0xFF63E6BE)
private val LabWarning = Color(0xFFF6BB5D)
private val LabError = Color(0xFFFFB4AB)
private val LabPaper = Color(0xFFF5F7FB)

/**
 * Debug-only phone lab for Meta's virtual Display glasses. The preview itself
 * is Meta's renderer; this screen only controls the simulated device around it.
 */
@Composable
fun DeveloperPreviewPanel(
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
            phoneCameraError = "Phone camera permission is required for this mock feed."
        }
    }

    fun requestPhoneCamera(facing: PreviewPhoneCamera) {
        if (!preview.active) {
            phoneCameraError = "Start the virtual glasses before selecting the phone camera."
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

    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = LabInk),
        shape = RoundedCornerShape(20.dp),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "Developer preview · virtual Meta Ray-Ban Display",
                color = LabSignal,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            Text(
                "Debug build only. The square below is Meta's Display renderer, not a recreated phone UI.",
                color = LabPaper,
                style = MaterialTheme.typography.bodySmall,
            )

            PreviewStateStrip(preview)
            HorizontalDivider(color = Color.White.copy(alpha = 0.18f))

            Text("Preview target", color = LabPaper, style = MaterialTheme.typography.labelLarge)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                PreviewModeButton(
                    label = "In app",
                    selected = selectedMode == DeveloperPreviewMode.IN_APP,
                    enabled = !preview.active,
                ) { selectedMode = DeveloperPreviewMode.IN_APP }
                PreviewModeButton(
                    label = "Chrome",
                    selected = selectedMode == DeveloperPreviewMode.CHROME,
                    enabled = !preview.active,
                ) { selectedMode = DeveloperPreviewMode.CHROME }
                if (!preview.active) {
                    Button(
                        onClick = {
                            scope.launch {
                                val deviceId = controller.start(selectedMode) ?: return@launch
                                viewModel.connectDisplay(deviceId)
                            }
                        },
                        enabled = enabled,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = LabSignal,
                            contentColor = LabInk,
                        ),
                    ) { Text("Start virtual glasses") }
                } else {
                    OutlinedButton(
                        onClick = {
                            scope.launch {
                                if (viewModel.disconnectDisplay()) controller.stop()
                            }
                        },
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = LabWarning),
                    ) { Text("Stop preview") }
                }
            }
            if (!enabled && !preview.active) {
                Text(
                    "Disconnect the active Display session before starting a virtual device.",
                    color = LabWarning,
                    style = MaterialTheme.typography.bodySmall,
                )
            }

            if (preview.active) {
                DeviceLifecycleControls(controller, preview)
                PermissionControls(controller)
                MediaControls(
                    preview = preview,
                    onSelectPhoto = { photoPicker.launch(arrayOf("image/jpeg", "image/png")) },
                    onSelectVideo = { videoPicker.launch(arrayOf("video/*")) },
                    onUsePhoneCamera = ::requestPhoneCamera,
                )
                SpeechControls(
                    query = query,
                    onQueryChange = { query = it },
                    onPartial = { controller.simulateTranscription(query, isFinal = false) },
                    onFinal = { controller.simulateTranscription(query, isFinal = true) },
                )
                PreviewSurface(preview, controller)
            }

            val issue = preview.error ?: phoneCameraError
            if (issue != null) {
                Text(issue, color = LabError, style = MaterialTheme.typography.bodySmall)
                OutlinedButton(
                    onClick = {
                        phoneCameraError = null
                        controller.clearError()
                    },
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = LabPaper),
                ) { Text("Dismiss") }
            }
            Text(preview.message, color = LabPaper.copy(alpha = 0.86f), style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun PreviewStateStrip(state: DeveloperPreviewState) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        PreviewBadge("Mock", state.active)
        PreviewBadge("Power", state.poweredOn)
        PreviewBadge("Open", state.unfolded)
        PreviewBadge("Worn", state.worn)
        PreviewBadge("${state.mode ?: "No target"}", state.mode != null)
    }
}

@Composable
private fun PreviewBadge(label: String, active: Boolean) {
    AssistChip(
        onClick = {},
        enabled = false,
        label = { Text(label, color = if (active) LabSignal else LabPaper.copy(alpha = 0.56f)) },
        colors = androidx.compose.material3.AssistChipDefaults.assistChipColors(
            disabledContainerColor = if (active) LabSlate else Color.White.copy(alpha = 0.08f),
            disabledLabelColor = if (active) LabSignal else LabPaper.copy(alpha = 0.56f),
        ),
    )
}

@Composable
private fun PreviewModeButton(
    label: String,
    selected: Boolean,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    if (selected) {
        Button(
            onClick = onClick,
            enabled = enabled,
            colors = ButtonDefaults.buttonColors(containerColor = LabSlate, contentColor = LabSignal),
        ) { Text(label) }
    } else {
        OutlinedButton(
            onClick = onClick,
            enabled = enabled,
            colors = ButtonDefaults.outlinedButtonColors(contentColor = LabPaper),
        ) { Text(label) }
    }
}

@Composable
private fun DeviceLifecycleControls(
    controller: DeveloperPreviewController,
    state: DeveloperPreviewState,
) {
    Text("Virtual device lifecycle", color = LabPaper, style = MaterialTheme.typography.labelLarge)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        LifecycleButton(if (state.poweredOn) "Power off" else "Power on") {
            if (state.poweredOn) controller.powerOff() else controller.powerOn()
        }
        LifecycleButton(if (state.unfolded) "Fold" else "Unfold") {
            if (state.unfolded) controller.fold() else controller.unfold()
        }
        LifecycleButton(if (state.worn) "Remove" else "Wear") {
            if (state.worn) controller.doff() else controller.don()
        }
    }
}

@Composable
private fun LifecycleButton(label: String, onClick: () -> Unit) {
    ElevatedButton(
        onClick = onClick,
        colors = ButtonDefaults.elevatedButtonColors(containerColor = LabSlate, contentColor = LabPaper),
    ) { Text(label) }
}

@Composable
private fun PermissionControls(controller: DeveloperPreviewController) {
    Text("DAT permissions", color = LabPaper, style = MaterialTheme.typography.labelLarge)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        PermissionButton("Camera allowed") { controller.setDatPermission(Permission.CAMERA, granted = true) }
        PermissionButton("Camera denied") { controller.setDatPermission(Permission.CAMERA, granted = false) }
        PermissionButton("Mic allowed") { controller.setDatPermission(Permission.MICROPHONE, granted = true) }
        PermissionButton("Mic denied") { controller.setDatPermission(Permission.MICROPHONE, granted = false) }
    }
}

@Composable
private fun PermissionButton(label: String, onClick: () -> Unit) {
    OutlinedButton(
        onClick = onClick,
        colors = ButtonDefaults.outlinedButtonColors(contentColor = LabPaper),
    ) { Text(label, style = MaterialTheme.typography.labelSmall) }
}

@Composable
private fun MediaControls(
    preview: DeveloperPreviewState,
    onSelectPhoto: () -> Unit,
    onSelectVideo: () -> Unit,
    onUsePhoneCamera: (PreviewPhoneCamera) -> Unit,
) {
    Text("Mock camera inputs", color = LabPaper, style = MaterialTheme.typography.labelLarge)
    Text(
        "Use JPEG/PNG for photo capture; use AVC/H.264 or HEVC/H.265 for video streaming.",
        color = LabPaper.copy(alpha = 0.74f),
        style = MaterialTheme.typography.bodySmall,
    )
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        LifecycleButton("Choose photo") { onSelectPhoto() }
        LifecycleButton("Choose video") { onSelectVideo() }
        LifecycleButton("Phone rear camera") { onUsePhoneCamera(PreviewPhoneCamera.BACK) }
        LifecycleButton("Phone front camera") { onUsePhoneCamera(PreviewPhoneCamera.FRONT) }
    }
    preview.capturedPhotoName?.let { SelectedMedia("Photo", it) }
    preview.videoFeedName?.let { SelectedMedia("Video", it) }
    preview.phoneCamera?.let { SelectedMedia("Phone feed", it.name.lowercase()) }
}

@Composable
private fun SelectedMedia(label: String, value: String) {
    Text(
        "$label: $value",
        color = LabSignal,
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
    Text("Mock speech", color = LabPaper, style = MaterialTheme.typography.labelLarge)
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        label = { Text("Simulated spoken query") },
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
    )
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        LifecycleButton("Send partial") { onPartial() }
        Button(
            onClick = onFinal,
            colors = ButtonDefaults.buttonColors(containerColor = LabSignal, contentColor = LabInk),
        ) { Text("Send final query") }
    }
}

@Composable
private fun PreviewSurface(
    state: DeveloperPreviewState,
    controller: DeveloperPreviewController,
) {
    HorizontalDivider(color = Color.White.copy(alpha = 0.18f))
    when (state.mode) {
        DeveloperPreviewMode.IN_APP -> {
            Text("Meta Display preview", color = LabPaper, style = MaterialTheme.typography.labelLarge)
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(360.dp)
                    .clip(RoundedCornerShape(18.dp))
                    .background(Color.Black),
                contentAlignment = Alignment.Center,
            ) {
                key(state.previewGeneration) {
                    AndroidView(
                        factory = { viewContext ->
                            controller.createInAppPreviewView(viewContext) ?: TextView(viewContext).apply {
                                text = "Waiting for Meta Display…"
                                setTextColor(android.graphics.Color.WHITE)
                                gravity = android.view.Gravity.CENTER
                            }
                        },
                        modifier = Modifier.size(320.dp),
                    )
                }
            }
        }
        DeveloperPreviewMode.CHROME -> {
            Text("Chrome Display Simulator", color = LabPaper, style = MaterialTheme.typography.labelLarge)
            Text(
                "1. Connect this phone by USB with debugging enabled.\n2. Run the command on your computer.\n3. Open the URL in Chrome and enable Meta Ray-Ban Display Simulator.",
                color = LabPaper.copy(alpha = 0.82f),
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
        color = LabSignal,
        style = MaterialTheme.typography.bodySmall,
        fontFamily = FontFamily.Monospace,
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.Black.copy(alpha = 0.36f), RoundedCornerShape(8.dp))
            .padding(10.dp),
    )
}
