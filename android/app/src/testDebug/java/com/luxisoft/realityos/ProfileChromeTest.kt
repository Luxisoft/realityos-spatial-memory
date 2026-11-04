package com.luxisoft.realityos

import android.app.Application
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import com.luxisoft.realityos.host.RealityDrawer
import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
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
class ProfileChromeTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    @Before fun initialize() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(if (context.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
    }

    @After fun reset() {
        RuntimeEnvironment.setFontScale(1f)
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun profile(source: String) = JSONObject()
        .put("display_name", "Elena Marquez").put("email", "elena@example.test").put("profile_source", source)
        .put("location", "California").put("hometown", "Bogotá").put("headline", "Enfermería")
        .put("birthday", "1990-04-12").put("age_min", 36).put("age_max", 36)
        .put("phone", "+1 555 0100").put("gender", "female").put("website", "https://example.test")
        .put("facebook_link", "https://facebook.invalid/example")
        .put("counts", JSONObject().put("friends", 710).put("likes", 711).put("photos", 712).put("videos", 713))
        .put("friends", JSONArray().put(JSONObject().put("name", "Facebook friend")))

    private fun capture(name: String) {
        compose.waitForIdle()
        compose.runOnIdle {
            val view = compose.activity.window.decorView
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val directory = File("build/outputs/profile-chrome").apply { mkdirs() }
            File(directory, "$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
    }

    private fun checkEmailProfile(name: String, scale: Float, userId: String? = null) {
        RuntimeEnvironment.setFontScale(scale)
        val state = ProfileState(userId).apply { apply(profile("email")) }
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme { ProfileHeader(state, onMenu = {}, onGlasses = {}) }
            }
        }
        if (scale == 1f) compose.onNodeWithTag("global-profile-header").assertHeightIsEqualTo(64.dp)
        val nameBounds = compose.onNodeWithTag("profile-name").fetchSemanticsNode().boundsInRoot
        val emailBounds = compose.onNodeWithTag("profile-email").fetchSemanticsNode().boundsInRoot
        assertEquals(nameBounds.bottom, emailBounds.top, 1f)
        compose.onNodeWithTag("profile-expand").assertHeightIsAtLeast(48.dp).assertIsDisplayed()
        compose.onNodeWithTag("profile-facebook").assertDoesNotExist()
        capture("collapsed-$name")
        compose.onNodeWithTag("profile-expand").performClick()
        compose.onNodeWithText("California").assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.ui_location)).assertDoesNotExist()
        compose.onNodeWithContentDescription(localizedText(R.string.ui_location)).assertIsDisplayed()
        listOf(R.string.ui_friends, R.string.ui_likes, R.string.ui_photos, R.string.ui_videos).forEach {
            compose.onNodeWithContentDescription(localizedText(it)).assertDoesNotExist()
        }
        listOf("710", "711", "712", "713", "Facebook friend").forEach { compose.onNodeWithText(it).assertDoesNotExist() }
        capture("expanded-$name")
        // Provider visibility belongs to the viewed profile, regardless of the viewer's login.
        compose.runOnIdle { state.apply(profile("facebook")) }
        compose.onNodeWithTag("profile-facebook").assertIsDisplayed()
        compose.onNodeWithText("711").performScrollTo().assertIsDisplayed()
        compose.onNodeWithContentDescription(localizedText(R.string.ui_likes)).assertExists()
        compose.onNodeWithText(localizedText(R.string.ui_likes)).assertDoesNotExist()
        capture("facebook-$name")
        compose.runOnIdle { state.apply(profile("other")) }
        compose.onNodeWithText("711").assertDoesNotExist()
        compose.onNodeWithText("Facebook friend").assertDoesNotExist()
    }

    @Test fun compactEmailProfileShowsOnlyItsOwnInformation() = checkEmailProfile("es-390", 1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun narrowSpanishProfileKeepsNameAndEmailTogetherAtLargeText() = checkEmailProfile("es-320-large", 2f)

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun visitedProfileUsesItsOwnProviderAtLargeEnglishText() = checkEmailProfile("en-320-large", 2f, "visited-user")

    private fun checkDrawer(name: String, scale: Float) {
        RuntimeEnvironment.setFontScale(scale)
        val actions = mutableListOf<String>()
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    RealityDrawer(
                        RealityExperienceStore(RuntimeEnvironment.getApplication()),
                        onAbout = { actions += "about" },
                        onConnections = { actions += "connections" },
                        connectionsEnabled = true,
                        onLogout = { actions += "logout" }
                    )
                }
            }
        }
        val keys = listOf("connections", "about", "logout")
        val icons = keys.map { compose.onNodeWithTag("drawer-$it-icon", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot }
        assertTrue(icons.all { it.left == icons.first().left })
        val labels = listOf(R.string.storage_title, R.string.nav_about, R.string.ui_sign_out).map {
            compose.onNodeWithText(localizedText(it), useUnmergedTree = true).assertIsDisplayed().fetchSemanticsNode().boundsInRoot
        }
        assertTrue(labels.all { it.left == labels.first().left })
        assertTrue(labels.first().left > icons.first().right)
        capture("drawer-$name")
        keys.forEach { compose.onNodeWithTag("drawer-$it").assertHeightIsAtLeast(48.dp).performTouchInput { click() } }
        compose.runOnIdle { assertEquals(keys, actions) }
        compose.onNodeWithTag("drawer-language").assertIsDisplayed()
    }

    @Test fun drawerIconsAndTextShareTheSameLeftAlignment() = checkDrawer("es-390", 1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun narrowSpanishDrawerKeepsAlignmentAtLargeText() = checkDrawer("es-320-large", 2f)

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun narrowEnglishDrawerKeepsAlignmentAtLargeText() = checkDrawer("en-320-large", 2f)
}
