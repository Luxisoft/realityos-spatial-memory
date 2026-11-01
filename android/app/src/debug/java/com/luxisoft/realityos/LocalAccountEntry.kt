package com.luxisoft.realityos

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Absent from Release. Local account credentials never enter production builds. */
@Composable
internal fun LocalAccountEntry(viewModel: RealityViewModel, onSuccess: () -> Unit): Boolean {
    if (!LocalAccessPolicy.canSkipFaceEntry(BuildConfig.DEBUG, BuildConfig.LOCAL_DEVELOPMENT, BuildConfig.DEFAULT_REALITYOS_API_BASE_URL, true)) return false
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var failed by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    Surface(Modifier.fillMaxSize()) {
        Column(
            Modifier.fillMaxSize().padding(24.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Column(Modifier.widthIn(max = 480.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text(stringResource(R.string.local_account_title), style = MaterialTheme.typography.headlineMedium)
                Text(stringResource(R.string.local_account_body))
                OutlinedTextField(email, { email = it }, Modifier.fillMaxWidth(), enabled = !busy, singleLine = true, label = { Text(stringResource(R.string.local_account_email)) })
                OutlinedTextField(password, { password = it }, Modifier.fillMaxWidth(), enabled = !busy, singleLine = true, visualTransformation = PasswordVisualTransformation(), label = { Text(stringResource(R.string.local_account_password)) })
                if (failed) Text(stringResource(R.string.local_account_failed), color = MaterialTheme.colorScheme.error)
                Button(enabled = !busy && email.isNotBlank() && password.isNotBlank(), onClick = {
                    busy = true
                    failed = false
                    scope.launch {
                        try {
                            val result = withContext(Dispatchers.IO) {
                                JSONObject(SocialSession.request("auth/local-login", JSONObject().put("email", email.trim()).put("password", password)))
                            }
                            check(result.optBoolean("local_access"))
                            val profile = result.getJSONObject("capture_profile")
                            SocialSession.workspaceId = profile.getString("workspace_id")
                            SocialSession.remember(result)
                            check(SocialSession.localEntryAllowed)
                            viewModel.useFacebookCaptureProfile(
                                DeviceProvisioning(
                                    BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
                                    profile.getString("workspace_id"),
                                    profile.getString("device_id"),
                                    profile.getString("device_key"),
                                    profile.getString("workspace_name")
                                )
                            )
                            password = ""
                            SocialSession.freshLogin = false
                            onSuccess()
                            SocialSession.active = true
                        } catch (cancelled: CancellationException) {
                            throw cancelled
                        } catch (_: Exception) {
                            SocialSession.clear()
                            failed = true
                        } finally {
                            busy = false
                        }
                    }
                }) {
                    if (busy) CircularProgressIndicator() else Text(stringResource(R.string.local_account_enter))
                }
            }
        }
    }
    return true
}
