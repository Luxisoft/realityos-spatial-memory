package com.luxisoft.realityos

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

/** Guards the user-provided, Debug-only panoramic Ray-Ban lens and its mask. */
@RunWith(AndroidJUnit4::class)
class RayBanDisplayLensAssetTest {
    @Test
    fun workspace_bokeh_background_is_high_definition_and_opaque() {
        val resources = InstrumentationRegistry.getInstrumentation().targetContext.resources
        val workspace = BitmapFactory.decodeResource(resources, R.drawable.realityos_workspace_bokeh)

        assertEquals(1312, workspace.width)
        assertEquals(1199, workspace.height)
        assertEquals(255, alpha(workspace, 656, 599))
    }

    @Test
    fun display_lens_and_mask_preserve_the_clean_central_opening() {
        val resources = InstrumentationRegistry.getInstrumentation().targetContext.resources
        val frame = BitmapFactory.decodeResource(resources, R.drawable.rayban_display_lens_frame)
        val aperture = BitmapFactory.decodeResource(resources, R.drawable.rayban_display_lens_aperture)

        assertEquals(1254, frame.width)
        assertEquals(858, frame.height)
        assertEquals(frame.width, aperture.width)
        assertEquals(frame.height, aperture.height)
        assertTrue(frame.hasAlpha())
        assertTrue(aperture.hasAlpha())
        assertTrue(alpha(frame, 623, 20) > 0)
        assertEquals(0, alpha(frame, 623, 444))

        val opening = transparentComponent(frame, seedX = 623, seedY = 444)
        assertEquals(176, opening.left)
        assertEquals(167, opening.top)
        assertEquals(1049, opening.right)
        assertEquals(753, opening.bottom)
        assertEquals(423_174, opening.area)

        assertEquals(0, alpha(aperture, 0, 0))
        assertEquals(255, alpha(aperture, 623, 444))
        assertEquals(opening.area, opaquePixelCount(aperture))
        assertTrue(
            "The renderer-safe viewport must stay fully inside the opaque lens mask.",
            isFullyOpaque(aperture, left = 425, top = 216, right = 875, bottom = 666),
        )
    }

    private fun transparentComponent(bitmap: Bitmap, seedX: Int, seedY: Int): Component {
        val width = bitmap.width
        val height = bitmap.height
        val pixels = IntArray(width * height)
        bitmap.getPixels(pixels, 0, width, 0, 0, width, height)
        val visited = BooleanArray(pixels.size)
        val queue = IntArray(pixels.size)
        var head = 0
        var tail = 0
        var left = width
        var top = height
        var right = 0
        var bottom = 0

        fun enqueue(index: Int) {
            if (visited[index] || pixels[index].ushr(24) > 1) return
            visited[index] = true
            queue[tail++] = index
        }

        enqueue(seedY * width + seedX)
        while (head < tail) {
            val index = queue[head++]
            val x = index % width
            val y = index / width
            left = minOf(left, x)
            top = minOf(top, y)
            right = maxOf(right, x + 1)
            bottom = maxOf(bottom, y + 1)

            if (x > 0) enqueue(index - 1)
            if (x < width - 1) enqueue(index + 1)
            if (y > 0) enqueue(index - width)
            if (y < height - 1) enqueue(index + width)
        }

        return Component(left, top, right, bottom, tail)
    }

    private fun opaquePixelCount(bitmap: Bitmap): Int {
        val pixels = IntArray(bitmap.width * bitmap.height)
        bitmap.getPixels(pixels, 0, bitmap.width, 0, 0, bitmap.width, bitmap.height)
        return pixels.count { it.ushr(24) > 0 }
    }

    private fun alpha(bitmap: Bitmap, x: Int, y: Int): Int = bitmap.getPixel(x, y).ushr(24)

    private fun isFullyOpaque(
        bitmap: Bitmap,
        left: Int,
        top: Int,
        right: Int,
        bottom: Int,
    ): Boolean {
        for (y in top until bottom) {
            for (x in left until right) {
                if (alpha(bitmap, x, y) != 255) return false
            }
        }
        return true
    }

    private data class Component(
        val left: Int,
        val top: Int,
        val right: Int,
        val bottom: Int,
        val area: Int,
    )
}
