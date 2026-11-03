package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import org.json.JSONObject

@Composable
internal fun StorageConnectionForm(existing: JSONObject?, busy: Boolean, onSave: (JSONObject) -> Unit, onClose: () -> Unit) {
    var name by remember { mutableStateOf(existing?.optString("name").orEmpty()) }
    var endpoint by remember { mutableStateOf(existing?.optString("endpoint").orEmpty()) }
    var bucket by remember { mutableStateOf(existing?.optString("bucket").orEmpty()) }
    var region by remember { mutableStateOf(existing?.optString("region") ?: "auto") }
    var prefix by remember { mutableStateOf(existing?.optString("prefix").orEmpty()) }
    var provider by remember { mutableStateOf(existing?.optString("provider") ?: "r2") }
    // Credentials deliberately do not enter SavedState or preferences.
    var access by remember { mutableStateOf("") }
    var secret by remember { mutableStateOf("") }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text(localizedText(R.string.storage_connection), style = MaterialTheme.typography.titleLarge)
        Text(localizedText(R.string.storage_credentials_help))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("r2", "s3").forEach { value ->
                FilterChip(selected = provider == value, onClick = {
                    provider = value
                    region = if (value == "r2") "auto" else "us-east-1"
                }, enabled = existing == null && !busy, label = { Text(value.uppercase()) })
            }
        }
        OutlinedTextField(name, { name = it }, label = { Text(localizedText(R.string.storage_name)) }, modifier = Modifier.fillMaxWidth(), enabled = !busy)
        OutlinedTextField(endpoint, { endpoint = it.trim() }, label = { Text("Endpoint HTTPS") }, placeholder = { Text("https://ACCOUNT.r2.cloudflarestorage.com") }, modifier = Modifier.fillMaxWidth(), enabled = existing == null && !busy)
        OutlinedTextField(bucket, { bucket = it.trim() }, label = { Text("Bucket") }, modifier = Modifier.fillMaxWidth(), enabled = existing == null && !busy)
        OutlinedTextField(region, { region = it.trim() }, label = { Text(localizedText(R.string.storage_region)) }, modifier = Modifier.fillMaxWidth(), enabled = existing == null && !busy)
        OutlinedTextField(prefix, { prefix = it }, label = { Text(localizedText(R.string.storage_folder)) }, modifier = Modifier.fillMaxWidth(), enabled = existing == null && !busy)
        OutlinedTextField(access, { access = it.trim() }, label = { Text("Access Key ID") }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth(), enabled = !busy)
        OutlinedTextField(secret, { secret = it.trim() }, label = { Text("Secret Access Key") }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth(), enabled = !busy)
        Button(onClick = {
            val body = JSONObject().put("name", name).put("provider", provider).put("endpoint", endpoint).put("bucket", bucket).put("region", region).put("prefix", prefix)
            if (access.isNotBlank() && secret.isNotBlank()) body.put("access_key", access).put("secret_key", secret)
            onSave(body)
        }, enabled = !busy && name.length >= 2 && bucket.isNotBlank() && endpoint.startsWith("https://") && ((access.isNotBlank() && secret.isNotBlank()) || (existing != null && access.isBlank() && secret.isBlank()))) { Text(localizedText(R.string.storage_save)) }
        TextButton(onClick = onClose, enabled = !busy) { Text(localizedText(R.string.storage_back)) }
    }
}
