package com.luxisoft.realityos

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle

/**
 * Administrator-only host screen. Field operation happens on Meta Ray-Ban
 * Display after one-time enrollment and connection are complete.
 */
@Composable
fun RealityOsApp(
    viewModel: RealityViewModel,
    onRegisterWithMeta: () -> Unit,
    onConnectDisplay: () -> Unit,
    onDisconnectDisplay: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    MaterialTheme {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text("RealityOS Display Host", style = MaterialTheme.typography.headlineSmall)
            Text(
                "This Android host is used only for Meta registration, encrypted device provisioning, Bluetooth transport, and audio routing. Operational controls are on the glasses.",
                style = MaterialTheme.typography.bodyMedium,
            )
            if (state.provisioning == null) {
                ProvisioningForm(onSave = viewModel::saveProvisioning)
            } else {
                ConnectionCard(state, onRegisterWithMeta, onConnectDisplay, onDisconnectDisplay)
                DeveloperPreviewPanel(viewModel = viewModel, enabled = !state.wearable.sessionActive)
            }
            if (state.busy) CircularProgressIndicator()
            Card(modifier = Modifier.fillMaxWidth()) {
                Text(state.message, modifier = Modifier.padding(16.dp))
            }
        }
    }
}

@Composable
private fun ProvisioningForm(onSave: (String, String, String, String) -> Unit) {
    var endpoint by rememberSaveable { mutableStateOf("https://your-server.example/v1") }
    var workspaceId by rememberSaveable { mutableStateOf("") }
    var deviceId by rememberSaveable { mutableStateOf("") }
    var deviceKey by rememberSaveable { mutableStateOf("") }
    Text("Administrator provisioning", style = MaterialTheme.typography.titleLarge)
    Text("Use a device credential issued once by the RealityOS administrator. Do not enter a Meta model key here.")
    OutlinedTextField(endpoint, { endpoint = it }, label = { Text("RealityOS API URL") }, singleLine = true, modifier = Modifier.fillMaxWidth())
    OutlinedTextField(workspaceId, { workspaceId = it }, label = { Text("Workspace UUID") }, singleLine = true, modifier = Modifier.fillMaxWidth())
    OutlinedTextField(deviceId, { deviceId = it }, label = { Text("Device ID") }, singleLine = true, modifier = Modifier.fillMaxWidth())
    OutlinedTextField(
        deviceKey,
        { deviceKey = it },
        label = { Text("Device key") },
        visualTransformation = PasswordVisualTransformation(),
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
    Button(onClick = { onSave(endpoint, workspaceId, deviceId, deviceKey) }) { Text("Save provisioning") }
}

@Composable
private fun ConnectionCard(
    state: RealityUiState,
    onRegisterWithMeta: () -> Unit,
    onConnectDisplay: () -> Unit,
    onDisconnectDisplay: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Meta Ray-Ban Display", style = MaterialTheme.typography.titleLarge)
            Text("Registration: ${state.wearable.registration}")
            Text("Paired device available: ${if (state.wearable.deviceAvailable) "yes" else "no"}")
            Text("Session: ${if (state.wearable.sessionActive) "active" else "not connected"}")
            Text("Display: ${if (state.wearable.displayReady) "ready" else "not connected"}")
            Button(onClick = onRegisterWithMeta) { Text("Register with Meta AI") }
            Button(onClick = onConnectDisplay, enabled = !state.wearable.sessionActive) { Text("Connect Display") }
            Button(onClick = onDisconnectDisplay, enabled = state.wearable.sessionActive) { Text("Disconnect Display") }
        }
    }
}
