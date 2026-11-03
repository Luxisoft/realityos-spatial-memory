package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Production password authentication; server-confirmed and separate from local Debug access. */
@Composable
internal fun AccountEntry(viewModel: RealityViewModel, onSuccess: () -> Unit, onBack: () -> Unit) {
    var mode by remember { mutableStateOf("register") }
    var email by remember { mutableStateOf("") }
    var username by remember { mutableStateOf("") }
    var name by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    Column(Modifier.fillMaxSize().safeDrawingPadding().padding(24.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("RealityOS", style = MaterialTheme.typography.titleLarge)
        Text(stringResource(if (mode == "register") R.string.account_register else if (mode == "login") R.string.account_login else R.string.account_recover), style = MaterialTheme.typography.headlineMedium)
        if (mode == "register") {
            OutlinedTextField(name, { name = it }, Modifier.fillMaxWidth(), enabled = !busy, singleLine = true, label = { Text(stringResource(R.string.account_name)) })
            OutlinedTextField(username, { username = it }, Modifier.fillMaxWidth(), enabled = !busy, singleLine = true, label = { Text(stringResource(R.string.account_username)) })
        }
        OutlinedTextField(email, { email = it }, Modifier.fillMaxWidth(), enabled = !busy, singleLine = true, label = { Text(stringResource(if (mode == "login") R.string.account_identifier else R.string.local_account_email)) })
        if (mode == "login" || mode == "register") {
            OutlinedTextField(password, { password = it }, Modifier.fillMaxWidth(), enabled = !busy, singleLine = true, visualTransformation = PasswordVisualTransformation(), label = { Text(stringResource(R.string.local_account_password)) }, supportingText = { if (mode == "register") Text(stringResource(R.string.account_password_hint)) })
        }
        if (message.isNotEmpty()) Text(message, style = MaterialTheme.typography.bodyMedium)
        Button(enabled = !busy && email.isNotBlank() && (mode !in listOf("login", "register") || password.length >= if (mode == "register") 12 else 1) && (mode != "register" || (username.isNotBlank() && name.isNotBlank())), onClick = {
            busy = true; message = ""
            scope.launch {
                try {
                    val payload = JSONObject().put("email", email.trim())
                    if (mode in listOf("register", "login")) payload.put("password", password)
                    if (mode == "register") payload.put("username", username.trim()).put("display_name", name.trim())
                    val result = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("auth/$mode", payload)) }
                    if (mode == "login") {
                        SocialSession.token = result.getString("access_token")
                        val profile = withContext(Dispatchers.IO) {
                            check(JSONObject(SocialSession.request("auth/account-session")).optBoolean("password_account"))
                            JSONObject(SocialSession.request("auth/account-capture-profile", JSONObject()))
                        }
                        SocialSession.workspaceId = profile.getString("workspace_id")
                        SocialSession.remember(result.put("password_account", true))
                        viewModel.useFacebookCaptureProfile(DeviceProvisioning(BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
                            profile.getString("workspace_id"), profile.getString("device_id"), profile.getString("device_key"), profile.getString("workspace_name")))
                        password = ""
                        onSuccess()
                        SocialSession.active = true
                    } else {
                        message = localizedText(R.string.account_email_sent)
                        password = ""
                    }
                } catch (cancelled: CancellationException) { throw cancelled }
                catch (_: Exception) {
                    if (mode == "login") SocialSession.clear()
                    message = localizedText(R.string.account_failed)
                } finally { busy = false }
            }
        }, modifier = Modifier.fillMaxWidth()) {
            if (busy) CircularProgressIndicator(Modifier.size(20.dp)) else Text(stringResource(if (mode == "login") R.string.account_login else if (mode == "register") R.string.account_register else R.string.account_send))
        }
        TextButton(enabled = !busy, onClick = { mode = if (mode == "register") "login" else "register"; message = "" }) { Text(stringResource(if (mode == "register") R.string.account_login else R.string.account_register)) }
        TextButton(enabled = !busy, onClick = { mode = "forgot-password"; message = "" }) { Text(stringResource(R.string.account_recover)) }
        TextButton(enabled = !busy, onClick = { mode = "resend-confirmation"; message = "" }) { Text(stringResource(R.string.account_resend)) }
        TextButton(enabled = !busy, onClick = onBack) { Text(stringResource(R.string.account_back)) }
    }
}
