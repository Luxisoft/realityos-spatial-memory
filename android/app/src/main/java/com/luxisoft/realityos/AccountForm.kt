package com.luxisoft.realityos

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.ArrowForward
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.platform.*
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import org.json.JSONObject

internal enum class AccountStep(val endpoint: String, val title: Int, val description: Int, val action: Int) {
    Login("login", R.string.account_login, R.string.account_login_description, R.string.account_login),
    Register("register", R.string.account_register_title, R.string.account_register_description, R.string.account_register),
    Recover("forgot-password", R.string.account_recover_title, R.string.account_recover_description, R.string.account_send_link),
    Resend("resend-confirmation", R.string.account_confirm_title, R.string.account_resend_description, R.string.account_resend),
    CorrectEmail("change-pending-email", R.string.account_correct_title, R.string.account_correct_description, R.string.account_correct_submit)
}

@Composable
internal fun AccountForm(onBack: () -> Unit, submit: suspend (String, JSONObject) -> Unit) {
    var step by rememberSaveable { mutableStateOf(AccountStep.Login) }
    var email by rememberSaveable { mutableStateOf("") }
    var username by rememberSaveable { mutableStateOf("") }
    var existingIdentifier by rememberSaveable { mutableStateOf("") }
    var confirmationIdentifier by rememberSaveable { mutableStateOf("") }
    var name by rememberSaveable { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var sent by rememberSaveable { mutableStateOf(false) }
    var failure by remember { mutableStateOf<Int?>(null) }
    var sentAgain by remember { mutableStateOf(false) }
    var attempted by remember { mutableStateOf(false) }
    var conflicts by remember { mutableStateOf(emptySet<String>()) }
    val touched = remember(step, sent) { mutableStateMapOf<String, Boolean>() }
    val focus = remember { listOf("name", "username", "identifier", "email", "password").associateWith { FocusRequester() } }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val focusManager = LocalFocusManager.current
    val keyboard = LocalSoftwareKeyboardController.current
    val autofill = LocalAutofillManager.current
    val scroll = rememberScrollState()
    val keyboardOpen = WindowInsets.ime.getBottom(LocalDensity.current) > 0
    fun navigate(next: AccountStep, identifier: String? = null) {
        autofill?.cancel()
        focusManager.clearFocus()
        if (next == AccountStep.CorrectEmail) {
            existingIdentifier = identifier ?: if (sent) confirmationIdentifier else email.trim()
        }
        step = next
        password = ""
        sent = false
        failure = null
        attempted = false
        sentAgain = false
        conflicts = emptySet()
        scope.launch { scroll.scrollTo(0) }
    }
    fun back() {
        if (step == AccountStep.Login) onBack() else navigate(AccountStep.Login)
    }
    BackHandler { if (!busy) back() }
    val fields = when (step) {
        AccountStep.Register -> listOf("name", "username", "email", "password")
        AccountStep.CorrectEmail -> listOf("identifier", "email", "password")
        AccountStep.Login -> listOf("email", "password")
        else -> listOf("email")
    }
    fun errorFor(field: String): Int? = if (field in conflicts) {
        if (field == "email") R.string.account_email_in_use else R.string.account_username_in_use
    } else {
        when (field) {
            "name" -> if (name.trim().length !in 1..160) R.string.account_name_error else null
            "username" -> if (!username.trim().matches(Regex("[a-zA-Z][a-zA-Z0-9_.-]{2,63}"))) R.string.account_username_hint else null
            "identifier" -> if (existingIdentifier.trim().length !in 3..320) R.string.account_existing_identifier_error else null
            "email" -> if (email.isBlank() || email.trim().length > 320 || (step != AccountStep.Login && !android.util.Patterns.EMAIL_ADDRESS.matcher(email.trim()).matches())) {
                if (step == AccountStep.Login) R.string.account_identifier_error else R.string.account_email_error
            } else {
                null
            }
            else -> if (password.length !in (if (step == AccountStep.Register) 12 else 1)..512) {
                if (step == AccountStep.Register) R.string.account_password_hint else R.string.account_password_error
            } else {
                null
            }
        }
    }
    fun send() {
        if (busy) return
        attempted = true
        fields.firstOrNull { errorFor(it) != null }?.let {
            focus.getValue(it).requestFocus()
            return
        }
        keyboard?.hide()
        focusManager.clearFocus()
        busy = true
        failure = null
        val action = step
        val payload = JSONObject().put("email", email.trim())
        if (action == AccountStep.Login || action == AccountStep.Register || action == AccountStep.CorrectEmail) payload.put("password", password)
        if (action == AccountStep.Register) payload.put("username", username.trim()).put("display_name", name.trim())
        if (action == AccountStep.CorrectEmail) payload.put("username", existingIdentifier.trim())
        AccountRequestLanguage.value = RealityExperienceStore(context).selectedLanguage().languageTag
        scope.launch {
            try {
                submit(action.endpoint, payload)
                if (action == AccountStep.Register) autofill?.commit()
                confirmationIdentifier = when (action) {
                    AccountStep.Register -> username.trim()
                    AccountStep.CorrectEmail -> if ('@' in existingIdentifier) email.trim() else existingIdentifier.trim()
                    else -> email.trim()
                }
                password = ""
                sent = action != AccountStep.Login
                scroll.animateScrollTo(0)
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (conflict: AccountConflict) {
                conflicts = conflict.fields
            } catch (error: AccountFailure) {
                failure = error.messageResource
            } catch (_: java.io.IOException) {
                failure = R.string.account_network_error
            } catch (_: Exception) {
                failure = R.string.account_service_unavailable
            } finally {
                busy = false
            }
        }
    }
    fun resend() {
        if (busy) return
        busy = true
        failure = null
        AccountRequestLanguage.value = RealityExperienceStore(context).selectedLanguage().languageTag
        val action = if (step == AccountStep.Register || step == AccountStep.CorrectEmail) AccountStep.Resend else step
        scope.launch {
            try {
                submit(action.endpoint, JSONObject().put("email", email.trim()))
                sentAgain = true
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: AccountFailure) {
                failure = error.messageResource
            } catch (_: java.io.IOException) {
                failure = R.string.account_network_error
            } catch (_: Exception) {
                failure = R.string.account_service_unavailable
            } finally {
                busy = false
            }
        }
    }
    Surface(Modifier.fillMaxSize().testTag("account-screen"), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().safeDrawingPadding().imePadding(), horizontalAlignment = Alignment.CenterHorizontally) {
            Row(Modifier.widthIn(max = 528.dp).fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = { back() }, enabled = !busy, modifier = Modifier.testTag("account-back")) {
                    Icon(Icons.AutoMirrored.Outlined.ArrowBack, stringResource(R.string.account_back), tint = MaterialTheme.colorScheme.onSurface)
                }
                Spacer(Modifier.width(4.dp))
                Image(painterResource(R.drawable.luxisoft_favicon_v9), null, Modifier.size(26.dp))
                Spacer(Modifier.width(9.dp))
                Text("RealityOS", style = MaterialTheme.typography.titleMedium)
            }
            Column(Modifier.weight(1f).widthIn(max = 528.dp).fillMaxWidth().verticalScroll(scroll).padding(horizontal = 24.dp).padding(bottom = 24.dp)) {
                AnimatedContent(targetState = Triple(step, sent, keyboardOpen), transitionSpec = { fadeIn(tween(180)) togetherWith fadeOut(tween(100)) }, label = "account-art") { (artStep, isSent, ime) ->
                    if (!ime) {
                        AccountArtwork(artStep, isSent, compact = (artStep == AccountStep.Register || artStep == AccountStep.CorrectEmail) && !isSent)
                    } else {
                        Spacer(Modifier.height(4.dp))
                    }
                }
                Spacer(Modifier.height(16.dp))
                Text(stringResource(if (sent) R.string.account_check_inbox else step.title), style = MaterialTheme.typography.headlineMedium, modifier = Modifier.testTag("account-title"))
                Spacer(Modifier.height(8.dp))
                Text(stringResource(if (sent) R.string.account_sent_description else step.description), style = MaterialTheme.typography.bodyMedium, color = AccountMuted)
                Spacer(Modifier.height(24.dp))
                if (sent) {
                    Surface(color = AccountFieldSurface, shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth()) {
                        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Outlined.AlternateEmail, null, tint = AccountBlue)
                            Spacer(Modifier.width(12.dp))
                            Text(email.trim(), style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f).testTag("account-recipient"))
                        }
                    }
                    Spacer(Modifier.height(16.dp))
                    Row(Modifier.semantics { liveRegion = LiveRegionMode.Polite }.testTag("account-message")) {
                        Icon(Icons.Outlined.Info, null, Modifier.size(18.dp), tint = AccountMuted)
                        Spacer(Modifier.width(8.dp))
                        Text(stringResource(R.string.account_inbox_hint), style = MaterialTheme.typography.bodySmall, color = AccountMuted)
                    }
                    if (failure != null || sentAgain) {
                        Spacer(Modifier.height(12.dp))
                        Text(
                            stringResource(failure ?: R.string.account_resent_notice),
                            color = if (failure != null) MaterialTheme.colorScheme.error else AccountBlue,
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite }.testTag("account-resend-status")
                        )
                    }
                    Spacer(Modifier.height(28.dp))
                    AccountPrimary(R.string.account_back_login, busy, onClick = { navigate(AccountStep.Login) })
                    TextButton(onClick = { navigate(if (step == AccountStep.Recover) AccountStep.Recover else AccountStep.CorrectEmail) }, enabled = !busy, modifier = Modifier.align(Alignment.CenterHorizontally).testTag("account-edit-email")) {
                        Text(stringResource(if (step == AccountStep.Recover) R.string.account_use_another_email else R.string.account_edit_email))
                    }
                    TextButton(onClick = { resend() }, enabled = !busy, modifier = Modifier.align(Alignment.CenterHorizontally).testTag("account-send-again")) {
                        Icon(Icons.Outlined.Refresh, null, Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(stringResource(R.string.account_send_again))
                    }
                } else {
                    key(step) {
                        fields.forEachIndexed { index, field ->
                            AccountField(
                                field,
                                when (field) {
                                    "name" -> name
                                    "username" -> username
                                    "identifier" -> existingIdentifier
                                    "email" -> email
                                    else -> password
                                },
                                onValue = {
                                    conflicts = conflicts - field
                                    failure = null
                                    when (field) {
                                        "name" -> name = it
                                        "username" -> username = it
                                        "identifier" -> existingIdentifier = it
                                        "email" -> email = it
                                        else -> password = it
                                    }
                                },
                                step = step, enabled = !busy, error = if (attempted || touched[field] == true) errorFor(field) else null,
                                focus = focus.getValue(field), onBlur = { touched[field] = true }, last = index == fields.lastIndex, onSubmit = { send() }
                            )
                            if (index != fields.lastIndex) Spacer(Modifier.height(12.dp))
                        }
                    }
                    if (step == AccountStep.Login || step == AccountStep.CorrectEmail) {
                        TextButton(onClick = {
                            if (step == AccountStep.CorrectEmail) email = existingIdentifier.takeIf { '@' in it }.orEmpty()
                            navigate(AccountStep.Recover)
                        }, enabled = !busy, modifier = Modifier.align(Alignment.End).testTag("account-recover")) { Text(stringResource(R.string.account_forgot)) }
                    } else {
                        Spacer(Modifier.height(20.dp))
                    }
                    if (failure != null) {
                        Surface(color = MaterialTheme.colorScheme.errorContainer, shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth().testTag("account-message").semantics { liveRegion = LiveRegionMode.Polite }) {
                            Row(Modifier.padding(14.dp)) {
                                Icon(Icons.Outlined.ErrorOutline, null, Modifier.size(20.dp), tint = MaterialTheme.colorScheme.error)
                                Spacer(Modifier.width(10.dp))
                                Text(stringResource(failure!!), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.error)
                            }
                        }
                        Spacer(Modifier.height(16.dp))
                    }
                    if (conflicts.isNotEmpty()) {
                        Surface(
                            color = AccountFieldSurface,
                            shape = MaterialTheme.shapes.medium,
                            modifier = Modifier.fillMaxWidth().testTag("account-conflict").semantics { liveRegion = LiveRegionMode.Polite }
                        ) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                    Icon(Icons.Outlined.PersonOutline, null, tint = AccountBlue, modifier = Modifier.size(22.dp))
                                    Text(stringResource(R.string.account_conflict_title), style = MaterialTheme.typography.titleMedium)
                                }
                                Text(stringResource(R.string.account_conflict_description), style = MaterialTheme.typography.bodyMedium, color = AccountMuted)
                                if (step == AccountStep.Register) {
                                    TextButton(onClick = {
                                        navigate(AccountStep.CorrectEmail, if ("username" in conflicts) username.trim() else email.trim())
                                    }, modifier = Modifier.fillMaxWidth().testTag("account-conflict-correct")) {
                                        Text(stringResource(R.string.account_wrong_registration_email))
                                    }
                                }
                                TextButton(onClick = {
                                    if ("email" !in conflicts) email = ""
                                    navigate(AccountStep.Recover)
                                }, modifier = Modifier.fillMaxWidth().testTag("account-conflict-recover")) {
                                    Text(stringResource(R.string.account_recover_existing))
                                }
                                TextButton(onClick = {
                                    if ("email" !in conflicts) email = ""
                                    navigate(AccountStep.Resend)
                                }, modifier = Modifier.fillMaxWidth().testTag("account-conflict-resend")) {
                                    Text(stringResource(R.string.account_resend))
                                }
                                TextButton(onClick = {
                                    val field = fields.first { it in conflicts }
                                    conflicts.forEach {
                                        if (it == "email") {
                                            email = ""
                                        } else if (it == "username") {
                                            username = ""
                                        }
                                    }
                                    conflicts = emptySet()
                                    attempted = false
                                    focus.getValue(field).requestFocus()
                                }, modifier = Modifier.fillMaxWidth().testTag("account-conflict-edit")) {
                                    Text(stringResource(R.string.account_use_other_details))
                                }
                            }
                        }
                        Spacer(Modifier.height(16.dp))
                    }
                    AccountPrimary(step.action, busy, enabled = conflicts.isEmpty(), onClick = { send() })
                    Spacer(Modifier.height(20.dp))
                    if (step == AccountStep.Login) {
                        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                        Spacer(Modifier.height(14.dp))
                        Text(stringResource(R.string.account_new_here), style = MaterialTheme.typography.bodyMedium, color = AccountMuted, modifier = Modifier.fillMaxWidth(), textAlign = TextAlign.Center)
                        TextButton(onClick = { navigate(AccountStep.Register) }, enabled = !busy, modifier = Modifier.align(Alignment.CenterHorizontally).testTag("account-register")) { Text(stringResource(R.string.account_register)) }
                        Spacer(Modifier.height(8.dp))
                        TextButton(onClick = { navigate(AccountStep.Resend) }, enabled = !busy, modifier = Modifier.align(Alignment.CenterHorizontally).testTag("account-resend")) {
                            Icon(Icons.Outlined.MarkEmailUnread, null, Modifier.size(18.dp), tint = AccountMuted)
                            Spacer(Modifier.width(8.dp))
                            Text(stringResource(R.string.account_unconfirmed), style = MaterialTheme.typography.bodySmall, color = AccountMuted)
                        }
                    } else {
                        if (step == AccountStep.Resend) {
                            TextButton(onClick = { navigate(AccountStep.CorrectEmail) }, enabled = !busy, modifier = Modifier.align(Alignment.CenterHorizontally).testTag("account-correct-email")) {
                                Text(stringResource(R.string.account_wrong_registration_email))
                            }
                        }
                        TextButton(onClick = { navigate(AccountStep.Login) }, enabled = !busy, modifier = Modifier.align(Alignment.CenterHorizontally)) { Text(stringResource(R.string.account_back_login)) }
                    }
                }
            }
        }
    }
}

@Composable
private fun AccountPrimary(label: Int, busy: Boolean, enabled: Boolean = true, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        enabled = !busy && enabled,
        shape = MaterialTheme.shapes.medium,
        colors = ButtonDefaults.buttonColors(contentColor = androidx.compose.ui.graphics.Color(0xFF17211F)),
        modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp).testTag("account-submit"),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 16.dp)
    ) {
        if (busy) {
            CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp, color = AccountBlue)
        } else {
            Text(stringResource(label), style = MaterialTheme.typography.labelLarge, modifier = Modifier.weight(1f), textAlign = TextAlign.Center)
            Icon(Icons.AutoMirrored.Outlined.ArrowForward, null, Modifier.size(20.dp))
        }
    }
}
