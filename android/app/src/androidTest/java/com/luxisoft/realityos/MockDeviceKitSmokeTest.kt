package com.luxisoft.realityos

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.meta.wearable.dat.mockdevice.MockDeviceKit
import com.meta.wearable.dat.mockdevice.api.GlassesModel
import com.meta.wearable.dat.mockdevice.api.MockDeviceKitConfig
import com.meta.wearable.dat.mockdevice.api.MockDeviceKitInterface
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Hardware-free DAT validation using Meta's official Mock Device Kit.
 *
 * This deliberately validates the simulated Display model, lifecycle, speech
 * controls and bundled Display preview server. It does not claim that camera,
 * microphone or audio routing ran on physical glasses.
 */
@RunWith(AndroidJUnit4::class)
class MockDeviceKitSmokeTest {
    private lateinit var mock: MockDeviceKitInterface
    private lateinit var targetContext: android.content.Context

    @Before
    fun enable_mock_device_kit() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        targetContext = instrumentation.targetContext
        grantRuntimePermission(instrumentation, "android.permission.BLUETOOTH_CONNECT")
        mock = MockDeviceKit.getInstance(targetContext)
        mock.enable(
            MockDeviceKitConfig(
                initiallyRegistered = true,
                initialPermissionsGranted = true,
            ),
        )
    }

    @After
    fun disable_mock_device_kit() {
        if (::mock.isInitialized) {
            mock.stopTestServer()
            mock.disable()
        }
    }

    @Test
    fun simulates_a_display_glasses_lifecycle_and_preview_server() {
        val pairing = mock.pairGlasses(GlassesModel.META_RAYBAN_DISPLAY)
        assertTrue(pairing.isSuccess)
        val glasses = pairing.getOrThrow()

        glasses.powerOn()
        glasses.unfold()
        glasses.don()
        assertEquals(1, mock.pairedDevices.size)

        // Meta supplies this renderer for a phone/browser Display preview.
        assertNotNull(glasses.services.display.createPreviewView(targetContext))
        val server = mock.startTestServer(0)
        assertTrue(server.isSuccess)
        assertTrue(server.getOrThrow() > 0)

        // These calls exercise the official mock speech controls, not Android STT.
        glasses.services.speech.setLocale("en-US")
        glasses.services.speech.simulateTranscription("Where is the yellow drill", false, 0.92f)
        glasses.services.speech.simulateTranscription("Where is the yellow drill", true, 0.92f)
    }

    private fun grantRuntimePermission(
        instrumentation: android.app.Instrumentation,
        permission: String,
    ) {
        instrumentation.uiAutomation.executeShellCommand(
            "pm grant ${instrumentation.targetContext.packageName} $permission",
        ).close()
    }
}
