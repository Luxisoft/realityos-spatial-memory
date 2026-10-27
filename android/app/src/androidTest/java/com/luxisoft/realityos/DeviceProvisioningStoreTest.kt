package com.luxisoft.realityos

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.time.Instant
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

/** Ensures runtime-issued live credentials are retained only in encrypted app storage. */
@RunWith(AndroidJUnit4::class)
class DeviceProvisioningStoreTest {
    @Test
    fun saves_live_virtual_profile_and_keeps_a_stable_installation_id() {
        val store = DeviceProvisioningStore(InstrumentationRegistry.getInstrumentation().targetContext)
        val installationId = store.installationId()
        val profile = DeviceProvisioning(
            apiBaseUrl = "https://realityos.luxisoft.com/v1",
            workspaceId = "e8a71467-fca1-4315-b0b2-2c1212ad8f07",
            deviceId = "virtual-display-test",
            deviceKey = "runtime-key-only",
            workspaceName = "Taller de electrónica",
            expiresAt = Instant.parse("2026-10-28T00:00:00Z"),
            processingMode = "live",
            source = ProvisioningSource.VIRTUAL_LIVE,
        )

        store.save(profile)
        val restored = store.read()

        assertEquals(profile, restored)
        assertEquals(installationId, store.installationId())
        assertTrue(installationId.isNotBlank())
        assertNotEquals(profile.deviceKey, "")
    }
}
