package com.luxisoft.realityos

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.meta.wearable.dat.mockdevice.MockDeviceKit
import com.meta.wearable.dat.mockdevice.api.GlassesModel
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

/** A hardware-free smoke check; real camera, speech and audio require device QA. */
@RunWith(AndroidJUnit4::class)
class MockDeviceKitSmokeTest {
    @Test
    fun pairs_a_display_capable_glasses_mock() {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val mock = MockDeviceKit.getInstance(context)
        mock.enable()
        try {
            val pairing = mock.pairGlasses(GlassesModel.META_RAYBAN_DISPLAY)
            assertTrue(pairing.isSuccess)
        } finally {
            mock.disable()
        }
    }
}
