package com.luxisoft.realityos

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PublishCapturePolicyTest {
    @Test
    fun `wearable route with ready camera uses the glasses`() {
        assertTrue(PublishCapturePolicy.useWearable(InputRoute.WEARABLE, wearableCameraReady = true))
    }

    @Test
    fun `wearable route without camera falls back to the phone`() {
        assertFalse(PublishCapturePolicy.useWearable(InputRoute.WEARABLE, wearableCameraReady = false))
    }

    @Test
    fun `phone route always uses the phone camera`() {
        assertFalse(PublishCapturePolicy.useWearable(InputRoute.PHONE, wearableCameraReady = true))
    }
}
