package com.luxisoft.realityos

import android.app.Application
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.StateRestorationTester
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class EntryExperienceTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    private fun tap(tag: String) = compose.onNodeWithTag(tag).performClick()
    private fun scrollTap(tag: String) = compose.onNodeWithTag(tag).performScrollTo().performClick()

    private fun capture(name: String) {
        compose.waitForIdle()
        val directory = File("build/outputs/entry-design").apply { mkdirs() }
        compose.runOnIdle {
            val view = compose.activity.findViewById<android.view.View>(android.R.id.content)
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            File(directory, "$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
        }
    }

    @Test fun facebookRequiresConsentAndEmailRemainsIndependent() {
        val consent = mutableStateOf(false)
        val busy = mutableStateOf(false)
        val error = mutableStateOf("")
        var facebook = 0
        var email = 0
        var explore = 0
        compose.setContent {
            RealityOsTheme {
                FacebookAccessScreen(busy.value, error.value, consent.value, { consent.value = it }, { facebook++ }, { email++ }, { explore++ })
            }
        }
        compose.onNodeWithTag("access-meta").assertIsNotEnabled()
        scrollTap("access-email")
        compose.runOnIdle {
            assertEquals(1, email)
            assertEquals(0, facebook)
        }
        compose.onNode(isToggleable()).performScrollTo().performClick()
        capture("access-consented-en-390")
        scrollTap("access-meta")
        scrollTap("access-explore")
        compose.runOnIdle {
            assertEquals(1, facebook)
            assertEquals(1, explore)
            busy.value = true
        }
        compose.onNodeWithTag("access-meta").assertIsNotEnabled()
        compose.onNodeWithTag("access-email").assertIsNotEnabled()
        compose.onNodeWithTag("access-explore").assertIsNotEnabled()
        compose.onNode(isToggleable()).assertIsNotEnabled()
        capture("access-loading-en-390")
        compose.runOnIdle {
            busy.value = false
            error.value = "Connection interrupted. Try again."
        }
        compose.onNodeWithTag("access-error").performScrollTo().assertIsDisplayed()
        capture("access-error-en-390")
        compose.onNodeWithTag("access-meta").assertIsEnabled()
    }

    @Test fun firstRunCanSkipOrCompleteAndNeverCompletesOnPageChange() {
        var finished = 0
        compose.setContent { RealityOsTheme { RealityWelcome(replay = false, onFinish = { finished++ }) } }
        compose.onNodeWithTag("explore-exit").assertTextEquals("Skip")
        compose.onNodeWithTag("explore-previous").assertIsNotEnabled()
        tap("explore-next")
        compose.onNodeWithTag("explore-title-1").assertIsDisplayed()
        compose.runOnIdle { assertEquals(0, finished) }
        compose.runOnIdle { compose.activity.onBackPressedDispatcher.onBackPressed() }
        compose.onNodeWithTag("explore-title-0").assertIsDisplayed()
        tap("explore-exit")
        compose.runOnIdle { assertEquals(1, finished) }
        repeat(5) { tap("explore-next") }
        compose.onNodeWithTag("explore-next").assertTextEquals("Get started")
        tap("explore-next")
        compose.runOnIdle { assertEquals(2, finished) }
    }

    @Test fun replaySupportsSwipePreviousRestorationAndClose() {
        var finished = 0
        val restoration = StateRestorationTester(compose)
        restoration.setContent { RealityOsTheme { RealityWelcome(replay = true, onFinish = { finished++ }) } }
        compose.onNodeWithTag("explore-exit").assertTextEquals("Close")
        compose.onNodeWithTag("explore-pager").performTouchInput { swipeLeft() }
        compose.onNodeWithTag("explore-title-1").assertIsDisplayed()
        tap("explore-next")
        restoration.emulateSavedInstanceStateRestore()
        compose.onNodeWithTag("explore-title-2").assertIsDisplayed()
        tap("explore-previous")
        compose.onNodeWithContentDescription("Page 2 of 6").assertExists()
        tap("explore-exit")
        compose.runOnIdle { assertEquals(1, finished) }
        repeat(4) { tap("explore-next") }
        compose.onNodeWithTag("explore-next").assertTextEquals("Back to the app")
        tap("explore-next")
        compose.runOnIdle { assertEquals(2, finished) }
    }

    private fun gallery(prefix: String, scale: Float = 1f) {
        val welcome = mutableStateOf(false)
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    if (welcome.value) {
                        RealityWelcome(replay = true, onFinish = { welcome.value = false })
                    } else {
                        FacebookAccessScreen(false, "", false, {}, {}, {}, { welcome.value = true })
                    }
                }
            }
        }
        capture("access-$prefix")
        compose.onNodeWithTag("access-email").performScrollTo().assertIsDisplayed()
        capture("access-actions-$prefix")
        scrollTap("access-explore")
        repeat(6) { page ->
            compose.onNodeWithTag("explore-title-$page").performScrollTo().assertIsDisplayed()
            // Return to the illustration for consistent visual review, including large text.
            compose.onNodeWithTag("explore-page-$page").performTouchInput { swipeDown() }
            capture("explore-$page-$prefix")
            if (page == 5) {
                compose.onNodeWithTag("explore-credits").performScrollTo().assertExists()
                capture("credits-$prefix")
            }
            compose.onNodeWithTag("explore-next").assertIsDisplayed()
            tap("explore-next")
        }
        compose.onNodeWithTag("access-screen").assertExists()
    }

    @Test fun english390() = gallery("en-390")

    @Test
    @Config(qualifiers = "es-w390dp-h844dp-mdpi")
    fun spanish390() = gallery("es-390")

    @Test
    @Config(qualifiers = "w320dp-h720dp-mdpi")
    fun narrow320() = gallery("en-320")

    @Test
    @Config(qualifiers = "w480dp-h900dp-mdpi")
    fun wide480() = gallery("en-480")

    @Test
    @Config(qualifiers = "es-w320dp-h720dp-mdpi")
    fun enlargedText() = gallery("es-320-text200", 2f)
}
