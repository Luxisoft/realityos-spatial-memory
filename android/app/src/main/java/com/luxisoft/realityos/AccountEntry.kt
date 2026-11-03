package com.luxisoft.realityos

import androidx.compose.runtime.Composable
import kotlinx.coroutines.Dispatchers
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

internal object AccountRequestLanguage {
    var value: String = "en"
}
