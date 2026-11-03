package com.luxisoft.realityos

import org.json.JSONObject

internal class AccountConflict(val fields: Set<String>) : IllegalStateException("Account details already registered")

internal fun accountConflict(path: String, status: Int, body: String): AccountConflict? {
    if (status != 409 || path !in setOf("auth/register", "auth/change-pending-email")) return null
    val fields = runCatching {
        val values = JSONObject(body).optJSONObject("detail")?.optJSONArray("fields")
        if (values == null) emptySet() else (0 until values.length()).map { values.optString(it) }.filter { it in setOf("email", "username") }.toSet()
    }.getOrDefault(emptySet())
    // Keep older servers' generic duplicate response useful during a rolling update.
    return if (fields.isNotEmpty()) {
        AccountConflict(fields)
    } else if (path == "auth/register") {
        AccountConflict(setOf("email", "username"))
    } else {
        null
    }
}
