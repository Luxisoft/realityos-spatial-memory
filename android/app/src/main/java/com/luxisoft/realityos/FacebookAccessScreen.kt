package com.luxisoft.realityos

import android.content.Context
import android.content.ContextWrapper
import android.provider.Settings
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.facebook.FacebookCallback
import com.facebook.FacebookException
import com.facebook.login.LoginManager
import com.facebook.login.LoginResult
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Reuses the existing welcome composition, type scale and memory illustration. */
@Composable
internal fun FacebookAccessScreen(busy: Boolean, error: String, consentChecked: Boolean, onConsentChange: (Boolean) -> Unit, onLogin: () -> Unit, onGuest: () -> Unit, onWelcome: () -> Unit) {
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().safeDrawingPadding().padding(horizontal = 24.dp, vertical = 14.dp),
            horizontalAlignment = Alignment.CenterHorizontally) {
            Row(Modifier.fillMaxWidth().widthIn(max = 560.dp), verticalAlignment = Alignment.CenterVertically) {
                Image(painterResource(R.drawable.luxisoft_favicon_v9), contentDescription = stringResource(R.string.content_luxisoft_mark), modifier = Modifier.size(34.dp))
                Spacer(Modifier.width(10.dp))
                Column {
                    Text("RealityOS", style = MaterialTheme.typography.titleMedium)
                    Text(stringResource(R.string.about_developed_by), style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            Column(Modifier.weight(1f).widthIn(max = 560.dp).verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.Center) {
                MemoryTrace(pageIndex = 2)
                Spacer(Modifier.height(30.dp))
                Text(stringResource(R.string.brand_spatial_memory), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.tertiary)
                Spacer(Modifier.height(12.dp))
                Text(stringResource(R.string.facebook_access_title), style = MaterialTheme.typography.displaySmall)
                Spacer(Modifier.height(12.dp))
                if (error.isNotBlank()) {
                    Spacer(Modifier.height(20.dp))
                    Surface(shape = MaterialTheme.shapes.medium, color = MaterialTheme.colorScheme.errorContainer) {
                        Text(error, Modifier.padding(16.dp), color = MaterialTheme.colorScheme.onErrorContainer,
                            style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
            Row(Modifier.fillMaxWidth().widthIn(max = 560.dp), verticalAlignment = Alignment.CenterVertically) {
                Checkbox(checked = consentChecked, onCheckedChange = onConsentChange, enabled = !busy)
                Text(stringResource(R.string.facebook_consent_entry), style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(start = 4.dp))
            }
            Spacer(Modifier.height(10.dp))
            Button(onClick = onLogin, enabled = !busy && consentChecked, modifier = Modifier.fillMaxWidth().widthIn(max = 560.dp).heightIn(min = 56.dp)) {
                if (busy) {
                    CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp)
                    Spacer(Modifier.width(12.dp))
                }
                Icon(painterResource(R.drawable.ic_meta), contentDescription = "Meta", modifier = Modifier.size(24.dp))
                Spacer(Modifier.width(8.dp))
                Text(stringResource(if (busy) R.string.facebook_access_connecting else R.string.facebook_access_continue))
            }
            Spacer(Modifier.height(10.dp))
            OutlinedButton(onClick = onGuest, enabled = !busy, modifier = Modifier.fillMaxWidth().widthIn(max = 560.dp).heightIn(min = 56.dp)) {
                Text(stringResource(R.string.account_access))
            }
            Spacer(Modifier.height(10.dp))
            TextButton(onClick = onWelcome, enabled = !busy) { Text(stringResource(R.string.facebook_access_welcome)) }
        }
    }
}

internal fun androidDeviceId(context: Context): String =
    Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID).orEmpty().ifBlank { "unknown" }

internal fun startGuestAccess(context: Context, scope: CoroutineScope, viewModel: RealityViewModel,
                              onBusy: (Boolean) -> Unit, onError: (String) -> Unit, onSuccess: () -> Unit) {
    onError(""); onBusy(true)
    scope.launch {
        try {
            val response = withContext(Dispatchers.IO) {
                JSONObject(SocialSession.request("auth/guest", JSONObject().put("device_id", androidDeviceId(context))))
            }
            SocialSession.token = response.getString("access_token")
            val profile = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("me/capture-profile", JSONObject())) }
            SocialSession.workspaceId = profile.getString("workspace_id")
            viewModel.useFacebookCaptureProfile(DeviceProvisioning(BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
                profile.getString("workspace_id"), profile.getString("device_id"), profile.getString("device_key"), "Casa"))
            SocialSession.remember(response)
            onSuccess()
            SocialSession.active = true
        } catch (cancelled: kotlinx.coroutines.CancellationException) { throw cancelled }
        catch (error: Exception) {
            SocialSession.clear()
            onError(context.getString(R.string.facebook_access_failed))
        } finally { onBusy(false) }
    }
}

internal fun startFacebookAccess(context: Context, scope: CoroutineScope, viewModel: RealityViewModel,
                                 onBusy: (Boolean) -> Unit, onError: (String) -> Unit, onSuccess: () -> Unit) {
    var base = context
    while (base is ContextWrapper && base !is MainActivity) base = base.baseContext
    val activity = base as? MainActivity
    if (activity == null || BuildConfig.FACEBOOK_APP_ID == "0") {
        onError(context.getString(R.string.facebook_access_unavailable)); return
    }
    onError(""); onBusy(true)
    val manager = LoginManager.getInstance()
    if (com.facebook.AccessToken.getCurrentAccessToken()?.applicationId?.let { it != BuildConfig.FACEBOOK_APP_ID } == true) {
        manager.logOut()
    }
    manager.registerCallback(activity.facebookCallbacks, object : FacebookCallback<LoginResult> {
        override fun onSuccess(result: LoginResult) {
            scope.launch {
                try {
                    val response = withContext(Dispatchers.IO) {
                        JSONObject(SocialSession.request("auth/facebook", JSONObject().put("access_token", result.accessToken.token).put("device_id", androidDeviceId(context))))
                    }
                    SocialSession.token = response.getString("access_token")
                    val profile = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("me/capture-profile", JSONObject())) }
                    SocialSession.workspaceId = profile.getString("workspace_id")
                    viewModel.useFacebookCaptureProfile(DeviceProvisioning(BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
                        profile.getString("workspace_id"), profile.getString("device_id"), profile.getString("device_key"), "Casa"))
                    SocialSession.remember(response)
                    onSuccess()
                    SocialSession.active = true
                } catch (cancelled: kotlinx.coroutines.CancellationException) { throw cancelled }
                catch (error: Exception) {
                    SocialSession.clear()
                    onError(context.getString(R.string.facebook_access_failed))
                } finally { onBusy(false) }
            }
        }
        override fun onCancel() { onBusy(false); onError("") }
        override fun onError(error: FacebookException) {
            onBusy(false)
            onError(context.getString(if (error.message.orEmpty().contains("hash", ignoreCase = true)) R.string.facebook_access_hash_error else R.string.facebook_access_failed))
        }
    })
    // Standard Facebook Login; identity is the app-scoped Facebook ID.
    // Scopes must stay aligned with the Meta app dashboard. Optional scopes may
    // be declined; the backend only requires a valid app-scoped identity.
    try { manager.logInWithReadPermissions(activity, listOf("public_profile", "email", "user_age_range", "user_birthday", "user_friends", "user_gender", "user_hometown", "user_likes", "user_link", "user_location", "user_photos", "user_posts", "user_videos")) }
    catch (error: Exception) { onBusy(false); onError(context.getString(R.string.facebook_access_failed)) }
}
