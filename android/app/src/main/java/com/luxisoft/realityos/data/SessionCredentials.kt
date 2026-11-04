package com.luxisoft.realityos.data

import org.json.JSONObject

internal data class SessionCredentials(
    val accessToken: String,
    val refreshToken: String,
    val isGuest: Boolean = false,
    val localAccess: Boolean? = null,
    val passwordAccount: Boolean? = null
) {
    fun toJson(): JSONObject = JSONObject()
        .put("access_token", accessToken)
        .put("refresh_token", refreshToken)
        .put("is_guest", isGuest)
        .apply {
            localAccess?.let { put("local_access", it) }
            passwordAccount?.let { put("password_account", it) }
        }
}
