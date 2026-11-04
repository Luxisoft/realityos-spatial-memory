package com.luxisoft.realityos

import androidx.compose.runtime.Composable
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

@Composable
internal fun AccountEntry(viewModel: RealityViewModel, onSuccess: () -> Unit, onBack: () -> Unit) {
    AccountForm(onBack = onBack) { mode, payload ->
        var identity = SocialSession.identity
        try {
            val result = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("auth/$mode", payload)) }
            if (mode == "login") {
                SocialSession.requireCurrent(identity)
                SocialSession.token = result.getString("access_token")
                val profile = withContext(Dispatchers.IO) {
                    check(JSONObject(SocialSession.request("auth/account-session")).optBoolean("password_account"))
                    JSONObject(SocialSession.request("auth/account-capture-profile", JSONObject()))
                }
                SocialSession.requireCurrent(identity)
                SocialSession.workspaceId = profile.getString("workspace_id")
                SocialSession.remember(result.put("password_account", true))
                identity = SocialSession.identity
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
        } catch (cancelled: CancellationException) {
            if (mode == "login" && !SocialSession.active) SocialSession.clearIfCurrent(identity)
            throw cancelled
        } catch (error: Exception) {
            if (mode == "login") SocialSession.clearIfCurrent(identity)
            throw error
        }
    }
}

internal object AccountRequestLanguage {
    var value: String = "en"
}
