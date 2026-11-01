package com.luxisoft.realityos

import android.graphics.BitmapFactory
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

/** Guards the owner-provided app icon/logo split used by the Android host. */
@RunWith(AndroidJUnit4::class)
class LuxisoftBrandAssetsTest {
    @Test
    fun internal_mark_has_a_transparent_canvas() {
        val resources = InstrumentationRegistry.getInstrumentation().targetContext.resources
        val mark = BitmapFactory.decodeResource(resources, R.drawable.luxisoft_brand_mark)

        assertTrue(mark.hasAlpha())
        assertEquals(0, mark.getPixel(0, 0).ushr(24))
    }

    @Test
    fun internal_favicon_remains_transparent_and_high_definition() {
        val resources = InstrumentationRegistry.getInstrumentation().targetContext.resources
        val favicon = BitmapFactory.decodeResource(resources, R.drawable.luxisoft_favicon_v9)

        assertEquals(512, favicon.width)
        assertEquals(512, favicon.height)
        assertTrue(favicon.hasAlpha())
        assertEquals(0, favicon.getPixel(0, 0).ushr(24))
        val visibleBounds = alphaBounds(favicon)
        assertTrue(
            "The internal favicon must remain the compact mark, not the wide brand logo.",
            kotlin.math.abs(visibleBounds.width - visibleBounds.height) <= 16,
        )
    }

    @Test
    fun launcher_uses_the_owner_provided_opaque_icon_unchanged() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val icon = BitmapFactory.decodeResource(context.resources, R.drawable.icon_app)

        assertEquals(R.mipmap.ic_launcher, context.applicationInfo.icon)
        assertEquals(50, icon.width)
        assertEquals(50, icon.height)
        assertFalse(icon.hasAlpha())
        assertEquals(0xFF62A9F8.toInt(), context.getColor(R.color.launcher_background))
    }

    private fun alphaBounds(bitmap: android.graphics.Bitmap): Bounds {
        var left = bitmap.width
        var top = bitmap.height
        var right = 0
        var bottom = 0
        for (y in 0 until bitmap.height) {
            for (x in 0 until bitmap.width) {
                if (bitmap.getPixel(x, y).ushr(24) <= 1) continue
                left = minOf(left, x)
                top = minOf(top, y)
                right = maxOf(right, x + 1)
                bottom = maxOf(bottom, y + 1)
            }
        }
        return Bounds(left, top, right, bottom)
    }

    private data class Bounds(
        val left: Int,
        val top: Int,
        val right: Int,
        val bottom: Int,
    ) {
        val width: Int get() = right - left
        val height: Int get() = bottom - top
    }
}
