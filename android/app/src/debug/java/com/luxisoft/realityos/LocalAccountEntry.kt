package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowForward
import androidx.compose.material.icons.outlined.PersonOutline
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Present only in Debug; the backend must independently confirm the local realm. */
@Composable
internal fun LocalAccountEntry(viewModel: RealityViewModel, onSuccess: () -> Unit): Boolean {
    if (!LocalAccessPolicy.canSkipFaceEntry(BuildConfig.DEBUG, BuildConfig.LOCAL_DEVELOPMENT, BuildConfig.DEFAULT_REALITYOS_API_BASE_URL, true)) return false
    var accounts by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var busy by remember { mutableStateOf(true) }
    var failed by remember { mutableStateOf(false) }
    var retry by remember { mutableIntStateOf(0) }
    val scope = rememberCoroutineScope()
    LaunchedEffect(retry) {
        busy = true
        failed = false
        try {
            val result = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("auth/local-accounts")) }
            check(result.optBoolean("local_access"))
            val rows = result.getJSONArray("accounts")
            accounts = (0 until rows.length()).map(rows::getJSONObject)
            check(accounts.isNotEmpty())
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            failed = true
        } finally {
            busy = false
        }
    }
    LocalAccountChooser(accounts, busy, failed, onRetry = { retry++ }, onSelect = { account ->
        busy = true
        failed = false
        scope.launch {
            var identity = SocialSession.identity
            try {
                val result = withContext(Dispatchers.IO) {
                    JSONObject(SocialSession.request("auth/local-select", JSONObject().put("user_id", account.getString("id"))))
                }
                SocialSession.requireCurrent(identity)
                check(result.optBoolean("local_access"))
                val profile = result.getJSONObject("capture_profile")
                SocialSession.workspaceId = profile.getString("workspace_id")
                SocialSession.remember(result)
                identity = SocialSession.identity
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
                SocialSession.freshLogin = false
                onSuccess()
                SocialSession.active = true
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                SocialSession.clearIfCurrent(identity)
                failed = true
            } finally {
                busy = false
            }
        }
    })
    return true
}

@Composable
internal fun LocalAccountChooser(accounts: List<JSONObject>, busy: Boolean, failed: Boolean, onRetry: () -> Unit, onSelect: (JSONObject) -> Unit) {
    Surface(Modifier.fillMaxSize().testTag("local-account-selector"), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().safeDrawingPadding(), horizontalAlignment = Alignment.CenterHorizontally) {
            Column(Modifier.widthIn(max = 528.dp).fillMaxSize()) {
                EntryBrandHeader()
                Column(
                    Modifier.fillMaxWidth().weight(1f).verticalScroll(rememberScrollState()).padding(24.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(stringResource(R.string.local_account_title), style = MaterialTheme.typography.headlineMedium)
                    Text(stringResource(R.string.local_account_body), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
                    if (failed) {
                        Text(stringResource(R.string.local_account_failed), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.error)
                        OutlinedButton(onClick = onRetry, enabled = !busy) { Text(stringResource(R.string.local_account_retry)) }
                    }
                    accounts.groupBy { it.getString("workspace_name") }.forEach { (group, members) ->
                        Text(group, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 12.dp))
                        members.forEach { account ->
                            OutlinedCard(
                                enabled = !busy,
                                modifier = Modifier.fillMaxWidth().testTag("local-account-${account.getString("username")}"),
                                shape = MaterialTheme.shapes.medium,
                                onClick = { onSelect(account) }
                            ) {
                                Row(Modifier.fillMaxWidth().padding(16.dp).heightIn(min = 32.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                    Icon(Icons.Outlined.PersonOutline, null, tint = AccountBlue)
                                    Text(account.getString("display_name"), style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                                    Icon(Icons.AutoMirrored.Outlined.ArrowForward, null, Modifier.size(20.dp))
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
