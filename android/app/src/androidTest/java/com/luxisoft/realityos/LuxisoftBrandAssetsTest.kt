package com.luxisoft.realityos

import android.graphics.BitmapFactory
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test
import org.junit.runner.RunWith

/** Guards the original app icon shared by the launcher and internal branding. */
@RunWith(AndroidJUnit4::class)
class LuxisoftBrandAssetsTest {
    @Test
    fun launcher_uses_the_owner_provided_opaque_icon_unchanged() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val icon = BitmapFactory.decodeResource(context.resources, R.drawable.icon_app)

        assertEquals(R.mipmap.ic_launcher, context.applicationInfo.icon)
        assertEquals(150, icon.width)
        assertEquals(150, icon.height)
        assertFalse(icon.hasAlpha())
        assertEquals(0xFF017DF7.toInt(), context.getColor(R.color.launcher_background))
    }
}
