package com.luxisoft.realityos

import com.luxisoft.realityos.data.JsonApi
import com.luxisoft.realityos.data.SessionCredentials
import com.luxisoft.realityos.data.SessionJsonApi
import com.luxisoft.realityos.data.get
import com.luxisoft.realityos.data.post
import org.json.JSONObject

internal data class AccountLogin(val credentials: SessionCredentials, val captureProfile: DeviceProvisioning)

internal class AccountRepository(
    private val identity: Long = SocialSession.identity,
    private val api: JsonApi = SessionJsonApi(identity)
) {
    suspend fun submit(mode: String, payload: JSONObject): AccountLogin? {
        val response = JSONObject(api.post("auth/$mode", payload))
        if (mode != "login") return null
        SocialSession.requireCurrent(identity)
        SocialSession.token = response.getString("access_token")
        check(confirm(local = false))
        val profile = JSONObject(api.post("auth/account-capture-profile"))
        SocialSession.requireCurrent(identity)
        return AccountLogin(
            SessionCredentials(response.getString("access_token"), response.getString("refresh_token"), passwordAccount = true),
            DeviceProvisioning(
                BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
                profile.getString("workspace_id"),
                profile.getString("device_id"),
                profile.getString("device_key"),
                profile.getString("workspace_name")
            )
        )
    }

    suspend fun confirm(local: Boolean): Boolean {
        val result = JSONObject(api.get(if (local) "auth/local-session" else "auth/account-session"))
        return result.optBoolean(if (local) "local_access" else "password_account")
    }
}
