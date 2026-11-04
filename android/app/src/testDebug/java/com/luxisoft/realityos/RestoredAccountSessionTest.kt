package com.luxisoft.realityos

import android.app.Application
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import java.io.IOException
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CompletableDeferred
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
@Config(application = Application::class, sdk = [35], qualifiers = "en-w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class RestoredAccountSessionTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    @Before fun start() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(if (context.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
        SocialSession.clear()
        SocialSession.remember(JSONObject().put("access_token", "saved").put("refresh_token", "refresh").put("password_account", true))
        SocialSession.passwordAccountConfirmed = false
        SocialSession.active = true
    }

    @After fun reset() {
        SocialSession.clear()
        RuntimeEnvironment.setFontScale(1f)
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun recovery(scale: Float, local: Boolean = false) {
        val attempts = AtomicInteger()
        var confirmed = false
        RuntimeEnvironment.setFontScale(scale)
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    RestoredAccountSession(local, onConfirmed = { confirmed = true }) { path ->
                        assertEquals(if (local) "auth/local-session" else "auth/account-session", path)
                        if (attempts.incrementAndGet() == 1) throw IOException("offline")
                        if (local) """{"local_access":true}""" else """{"password_account":true}"""
                    }
                }
            }
        }
        compose.waitUntil(10000) { compose.onAllNodesWithTag("session-restore-retry").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithTag("session-restore-retry").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("session-restore-signout").performScrollTo().assertIsDisplayed()
        compose.runOnIdle {
            assertTrue(SocialSession.active)
            assertFalse(SocialSession.passwordAccountConfirmed)
            assertFalse(confirmed)
            val view = compose.activity.window.decorView
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val directory = File("build/outputs/session-recovery").apply { mkdirs() }
            val language = RuntimeEnvironment.getApplication().resources.configuration.locales[0].language
            File(directory, "$language-$scale-$local.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
        compose.onNodeWithTag("session-restore-retry").performScrollTo().performClick()
        compose.waitUntil(10000) { confirmed }
        assertEquals(2, attempts.get())
        assertEquals("saved", SocialSession.token)
        assertTrue(SocialSession.active)
    }

    @Test fun offlineRestorationKeepsCredentialsAndCanRetry() = recovery(1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun spanishRecoveryAtLargeTextKeepsControlsReachable() = recovery(2f)

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun localRealmRecoveryAtLargeTextStillRequiresConfirmation() = recovery(2f, local = true)

    @Test fun leavingScreenCancelsVerificationWithoutSigningOut() {
        val pending = CompletableDeferred<String>()
        var visible by mutableStateOf(true)
        var started = false
        var confirmed = false
        compose.setContent {
            RealityOsTheme {
                if (visible) {
                    RestoredAccountSession(false, { confirmed = true }) {
                        started = true
                        pending.await()
                    }
                }
            }
        }
        compose.waitUntil(10000) { started }
        compose.runOnIdle { visible = false }
        compose.waitForIdle()
        compose.runOnIdle { pending.complete("""{"password_account":true}""") }
        compose.waitForIdle()
        assertTrue(SocialSession.active)
        assertEquals("saved", SocialSession.token)
        assertFalse(confirmed)
    }

    @Test fun refusedAccountDoesNotAdmitUserAndSignOutRemainsExplicit() {
        var confirmed = false
        compose.setContent {
            RealityOsTheme { RestoredAccountSession(false, { confirmed = true }) { """{"password_account":false}""" } }
        }
        compose.waitUntil(10000) { compose.onAllNodesWithTag("session-restore-signout").fetchSemanticsNodes().isNotEmpty() }
        assertFalse(confirmed)
        assertTrue(SocialSession.active)
        assertFalse(SocialSession.accountEntryAllowed)
        compose.onNodeWithTag("session-restore-signout").performClick()
        assertFalse(SocialSession.active)
        assertNull(SocialSession.token)
    }
}
