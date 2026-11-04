package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** A connection failure cannot turn a saved session into a logout or an admitted account. */
@Composable
internal fun RestoredAccountSession(
    local: Boolean,
    onConfirmed: () -> Unit,
    request: suspend (String) -> String = { path -> withContext(Dispatchers.IO) { SocialSession.request(path) } }
) {
    val identity = SocialSession.identity
    var retry by remember(identity) { mutableIntStateOf(0) }
    var failed by remember(identity) { mutableStateOf(false) }
    LaunchedEffect(identity, retry, local) {
        failed = false
        try {
            val response = JSONObject(request(if (local) "auth/local-session" else "auth/account-session"))
            SocialSession.requireCurrent(identity)
            check(response.optBoolean(if (local) "local_access" else "password_account"))
            onConfirmed()
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            if (SocialSession.isCurrent(identity)) failed = true
        }
    }
    Surface(Modifier.fillMaxSize()) {
        Box(Modifier.fillMaxSize().safeDrawingPadding(), contentAlignment = Alignment.Center) {
            Column(
                Modifier.widthIn(max = 528.dp).verticalScroll(rememberScrollState()).padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                if (!failed) {
                    CircularProgressIndicator(Modifier.testTag("session-restoring"))
                    Text(localizedText(R.string.session_restoring), style = MaterialTheme.typography.bodyLarge)
                } else {
                    Text(localizedText(R.string.session_restore_failed), style = MaterialTheme.typography.titleLarge)
                    Text(localizedText(R.string.session_restore_retry_hint), style = MaterialTheme.typography.bodyLarge)
                    Button(onClick = { retry++ }, shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp).testTag("session-restore-retry")) {
                        Text(localizedText(R.string.session_restore_retry))
                    }
                    TextButton(onClick = { SocialSession.clearIfCurrent(identity) }, modifier = Modifier.heightIn(min = 48.dp).testTag("session-restore-signout")) {
                        Text(localizedText(R.string.ui_sign_out))
                    }
                }
            }
        }
    }
}
