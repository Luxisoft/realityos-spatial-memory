package com.luxisoft.realityos

import android.content.Context
import android.content.ContextWrapper
import android.provider.Settings
import com.facebook.FacebookCallback
import com.facebook.FacebookException
import com.facebook.login.LoginManager
import com.facebook.login.LoginResult
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

internal fun androidDeviceId(context: Context): String =
    Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID).orEmpty().ifBlank { "unknown" }

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
