package com.luxisoft.realityos

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

@Composable
internal fun AccountBiometricGate(content: @Composable () -> Unit) {
    if (!SocialSession.passwordAccount || SocialSession.localEntryAllowed) {
        content()
        return
    }
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var status by remember(SocialSession.token) { mutableStateOf<JSONObject?>(null) }
    var busy by remember { mutableStateOf(false) }
    var failed by remember { mutableStateOf(false) }
    var progress by remember { mutableStateOf("") }
    var resetReferences by remember { mutableStateOf(false) }
    val session = SocialSession.token
    suspend fun refresh() {
        val response = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("faces/setup")) }
        if (SocialSession.token == session) status = response
    }
    fun operation(action: suspend () -> Unit) {
        scope.launch {
            busy = true
            failed = false
            try {
                action()
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: Exception) {
                failed = true
                AppNotices.show(error.message.orEmpty(), NoticeKind.ERROR)
            } finally {
                busy = false
                progress = ""
            }
        }
    }
    LaunchedEffect(session) { operation { refresh() } }
    val profilePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            operation {
                withContext(Dispatchers.IO) {
                    val raw = context.contentResolver.openInputStream(uri)?.use { it.readBytes() } ?: error(localizedText(R.string.face_unreadable))
                    val mime = context.contentResolver.getType(uri) ?: "image/jpeg"
                    SocialSession.requestMultipart("faces/profile-photo", emptyMap(), raw, "profile-photo", mime)
                    SocialSession.requestMultipart("me/profile/avatar", emptyMap(), raw, "avatar", mime)
                }
                refresh()
            }
        }
    }
    val referencePicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
        if (uris.isNotEmpty()) {
            operation {
                val remaining = (25 - (status?.optInt("accepted_photos") ?: 0)).coerceAtLeast(0)
                for ((index, uri) in uris.take(remaining).withIndex()) {
                    progress = "${index + 1} / ${uris.size.coerceAtMost(remaining)}"
                    try {
                        withContext(Dispatchers.IO) {
                            val raw = context.contentResolver.openInputStream(uri)?.use { it.readBytes() } ?: error(localizedText(R.string.face_unreadable))
                            SocialSession.requestMultipart("faces/reference-photos", emptyMap(), raw, "reference-photo", context.contentResolver.getType(uri) ?: "image/jpeg")
                        }
                    } catch (cancelled: CancellationException) {
                        throw cancelled
                    } catch (error: Exception) {
                        AppNotices.show("${index + 1}: ${error.message.orEmpty()}", NoticeKind.ERROR)
                    }
                    refresh()
                }
            }
        }
    }
    if (status?.optBoolean("complete") == true) {
        content()
        return
    }
    AccountBiometricSetupScreen(
        status = status,
        busy = busy,
        failed = failed,
        progress = progress,
        onRetry = { operation { refresh() } },
        onConsent = {
            operation {
                withContext(Dispatchers.IO) { SocialSession.request("faces/consent", JSONObject().put("confirm", true)) }
                refresh()
            }
        },
        onProfile = { profilePicker.launch("image/*") },
        onReferences = { referencePicker.launch(arrayOf("image/jpeg", "image/png", "image/webp")) },
        onResetReferences = { resetReferences = true },
        onComplete = {
            operation {
                withContext(Dispatchers.IO) { SocialSession.request("faces/setup/complete", JSONObject()) }
                refresh()
            }
        },
        onSignOut = { SocialSession.clear() }
    )
    if (resetReferences) {
        AlertDialog(
            onDismissRequest = { resetReferences = false },
            title = { Text(localizedText(R.string.biometric_reset_references)) },
            text = { Text(localizedText(R.string.biometric_reset_body)) },
            confirmButton = {
                TextButton(onClick = {
                    resetReferences = false
                    operation {
                        val ids = status?.optJSONArray("reference_ids")
                        withContext(Dispatchers.IO) {
                            if (ids != null) {
                                for (index in 0 until ids.length()) {
                                    SocialSession.requestJson("faces/reference-photos/${ids.getString(index)}", "DELETE")
                                }
                            }
                        }
                        refresh()
                    }
                }) { Text(localizedText(R.string.biometric_reset_references)) }
            },
            dismissButton = { TextButton(onClick = { resetReferences = false }) { Text(localizedText(R.string.ui_cancel)) } }
        )
    }
}
