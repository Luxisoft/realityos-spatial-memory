package com.luxisoft.realityos

import android.app.Application
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "en-w480dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class RootPanelTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    @After fun resetLanguage() {
        RealityExperienceStore(compose.activity).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun panel(scale: Float) {
        LocalizedText.initialize(compose.activity)
        RealityExperienceStore(compose.activity).setLanguage(if (compose.activity.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
        var closed = false
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    Box(Modifier.fillMaxSize().testTag("panel-window")) {
                        RootPanel(onClose = { closed = true }) { Text(localizedText(R.string.ui_search)) }
                    }
                }
            }
        }
        compose.mainClock.advanceTimeBy(1000)
        val window = compose.onNodeWithTag("panel-window").fetchSemanticsNode().boundsInRoot
        val panel = compose.onNodeWithTag("root-panel").assertIsDisplayed().fetchSemanticsNode().boundsInRoot
        assertEquals(window.top, panel.top, .5f)
        assertEquals(window.bottom, panel.bottom, .5f)
        compose.runOnIdle {
            val view = compose.activity.window.decorView
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val directory = File("build/outputs/root-panel").apply { mkdirs() }
            File(directory, "panel-$scale.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
        compose.onNodeWithContentDescription(localizedText(R.string.ui_close)).performTouchInput { click() }
        compose.mainClock.advanceTimeBy(1000)
        compose.runOnIdle { assertTrue(closed) }
    }

    @Test fun englishPanelUsesEntireHeight() = panel(1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun spanishNarrowPanelUsesEntireHeightAtLargeText() = panel(2f)
}
