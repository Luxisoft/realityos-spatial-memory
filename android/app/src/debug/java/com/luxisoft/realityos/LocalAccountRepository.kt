package com.luxisoft.realityos

import com.luxisoft.realityos.data.JsonApi
import com.luxisoft.realityos.data.SessionCredentials
import com.luxisoft.realityos.data.SessionJsonApi
import com.luxisoft.realityos.data.get
import com.luxisoft.realityos.data.post
import org.json.JSONObject

internal data class LocalAccount(
    val id: String,
    val username: String,
    val displayName: String,
    val workspaceId: String,
    val workspaceName: String,
    val pictureUrl: String? = null
)

internal data class LocalAccountSelection(
    val credentials: SessionCredentials,
    val captureProfile: DeviceProvisioning
)

/** A database-backed account list, available only in the Debug source set. */
internal class LocalAccountRepository(private val api: JsonApi = SessionJsonApi()) {
    suspend fun accounts(): List<LocalAccount> {
        val response = JSONObject(api.get("auth/local-accounts"))
        check(response.optBoolean("local_access"))
        val rows = response.getJSONArray("accounts")
        return List(rows.length()) { index ->
            val row = rows.getJSONObject(index)
            LocalAccount(
                row.getString("id"),
                row.getString("username"),
                row.getString("display_name"),
                row.getString("workspace_id"),
                row.getString("workspace_name"),
                row.optText("picture_url")
            )
        }.also { check(it.isNotEmpty()) }
    }

    suspend fun select(account: LocalAccount): LocalAccountSelection {
        val response = JSONObject(api.post("auth/local-select", JSONObject().put("user_id", account.id)))
        check(response.optBoolean("local_access"))
        val profile = response.getJSONObject("capture_profile")
        check(profile.getString("workspace_id") == account.workspaceId)
        return LocalAccountSelection(
            SessionCredentials(response.getString("access_token"), response.getString("refresh_token"), localAccess = true),
            DeviceProvisioning(
                BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
                profile.getString("workspace_id"),
                profile.getString("device_id"),
                profile.getString("device_key"),
                profile.getString("workspace_name")
            )
        )
    }
}
