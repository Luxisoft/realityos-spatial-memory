package com.luxisoft.realityos

import android.app.Application
import androidx.compose.material3.Text
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import java.net.HttpURLConnection
import java.util.concurrent.TimeUnit
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
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
@Config(application = Application::class, sdk = [35], qualifiers = "w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class AccountBiometricSetupTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()
    private val state = mutableStateOf<JSONObject?>(null)
    private val busy = mutableStateOf(false)
    private val failed = mutableStateOf(false)
    private val progress = mutableStateOf("")
    private val actions = mutableListOf<String>()
    private val originalConnection = SocialSession.openJsonConnection

    @Before fun initialize() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(if (context.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
        SocialSession.clear()
        SocialSession.openJsonConnection = { error("Unexpected network request from setup presentation") }
    }

    @After fun reset() {
        RuntimeEnvironment.setFontScale(1f)
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
        SocialSession.openJsonConnection = originalConnection
        SocialSession.clear()
    }

    private fun status(consented: Boolean = true, photo: Boolean = true, count: Int = 0, avatar: Boolean = photo) = JSONObject()
        .put("consented", consented).put("profile_photo_ready", photo).put("avatar_ready", avatar)
        .put("accepted_photos", count).put("complete", false)

    private fun show(value: JSONObject? = status(), scale: Float = 1f) {
        state.value = value
        RuntimeEnvironment.setFontScale(scale)
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    AccountBiometricSetupScreen(
                        state.value, busy.value, failed.value, progress.value,
                        { actions += "retry" }, { actions += "consent" }, { actions += "profile" },
                        { actions += "references" }, { actions += "reset" }, { actions += "complete" }, { actions += "sign-out" }
                    )
                }
            }
        }
    }

    private fun control(tag: String) = compose.onNodeWithTag(tag).performScrollTo()

    private fun capture(name: String) {
        compose.waitForIdle()
        compose.runOnIdle {
            val view = compose.activity.findViewById<android.view.View>(android.R.id.content)
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val directory = File("build/outputs/recognition-design").apply { mkdirs() }
            File(directory, "$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
        }
    }

    @Test fun consentAndBothProfilePhotosAreRequiredBeforeReferenceActions() {
        show(status(consented = false, photo = false))
        compose.onNodeWithTag("setup-profile").assertDoesNotExist()
        compose.onNodeWithTag("setup-references").assertDoesNotExist()
        compose.onNodeWithTag("setup-complete").assertDoesNotExist()
        control("setup-consent").performClick()
        compose.runOnIdle {
            assertEquals(listOf("consent"), actions)
            state.value = status(photo = true, avatar = false)
        }
        compose.onNodeWithTag("setup-consent").assertDoesNotExist()
        compose.onNodeWithTag("setup-references").assertDoesNotExist()
        control("setup-profile").assertIsEnabled().performClick()
        compose.runOnIdle { assertEquals(listOf("consent", "profile"), actions) }
    }

    @Test fun acceptedCountControlsCompletionAndLimitWithoutAutomaticSubmission() {
        show(status(count = 2))
        control("setup-complete").assertIsNotEnabled()
        control("setup-references").performClick()
        compose.runOnIdle { state.value = status(count = 3) }
        control("setup-references").assertIsEnabled()
        control("setup-complete").assertIsEnabled()
        compose.runOnIdle { assertEquals(listOf("references"), actions) }
        control("setup-complete").performClick()
        compose.runOnIdle { state.value = status(count = 25) }
        control("setup-references").assertIsNotEnabled()
        control("setup-complete").assertIsEnabled()
        control("setup-reset").performClick()
        compose.runOnIdle { assertEquals(listOf("references", "complete", "reset"), actions) }
    }

    @Test fun uploadDisablesMutationsAndShowsProgress() {
        show(status(count = 3))
        compose.runOnIdle {
            busy.value = true
            progress.value = "2 / 5"
        }
        listOf("setup-profile", "setup-references", "setup-reset", "setup-complete").forEach { control(it).assertIsNotEnabled() }
        compose.onNodeWithTag("setup-sign-out").assertIsNotEnabled()
        compose.onNodeWithText("Processing photo 2 / 5…").performScrollTo().assertIsDisplayed()
        capture("upload-en-390")
    }

    @Test fun initialLoadingAndFailureHaveDistinctRecoveryStates() {
        busy.value = true
        show(null)
        compose.onNodeWithTag("setup-loading").assertIsDisplayed()
        compose.onNodeWithTag("setup-consent").assertDoesNotExist()
        capture("loading-en-390")
        compose.runOnIdle {
            busy.value = false
            failed.value = true
        }
        compose.onNodeWithTag("setup-loading").assertDoesNotExist()
        control("setup-retry").performClick()
        compose.onNodeWithTag("setup-sign-out").performClick()
        compose.runOnIdle { assertEquals(listOf("retry", "sign-out"), actions) }
        capture("error-en-390")
    }

    @Test fun accountGateRequiresExplicitConsentAndServerConfirmedCompletion() {
        val server = MockWebServer().apply { start() }
        try {
            SocialSession.remember(JSONObject().put("access_token", "synthetic-setup-token").put("refresh_token", "synthetic-refresh-token").put("password_account", true))
            SocialSession.openJsonConnection = { path -> server.url("/$path").toUrl().openConnection() as HttpURLConnection }
            server.enqueue(MockResponse().setBody(status(consented = false, photo = false).toString()))
            compose.setContent { RealityOsTheme { AccountBiometricGate { Text("Private app content") } } }
            compose.waitUntil(10000) { compose.onAllNodesWithTag("setup-consent").fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText("Private app content").assertDoesNotExist()
            assertEquals(1, server.requestCount)
            val initial = server.takeRequest(5, TimeUnit.SECONDS)!!
            assertEquals("/faces/setup", initial.path)
            assertEquals("Bearer synthetic-setup-token", initial.getHeader("Authorization"))
            server.enqueue(MockResponse().setBody("{}"))
            server.enqueue(MockResponse().setBody(status(count = 3).toString()))
            control("setup-consent").performClick()
            compose.waitUntil(10000) { compose.onAllNodesWithTag("setup-complete").fetchSemanticsNodes().isNotEmpty() }
            val consent = server.takeRequest(5, TimeUnit.SECONDS)!!
            assertEquals("/faces/consent", consent.path)
            assertTrue(JSONObject(consent.body.readUtf8()).getBoolean("confirm"))
            assertEquals("/faces/setup", server.takeRequest(5, TimeUnit.SECONDS)!!.path)
            compose.onNodeWithText("Private app content").assertDoesNotExist()
            server.enqueue(MockResponse().setBody("{}"))
            server.enqueue(MockResponse().setBody(status(count = 3).put("complete", true).toString()))
            control("setup-complete").performClick()
            compose.waitUntil(10000) { compose.onAllNodesWithText("Private app content").fetchSemanticsNodes().isNotEmpty() }
            assertEquals("/faces/setup/complete", server.takeRequest(5, TimeUnit.SECONDS)!!.path)
            assertEquals("/faces/setup", server.takeRequest(5, TimeUnit.SECONDS)!!.path)
            compose.onNodeWithTag("account-biometric-setup").assertDoesNotExist()
        } finally {
            server.shutdown()
        }
    }

    private fun gallery(name: String, scale: Float = 1f) {
        show(status(consented = false, photo = false), scale)
        capture("consent-$name")
        control("setup-consent").assertIsDisplayed()
        capture("consent-action-$name")
        compose.runOnIdle { state.value = status(photo = false) }
        control("setup-profile").assertIsDisplayed()
        capture("profile-$name")
        compose.runOnIdle { state.value = status(count = 1) }
        control("setup-references").assertIsDisplayed()
        capture("references-$name")
        control("setup-complete").assertIsDisplayed().assertIsNotEnabled()
        compose.runOnIdle { state.value = status(count = 3) }
        control("setup-complete").assertIsDisplayed().assertIsEnabled()
        capture("ready-$name")
    }

    @Test fun english390() = gallery("en-390")

    @Test
    @Config(qualifiers = "es-w390dp-h844dp-mdpi")
    fun spanish390() = gallery("es-390")

    @Test
    @Config(qualifiers = "es-w320dp-h720dp-mdpi")
    fun spanishNarrowWithLargeText() = gallery("es-320-text200", 2f)

    @Test
    @Config(qualifiers = "w480dp-h900dp-mdpi")
    fun englishWide480() = gallery("en-480")
}
