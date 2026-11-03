package com.luxisoft.realityos

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

@Composable
internal fun AccountEntry(viewModel: RealityViewModel, onSuccess: () -> Unit, onBack: () -> Unit) {
    AccountForm(onBack = onBack) { mode, payload ->
        try {
            val result = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("auth/$mode", payload)) }
            if (mode == "login") {
                SocialSession.token = result.getString("access_token")
                val profile = withContext(Dispatchers.IO) {
                    check(JSONObject(SocialSession.request("auth/account-session")).optBoolean("password_account"))
                    JSONObject(SocialSession.request("auth/account-capture-profile", JSONObject()))
                }
                SocialSession.workspaceId = profile.getString("workspace_id")
                SocialSession.remember(result.put("password_account", true))
                viewModel.useFacebookCaptureProfile(
                    DeviceProvisioning(
                        BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
                        profile.getString("workspace_id"),
                        profile.getString("device_id"),
                        profile.getString("device_key"),
                        profile.getString("workspace_name")
                    )
                )
                SocialSession.active = true
                onSuccess()
            }
        } catch (error: Exception) {
            if (mode == "login") SocialSession.clear()
            throw error
        }
    }
}

/** UI independent of session provisioning so navigation and requests can be tested together. */
@Composable
internal fun AccountForm(onBack: () -> Unit, submit: suspend (String, JSONObject) -> Unit) {
    var mode by rememberSaveable { mutableStateOf("login") }
    var email by rememberSaveable { mutableStateOf("") }
    var username by rememberSaveable { mutableStateOf("") }
    var name by rememberSaveable { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var visible by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var sent by remember { mutableStateOf(false) }
    var failed by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    fun navigate(next: String) {
        mode = next
        password = ""
        visible = false
        sent = false
        failed = false
    }
    fun back() {
        if (mode == "login") onBack() else navigate("login")
    }
    BackHandler { if (!busy) back() }
    val title = when (mode) {
        "register" -> R.string.account_register
        "forgot-password" -> R.string.account_recover
        "resend-confirmation" -> R.string.account_resend
        else -> R.string.account_login
    }
    val needsPassword = mode == "login" || mode == "register"
    val valid = email.isNotBlank() && (mode == "login" || android.util.Patterns.EMAIL_ADDRESS.matcher(email.trim()).matches()) &&
        (!needsPassword || password.length in (if (mode == "register") 12 else 1)..512) &&
        (mode != "register" || (name.trim().length in 1..160 && username.trim().matches(Regex("[a-zA-Z][a-zA-Z0-9_.-]{2,63}"))))
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().safeDrawingPadding().imePadding().verticalScroll(rememberScrollState()).padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Column(Modifier.widthIn(max = 560.dp).fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text("RealityOS", style = MaterialTheme.typography.titleLarge)
                Text(stringResource(title), style = MaterialTheme.typography.headlineMedium, modifier = Modifier.testTag("account-title"))
                if (mode == "register" && !sent) {
                    OutlinedTextField(name, { name = it }, Modifier.fillMaxWidth(), enabled = !busy, singleLine = true, label = { Text(stringResource(R.string.account_name)) })
                    OutlinedTextField(username, { username = it }, Modifier.fillMaxWidth(), enabled = !busy, singleLine = true, label = { Text(stringResource(R.string.account_username)) })
                }
                if (!sent) {
                    OutlinedTextField(
                        email,
                        { email = it },
                        Modifier.fillMaxWidth().testTag("account-email"),
                        enabled = !busy,
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(keyboardType = if (mode == "login") KeyboardType.Text else KeyboardType.Email),
                        label = { Text(stringResource(if (mode == "login") R.string.account_identifier else R.string.local_account_email)) }
                    )
                    if (needsPassword) {
                        OutlinedTextField(
                            password, { password = it }, Modifier.fillMaxWidth().testTag("account-password"), enabled = !busy, singleLine = true,
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            visualTransformation = if (visible) VisualTransformation.None else PasswordVisualTransformation(),
                            trailingIcon = { TextButton(onClick = { visible = !visible }) { Text(stringResource(if (visible) R.string.account_hide_password else R.string.account_show_password)) } },
                            label = { Text(stringResource(R.string.local_account_password)) }, supportingText = { if (mode == "register") Text(stringResource(R.string.account_password_hint)) }
                        )
                    }
                }
                if (sent || failed) Text(stringResource(if (sent) R.string.account_email_sent else R.string.account_failed), color = if (failed) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface, modifier = Modifier.testTag("account-message"))
                if (!sent) {
                    Button(enabled = !busy && valid, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp).testTag("account-submit"), onClick = {
                        busy = true
                        failed = false
                        val action = mode
                        val payload = JSONObject().put("email", email.trim())
                        if (needsPassword) payload.put("password", password)
                        if (action == "register") payload.put("username", username.trim()).put("display_name", name.trim())
                        // Capture the selected language before moving the request to an IO thread.
                        AccountRequestLanguage.value = RealityExperienceStore(context).selectedLanguage().languageTag
                        scope.launch {
                            try {
                                submit(action, payload)
                                password = ""
                                sent = action != "login"
                            } catch (cancelled: CancellationException) {
                                throw cancelled
                            } catch (_: Exception) {
                                failed = true
                            } finally {
                                busy = false
                            }
                        }
                    }) {
                        if (busy) CircularProgressIndicator(Modifier.size(20.dp)) else Text(stringResource(if (needsPassword) title else R.string.account_send))
                    }
                }
                if (mode == "login") {
                    TextButton(enabled = !busy, onClick = { navigate("forgot-password") }) { Text(stringResource(R.string.account_forgot)) }
                    TextButton(enabled = !busy, onClick = { navigate("register") }) { Text(stringResource(R.string.account_signup_link)) }
                }
                if ((mode == "register" && sent) || mode == "login") {
                    TextButton(enabled = !busy, onClick = { navigate("resend-confirmation") }) { Text(stringResource(R.string.account_resend)) }
                }
                TextButton(enabled = !busy, onClick = { back() }) { Text(stringResource(if (mode == "login") R.string.account_back else R.string.account_back_login)) }
            }
        }
    }
}

internal object AccountRequestLanguage {
    var value: String = "en"
}
