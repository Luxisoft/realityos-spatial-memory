package com.luxisoft.realityos

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import java.time.Instant
import java.util.UUID

/**
 * A server administrator provisions this once after enrolling the physical
 * device. This is deliberately a device credential, not a person login.
 */
enum class ProvisioningSource {
    VIRTUAL_LIVE,
    CUSTOM,
}

data class DeviceProvisioning(
    val apiBaseUrl: String,
    val workspaceId: String,
    val deviceId: String,
    val deviceKey: String,
    val workspaceName: String? = null,
    val expiresAt: Instant? = null,
    val processingMode: String? = null,
    val source: ProvisioningSource = ProvisioningSource.CUSTOM,
)

data class ProvisioningDraft(
    val apiBaseUrl: String = BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
    val workspaceId: String = "",
    val deviceId: String = "",
    val deviceKey: String = "",
    val workspaceName: String? = null,
    val expiresAt: Instant? = null,
    val processingMode: String? = null,
    val source: ProvisioningSource = ProvisioningSource.CUSTOM,
)

fun DeviceProvisioning.toDraft() = ProvisioningDraft(
    apiBaseUrl = apiBaseUrl,
    workspaceId = workspaceId,
    deviceId = deviceId,
    deviceKey = deviceKey,
    workspaceName = workspaceName,
    expiresAt = expiresAt,
    processingMode = processingMode,
    source = source,
)

class DeviceProvisioningStore(context: Context) {
    private val preferences = EncryptedSharedPreferences.create(
        context,
        "realityos-device-provisioning",
        MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    fun read(): DeviceProvisioning? {
        val endpoint = preferences.getString("api_base_url", null) ?: return null
        val workspace = preferences.getString("workspace_id", null) ?: return null
        val deviceId = preferences.getString("device_id", null) ?: return null
        val deviceKey = preferences.getString("device_key", null) ?: return null
        val expiry = preferences.getString("virtual_device_expires_at", null)
            ?.let { value -> runCatching { Instant.parse(value) }.getOrNull() }
        val source = preferences.getString("provisioning_source", ProvisioningSource.CUSTOM.name)
            ?.let { value -> runCatching { ProvisioningSource.valueOf(value) }.getOrNull() }
            ?: ProvisioningSource.CUSTOM
        return DeviceProvisioning(
            apiBaseUrl = endpoint,
            workspaceId = workspace,
            deviceId = deviceId,
            deviceKey = deviceKey,
            workspaceName = preferences.getString("workspace_name", null),
            expiresAt = expiry,
            processingMode = preferences.getString("processing_mode", null),
            source = source,
        )
    }

    fun save(value: DeviceProvisioning) {
        preferences.edit()
            .putString("api_base_url", value.apiBaseUrl.trim().trimEnd('/'))
            .putString("workspace_id", value.workspaceId.trim())
            .putString("device_id", value.deviceId.trim())
            .putString("device_key", value.deviceKey.trim())
            .putString("workspace_name", value.workspaceName)
            .putString("virtual_device_expires_at", value.expiresAt?.toString())
            .putString("processing_mode", value.processingMode)
            .putString("provisioning_source", value.source.name)
            .apply()
    }

    /** Stable but non-secret identifier used only to rotate this installation's virtual device. */
    fun installationId(): String {
        val existing = preferences.getString("virtual_installation_id", null)
        if (!existing.isNullOrBlank()) return existing
        return UUID.randomUUID().toString().also { identifier ->
            preferences.edit().putString("virtual_installation_id", identifier).apply()
        }
    }
}
