package com.luxisoft.realityos

import android.app.Application
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import com.luxisoft.realityos.host.GalleryActions
import com.luxisoft.realityos.host.MetaViewHeader
import java.io.File
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "es-w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class UnifiedChromeTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    @After fun reset() {
        RuntimeEnvironment.setFontScale(1f)
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun checkChrome(name: String, scale: Float) {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(if (context.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
        RuntimeEnvironment.setFontScale(scale)
        val profile = ProfileState().apply { apply(JSONObject().put("display_name", "Elena Marquez").put("email", "elena@example.test").put("headline", "Community coordinator").put("profile_source", "email")) }
        val actions = mutableListOf<String>()
        val groups = GalleryTopBarState().apply {
            loading = false
            options = listOf(WorkspaceOption("group", "Meta Social Media", "admin"))
            selectedId = "group"
        }
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    Scaffold(bottomBar = {
                        ProfileHeader(profile, bottom = true, onMenu = { actions += "menu" }, onAvatar = { actions += "gallery" }, onGlasses = { actions += "glasses" }, onSearch = { actions += "search" }, onEditDrawerChange = { if (it) actions += "edit" })
                    }) { padding ->
                        Column(Modifier.fillMaxSize().padding(padding)) {
                            GalleryActions(groups)
                            MetaViewHeader(localizedText(R.string.preview_simulator_title), MetaSection.PREVIEW, { actions += "meta-${it.name}" }, { actions += "controls" })
                            Text("Meta Social Media", Modifier.padding(16.dp))
                        }
                    }
                }
            }
        }
        val keys = listOf("host-menu-button", "profile-avatar", "profile-expand", "profile-glasses", "host-search-button")
        val bounds = keys.map { compose.onNodeWithTag(it).assertIsDisplayed().assertHeightIsAtLeast(48.dp).fetchSemanticsNode().boundsInRoot }
        assertTrue(bounds.zipWithNext().all { (left, right) -> left.right <= right.left })
        assertTrue(bounds.last().right <= compose.activity.resources.configuration.screenWidthDp)
        val edit = compose.onNodeWithTag("profile-edit").assertIsDisplayed().fetchSemanticsNode().boundsInRoot
        val portrait = bounds[1]
        assertEquals(portrait.right, edit.right, 0.5f)
        assertEquals(portrait.bottom, edit.bottom, 0.5f)
        assertTrue(edit.left > portrait.left && edit.top > portrait.top)
        // Tap the portrait away from its separately clickable edit badge.
        compose.onNodeWithTag("profile-avatar").performTouchInput { click(androidx.compose.ui.geometry.Offset(8f, 8f)) }
        compose.runOnIdle { assertEquals(listOf("gallery"), actions) }
        compose.onNodeWithTag("host-menu-button").performTouchInput { click() }
        compose.onNodeWithTag("profile-glasses").performTouchInput { click() }
        compose.onNodeWithTag("host-search-button").performTouchInput { click() }
        compose.onNodeWithTag("host-preview-controls-button").performClick()
        compose.runOnIdle { assertEquals(listOf("gallery", "menu", "glasses", "search", "controls"), actions) }
        capture("collapsed-$name")
        compose.onNodeWithTag("profile-expand").performClick()
        compose.mainClock.advanceTimeBy(500)
        compose.waitForIdle()
        capture("expanded-$name")
        val details = compose.onNodeWithTag("profile-details").assertIsDisplayed().fetchSemanticsNode().boundsInRoot
        val avatar = compose.onNodeWithTag("profile-avatar").fetchSemanticsNode().boundsInRoot
        assertTrue(details.bottom <= avatar.top)
        capture("expanded-$name")
        compose.onNodeWithTag("profile-edit").performClick()
        compose.runOnIdle { assertEquals(listOf("gallery", "menu", "glasses", "search", "controls", "edit"), actions) }
    }

    private fun capture(name: String) {
        compose.runOnIdle {
            val view = compose.activity.window.decorView
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val directory = File("build/outputs/unified-chrome").apply { mkdirs() }
            File(directory, "$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
    }

    @Test fun spanishChrome() = checkChrome("es-390", 1f)

    @Test
    @Config(qualifiers = "en-w480dp-h844dp-mdpi")
    fun englishChrome() = checkChrome("en-480", 1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun largeSpanishChrome() = checkChrome("es-320-large", 2f)

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun largeEnglishChrome() = checkChrome("en-320-large", 2f)
}
