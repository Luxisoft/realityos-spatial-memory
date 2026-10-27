package com.luxisoft.realityos

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * A server administrator provisions this once after enrolling the physical
 * device. This is deliberately a device credential, not a person login.
 */
data class DeviceProvisioning(
    val apiBaseUrl: String,
    val workspaceId: String,
    val deviceId: String,
    val deviceKey: String,
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
        return DeviceProvisioning(endpoint, workspace, deviceId, deviceKey)
    }

    fun save(value: DeviceProvisioning) {
        preferences.edit()
            .putString("api_base_url", value.apiBaseUrl.trim().trimEnd('/'))
            .putString("workspace_id", value.workspaceId.trim())
            .putString("device_id", value.deviceId.trim())
            .putString("device_key", value.deviceKey.trim())
            .apply()
    }
}
