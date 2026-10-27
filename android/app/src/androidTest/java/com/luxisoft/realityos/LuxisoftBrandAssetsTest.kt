package com.luxisoft.realityos

import android.graphics.BitmapFactory
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.xmlpull.v1.XmlPullParser

/** Guards the owner-provided LUXISOFT asset split used by the Android host. */
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
    fun adaptive_launcher_uses_the_current_luxisoft_favicon() {
        val resources = InstrumentationRegistry.getInstrumentation().targetContext.resources
        val parser = resources.getXml(R.mipmap.ic_launcher)
        var foreground = 0
        while (parser.next() != XmlPullParser.END_DOCUMENT) {
            if (parser.eventType == XmlPullParser.START_TAG && parser.name == "foreground") {
                foreground = parser.getAttributeResourceValue(
                    "http://schemas.android.com/apk/res/android",
                    "drawable",
                    0,
                )
                break
            }
        }

        assertEquals(R.drawable.luxisoft_favicon_v9, foreground)
    }
}
