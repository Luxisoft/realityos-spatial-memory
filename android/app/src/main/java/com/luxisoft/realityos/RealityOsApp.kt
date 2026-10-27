package com.luxisoft.realityos

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/**
 * Native Android host for physical or virtual Meta Ray-Ban Display sessions.
 * The operational UI stays on the glasses; this screen makes connection state
 * and safe, editable device provisioning unmistakable on the phone.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RealityOsApp(
    viewModel: RealityViewModel,
    onRegisterWithMeta: () -> Unit,
    onConnectDisplay: () -> Unit,
    onDisconnectDisplay: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var editingConnection by rememberSaveable { mutableStateOf(state.provisioning == null) }

    LaunchedEffect(state.provisioning) {
        if (state.provisioning == null) editingConnection = true
    }

    RealityOsTheme {
        Scaffold(
            containerColor = MaterialTheme.colorScheme.background,
            contentWindowInsets = WindowInsets.safeDrawing,
            topBar = {
                CenterAlignedTopAppBar(
                    title = {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("RealityOS", style = MaterialTheme.typography.titleLarge)
                            Text(
                                "SPATIAL MEMORY HOST",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.Bold,
                            )
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.background,
                        titleContentColor = MaterialTheme.colorScheme.onBackground,
                    ),
                )
            },
            bottomBar = {
                if (editingConnection) {
                    ProvisioningBottomBar(
                        loading = state.virtualProfileLoading,
                        enabled = !state.virtualProfileLoading,
                        onSave = {
                            if (viewModel.saveProvisioning()) {
                                editingConnection = false
                            }
                        },
                    )
                } else {
                    DisplayBottomBar(
                        state = state,
                        onConnect = onConnectDisplay,
                        onDisconnect = onDisconnectDisplay,
                    )
                }
            },
        ) { contentPadding ->
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(contentPadding)
                    .consumeWindowInsets(contentPadding)
                    .imePadding(),
                contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                item {
                    SignalHeader(
                        connected = state.wearable.sessionActive,
                        live = state.provisioning?.processingMode?.lowercase() == "live" ||
                            state.provisioningDraft.processingMode?.lowercase() == "live",
                    )
                }
                item {
                    HostStateCard(state = state, onRegisterWithMeta = onRegisterWithMeta)
                }
                if (editingConnection) {
                    item {
                        ProvisioningCard(
                            state = state,
                            onUpdate = viewModel::updateProvisioningDraft,
                            onReloadLiveProfile = viewModel::loadVirtualDeviceProfile,
                        )
                    }
                } else {
                    item {
                        SavedConnectionCard(
                            provisioning = state.provisioning ?: return@item,
                            onEdit = { editingConnection = true },
                            onReloadLiveProfile = {
                                editingConnection = true
                                viewModel.loadVirtualDeviceProfile()
                            },
                        )
                    }
                    item {
                        DeveloperPreviewPanel(
                            viewModel = viewModel,
                            enabled = !state.wearable.sessionActive,
                        )
                    }
                }
                item { NoticeCard(message = state.message, error = state.virtualProfileError) }
            }
        }
    }
}

@Composable
private fun SignalHeader(connected: Boolean, live: Boolean) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        shape = MaterialTheme.shapes.extraLarge,
    ) {
        Row(
            modifier = Modifier.padding(20.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            SpatialSignal(active = connected)
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    if (connected) "Signal connected" else "Ready to connect",
                    style = MaterialTheme.typography.headlineSmall,
                )
                Text(
                    if (connected) {
                        "RealityOS is routing the active Display session."
                    } else {
                        "Provision the host, then start physical or virtual glasses."
                    },
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyMedium,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    StateChip(if (live) "LIVE META" else "CONNECTION SETUP", live)
                    StateChip(if (connected) "DISPLAY ACTIVE" else "DISPLAY IDLE", connected)
                }
            }
        }
    }
}

@Composable
private fun SpatialSignal(active: Boolean) {
    val signal = if (active) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline
    Canvas(
        modifier = Modifier
            .size(66.dp)
            .drawBehind {
                drawCircle(
                    color = signal.copy(alpha = if (active) 0.14f else 0.08f),
                    radius = size.minDimension / 2,
                )
            },
    ) {
        val center = Offset(size.width / 2, size.height / 2)
        drawCircle(color = signal, radius = size.minDimension * 0.11f)
        drawCircle(color = signal, radius = size.minDimension * 0.27f, style = Stroke(width = 2.5f))
        drawCircle(
            color = signal.copy(alpha = 0.55f),
            radius = size.minDimension * 0.43f,
            style = Stroke(width = 1.6f),
        )
        drawLine(
            color = signal,
            start = Offset(center.x, size.height * 0.08f),
            end = Offset(center.x, size.height * 0.24f),
            strokeWidth = 2.5f,
        )
    }
}

@Composable
private fun StateChip(label: String, active: Boolean) {
    AssistChip(
        onClick = {},
        enabled = false,
        label = { Text(label) },
        colors = AssistChipDefaults.assistChipColors(
            disabledContainerColor = if (active) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surface
            },
            disabledLabelColor = if (active) {
                MaterialTheme.colorScheme.onPrimaryContainer
            } else {
                MaterialTheme.colorScheme.onSurfaceVariant
            },
        ),
    )
}

@Composable
private fun HostStateCard(state: RealityUiState, onRegisterWithMeta: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth(), shape = MaterialTheme.shapes.extraLarge) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("Display host", style = MaterialTheme.typography.titleLarge)
            Text(
                "This phone handles Meta registration, secure device identity, Bluetooth transport, and voice output. Register and Query operate on the glasses.",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodyMedium,
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            StatusRow("Meta registration", state.wearable.registration.lowercase().replace('_', ' '))
            StatusRow("Paired device", if (state.wearable.deviceAvailable) "available" else "not detected")
            StatusRow("Display session", if (state.wearable.sessionActive) "active" else "not connected")
            OutlinedButton(onClick = onRegisterWithMeta, modifier = Modifier.fillMaxWidth()) {
                Text("Register with Meta AI")
            }
        }
    }
}

@Composable
private fun StatusRow(label: String, value: String) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(label, modifier = Modifier.weight(0.42f), color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(
            value,
            modifier = Modifier.weight(0.58f),
            textAlign = TextAlign.End,
            style = MaterialTheme.typography.labelLarge,
        )
    }
}

@Composable
private fun ProvisioningCard(
    state: RealityUiState,
    onUpdate: (String?, String?, String?, String?) -> Unit,
    onReloadLiveProfile: () -> Unit,
) {
    val draft = state.provisioningDraft
    var revealDeviceKey by rememberSaveable { mutableStateOf(false) }
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.extraLarge,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("Live connection", style = MaterialTheme.typography.titleLarge)
                    Text(
                        "These values connect this host to the real RealityOS server. You can replace any of them with your own server values.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                StateChip(
                    if (draft.processingMode?.lowercase() == "live") "LIVE" else "SETUP",
                    draft.processingMode?.lowercase() == "live",
                )
            }
            if (state.virtualProfileLoading) {
                LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                Text(
                    "Loading a real virtual-device identity from the HTTPS server…",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodySmall,
                )
            }
            state.virtualProfileError?.let { error ->
                Text(error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            }
            OutlinedTextField(
                value = draft.apiBaseUrl,
                onValueChange = { onUpdate(it, null, null, null) },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("RealityOS HTTPS URL") },
                supportingText = { Text("HTTPS is required. Default: realityos.luxisoft.com") },
                singleLine = true,
            )
            OutlinedTextField(
                value = draft.workspaceId,
                onValueChange = { onUpdate(null, it, null, null) },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Workspace ID") },
                supportingText = {
                    Text(draft.workspaceName?.let { "Workspace: $it" } ?: "Your authorized workspace UUID")
                },
                singleLine = true,
            )
            OutlinedTextField(
                value = draft.deviceId,
                onValueChange = { onUpdate(null, null, it, null) },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Device ID") },
                supportingText = { Text("Scoped to this RealityOS workspace") },
                singleLine = true,
            )
            OutlinedTextField(
                value = draft.deviceKey,
                onValueChange = { onUpdate(null, null, null, it) },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Device key") },
                supportingText = { Text("Stored encrypted on this phone after saving") },
                visualTransformation = if (revealDeviceKey) {
                    VisualTransformation.None
                } else {
                    PasswordVisualTransformation()
                },
                singleLine = true,
            )
            TextButton(onClick = { revealDeviceKey = !revealDeviceKey }) {
                Text(if (revealDeviceKey) "Hide device key" else "Show device key")
            }
            draft.expiresAt?.let { expiry ->
                Text(
                    "Virtual device expires ${formatExpiry(expiry)}. Reloading issues a fresh live credential.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodySmall,
                )
            }
            OutlinedButton(
                onClick = onReloadLiveProfile,
                enabled = !state.virtualProfileLoading,
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Reload live virtual-device values") }
        }
    }
}

@Composable
private fun SavedConnectionCard(
    provisioning: DeviceProvisioning,
    onEdit: () -> Unit,
    onReloadLiveProfile: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.extraLarge,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("Active connection", style = MaterialTheme.typography.titleLarge)
            StatusRow("Server", provisioning.apiBaseUrl)
            StatusRow("Workspace", provisioning.workspaceName ?: provisioning.workspaceId)
            StatusRow("Device", provisioning.deviceId)
            provisioning.expiresAt?.let { expiry ->
                StatusRow("Credential", "expires ${formatExpiry(expiry)}")
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = onEdit, modifier = Modifier.weight(1f)) {
                    Text("Edit connection")
                }
                if (provisioning.source == ProvisioningSource.VIRTUAL_LIVE) {
                    Button(onClick = onReloadLiveProfile, modifier = Modifier.weight(1f)) {
                        Text("Refresh live values")
                    }
                }
            }
        }
    }
}

@Composable
private fun NoticeCard(message: String, error: String?) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (error == null) {
                MaterialTheme.colorScheme.surfaceVariant
            } else {
                MaterialTheme.colorScheme.errorContainer
            },
        ),
        shape = MaterialTheme.shapes.large,
    ) {
        Text(
            error ?: message,
            modifier = Modifier.padding(16.dp),
            color = if (error == null) {
                MaterialTheme.colorScheme.onSurfaceVariant
            } else {
                MaterialTheme.colorScheme.onErrorContainer
            },
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

@Composable
private fun ProvisioningBottomBar(loading: Boolean, enabled: Boolean, onSave: () -> Unit) {
    BottomAppBar(containerColor = MaterialTheme.colorScheme.surface) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 8.dp),
        ) {
            Button(
                onClick = onSave,
                enabled = enabled && !loading,
                modifier = Modifier.fillMaxWidth(),
            ) { Text(if (loading) "Loading live connection…" else "Save live connection") }
        }
    }
}

@Composable
private fun DisplayBottomBar(
    state: RealityUiState,
    onConnect: () -> Unit,
    onDisconnect: () -> Unit,
) {
    BottomAppBar(containerColor = MaterialTheme.colorScheme.surface) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 8.dp),
        ) {
            if (state.wearable.sessionActive) {
                OutlinedButton(onClick = onDisconnect, modifier = Modifier.fillMaxWidth()) {
                    Text("Disconnect Display")
                }
            } else {
                Button(onClick = onConnect, modifier = Modifier.fillMaxWidth()) {
                    Text("Connect physical Display")
                }
            }
        }
    }
}

private fun formatExpiry(value: Instant): String = value
    .atZone(ZoneId.systemDefault())
    .format(DateTimeFormatter.ofPattern("MMM d, HH:mm"))
