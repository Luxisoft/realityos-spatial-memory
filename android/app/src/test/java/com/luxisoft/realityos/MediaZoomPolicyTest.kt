package com.luxisoft.realityos

import androidx.compose.foundation.gestures.calculateCentroid
import androidx.compose.foundation.gestures.calculatePan
import androidx.compose.foundation.gestures.calculateZoom
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.pointer.PointerEvent
import androidx.compose.ui.input.pointer.PointerId
import androidx.compose.ui.input.pointer.PointerInputChange
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MediaZoomPolicyTest {
    private fun gesture(
        state: MediaZoomTransform,
        centroidX: Float = 200f,
        centroidY: Float = 400f,
        movementX: Float = 0f,
        movementY: Float = 0f,
        scaleChange: Float = 1f
    ) = MediaZoomPolicy.transform(state, 400, 800, 1600, 800, centroidX, centroidY, movementX, movementY, scaleChange)

    @Test
    fun `actual Compose release event has no centroid and must preserve the transform`() {
        val release = PointerEvent(
            listOf(
                PointerInputChange(
                    id = PointerId(1),
                    uptimeMillis = 32,
                    position = Offset(200f, 400f),
                    pressed = false,
                    previousUptimeMillis = 16,
                    previousPosition = Offset(200f, 400f),
                    previousPressed = true,
                    isInitiallyConsumed = false
                )
            )
        )
        assertEquals(Offset.Unspecified, release.calculateCentroid(useCurrent = false))
        assertEquals(1f, release.calculateZoom())
        assertEquals(Offset.Zero, release.calculatePan())
        val enlarged = MediaZoomTransform(5f, 60f, 20f)
        assertEquals(enlarged, gesture(enlarged, centroidX = Float.NaN, centroidY = Float.NaN, scaleChange = release.calculateZoom()))
    }

    @Test
    fun `releasing all pointers keeps the enlarged image visible and subsequent drag works`() {
        val enlarged = gesture(MediaZoomTransform(), scaleChange = 5f)
        val released = gesture(enlarged, centroidX = Float.NaN, centroidY = Float.NaN)
        assertEquals(enlarged, released)
        val dragged = gesture(released, movementX = 60f, movementY = 20f)
        assertEquals(MediaZoomTransform(5f, 60f, 20f), dragged)
        assertTrue(dragged.panX.isFinite() && dragged.panY.isFinite())
    }

    @Test
    fun `release after repeated pinch gestures never poisons the transform`() {
        var state = MediaZoomTransform()
        repeat(20) {
            state = gesture(state, scaleChange = 1.1f)
            val expected = state
            state = gesture(state, centroidX = Float.NaN, centroidY = Float.NaN)
            assertEquals(expected, state)
        }
    }

    @Test
    fun `pinch and pan stay bounded and zooming out restores the image center`() {
        val enlarged = gesture(MediaZoomTransform(), centroidX = 100f, scaleChange = 5f)
        assertEquals(MediaZoomTransform(5f, 400f, 0f), enlarged)
        assertEquals(MediaZoomTransform(5f, 800f, 100f), gesture(enlarged, movementX = 10000f, movementY = 10000f))
        assertEquals(MediaZoomTransform(), gesture(enlarged, scaleChange = 0.01f))
        assertEquals(8f, gesture(enlarged, scaleChange = 100f).scale)
    }

    @Test
    fun `non finite gesture input cannot make an image disappear`() {
        val enlarged = MediaZoomTransform(5f, 60f, 20f)
        for (invalid in listOf(Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY)) {
            assertEquals(enlarged, gesture(enlarged, centroidX = invalid))
            assertEquals(enlarged, gesture(enlarged, centroidY = invalid))
            assertEquals(enlarged, gesture(enlarged, movementX = invalid))
            assertEquals(enlarged, gesture(enlarged, movementY = invalid))
            assertEquals(enlarged, gesture(enlarged, scaleChange = invalid))
            assertEquals(0f to 0f, MediaZoomPolicy.panLimits(400, 800, 1600, 800, invalid))
        }
        assertEquals(enlarged, gesture(enlarged, scaleChange = 0f))
        assertEquals(enlarged, gesture(enlarged, scaleChange = -1f))
        assertEquals(MediaZoomTransform(), gesture(MediaZoomTransform(Float.NaN, Float.NaN, Float.NaN)))
    }

    @Test
    fun `landscape image fits without cropping and only pans along enlarged axes`() {
        assertEquals(0f to 0f, MediaZoomPolicy.panLimits(400, 800, 1600, 800, 1f))
        assertEquals(200f to 0f, MediaZoomPolicy.panLimits(400, 800, 1600, 800, 2f))
        assertEquals(800f to 100f, MediaZoomPolicy.panLimits(400, 800, 1600, 800, 5f))
    }

    @Test
    fun `portrait image fits height before zooming`() {
        assertEquals(0f to 0f, MediaZoomPolicy.panLimits(400, 800, 800, 2400, 1f))
        val limits = MediaZoomPolicy.panLimits(400, 800, 800, 2400, 2f)
        assertEquals(66.6667f, limits.first, 0.001f)
        assertEquals(400f, limits.second, 0.001f)
    }

    @Test
    fun `small image is not expanded to fill screen`() {
        assertEquals(0f to 0f, MediaZoomPolicy.panLimits(400, 800, 100, 100, 2f))
        assertEquals(200f to 0f, MediaZoomPolicy.panLimits(400, 800, 100, 100, 8f))
    }

    @Test
    fun `loading and empty viewport cannot pan`() {
        assertEquals(0f to 0f, MediaZoomPolicy.panLimits(400, 800, 0, 0, 4f))
        assertEquals(0f to 0f, MediaZoomPolicy.panLimits(0, 0, 800, 1600, 4f))
    }
}
