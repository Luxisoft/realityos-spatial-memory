package com.luxisoft.realityos

import android.app.Application
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "en-w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class LocalAccountChooserTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    private fun chooser(scale: Float) {
        val groups = listOf("Pacific Ridge Police Department", "California Valley Medical Center", "Sonoran Neurological Institute")
        val names = listOf("Alex Rivera", "Maya Johnson", "Daniel Kim", "Elena Marquez", "Mateo Rios", "Sarah Chen", "Noah Brooks", "Lucia Vega", "Owen Patel")
        val accounts = names.mapIndexed { index, name -> JSONObject().put("id", index.toString()).put("username", "person-$index").put("display_name", name).put("workspace_name", groups[index / 3]) }
        var selected = ""
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme { LocalAccountChooser(accounts, false, false, {}, { selected = it.getString("id") }) }
            }
        }
        compose.onNodeWithText("Alex Rivera").assertIsDisplayed()
        capture("top-$scale")
        compose.onNodeWithTag("local-account-person-8").performScrollTo().assertIsDisplayed().performClick()
        assertEquals("8", selected)
        capture("bottom-$scale")
    }

    private fun capture(name: String) {
        compose.waitForIdle()
        compose.runOnIdle {
            val view = compose.activity.window.decorView
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val language = compose.activity.resources.configuration.locales[0].language
            val directory = File("build/outputs/local-access").apply { mkdirs() }
            File(directory, "$language-$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
    }

    @Test fun allNineAccountsCanBeReachedAndSelected() = chooser(1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun spanishNarrowScreenAtTwoHundredPercentText() = chooser(2f)

    @Test fun connectionErrorOffersRetry() {
        var retries = 0
        compose.setContent { RealityOsTheme { LocalAccountChooser(emptyList(), false, true, { retries++ }, {}) } }
        compose.onNodeWithText("Retry").performClick()
        assertEquals(1, retries)
        capture("error")
    }
}
