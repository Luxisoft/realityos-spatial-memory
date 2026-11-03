package com.luxisoft.realityos

import org.json.JSONObject

internal class AccountConflict(val fields: Set<String>) : IllegalStateException("Account details already registered")

internal class AccountFailure(val messageResource: Int) : IllegalStateException("Account request failed")

internal fun accountFailure(path: String, status: Int): AccountFailure? {
    if (path !in setOf("auth/login", "auth/register", "auth/change-pending-email", "auth/resend-confirmation", "auth/forgot-password")) return null
    val message = when {
        status == 401 && path == "auth/change-pending-email" -> R.string.account_correction_credentials_error
        status == 401 -> R.string.account_credentials_error
        status == 403 && path == "auth/login" -> R.string.account_confirmation_required
        status == 409 && path == "auth/change-pending-email" -> R.string.account_correction_unavailable
        status == 429 -> R.string.account_too_many_attempts
        status == 503 && path != "auth/login" -> R.string.account_delivery_failed
        status == 422 -> R.string.account_invalid_details
        else -> R.string.account_service_unavailable
    }
    return AccountFailure(message)
}

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
