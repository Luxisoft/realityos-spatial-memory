package com.luxisoft.realityos

import android.app.Application
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import kotlinx.coroutines.CompletableDeferred
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
class AccountEntryTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    private fun tap(tag: String) = compose.onNodeWithTag(tag).performScrollTo().performClick()
    private fun capture(name: String) {
        compose.waitForIdle()
        val directory = File("build/outputs/account-design").apply { mkdirs() }
        compose.runOnIdle {
            val view = compose.activity.findViewById<android.view.View>(android.R.id.content)
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            File(directory, "$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
        }
    }

    @Test fun navigationPreservesEmailAndClearsPassword() {
        compose.setContent { RealityOsTheme { AccountForm(onBack = {}) { _, _ -> } } }
        compose.onNodeWithTag("account-title").assertTextEquals("Sign in")
        compose.onNodeWithTag("account-email").performTextInput("person@example.test")
        compose.onNodeWithTag("account-password").performTextInput("PrivatePassword123!")
        tap("account-register")
        compose.onNodeWithTag("account-title").assertTextEquals("Create your account")
        compose.onNodeWithTag("account-email").assertTextContains("person@example.test")
        compose.onNodeWithTag("account-password").assert(SemanticsMatcher.expectValue(androidx.compose.ui.semantics.SemanticsProperties.EditableText, androidx.compose.ui.text.AnnotatedString("")))
        tap("account-submit")
        compose.onNodeWithTag("account-name-help", useUnmergedTree = true).assertExists()
        compose.onNodeWithTag("account-back").performClick()
        tap("account-recover")
        compose.onNodeWithTag("account-title").assertTextEquals("Recover your access")
        compose.onNodeWithTag("account-password").assertDoesNotExist()
    }

    @Test fun pendingRequestBlocksDuplicatesAndConfirmationResends() {
        val completion = CompletableDeferred<Unit>()
        var requests = 0
        compose.setContent {
            RealityOsTheme {
                AccountForm(onBack = {}) { mode, payload ->
                    assertEquals("forgot-password", mode)
                    assertEquals("person@example.test", payload.getString("email"))
                    requests++
                    completion.await()
                }
            }
        }
        tap("account-recover")
        compose.onNodeWithTag("account-email").performTextInput("person@example.test")
        tap("account-submit")
        compose.onNodeWithTag("account-submit").assertIsNotEnabled()
        capture("loading-en-390")
        compose.runOnIdle {
            assertEquals(1, requests)
            completion.complete(Unit)
        }
        compose.onNodeWithTag("account-title").assertTextEquals("Check your email")
        compose.onNodeWithTag("account-recipient").assertTextEquals("person@example.test")
        tap("account-send-again")
        compose.runOnIdle { assertEquals(2, requests) }
        compose.onNodeWithTag("account-resend-status").assertExists()
        tap("account-edit-email")
        compose.onNodeWithTag("account-email").assertTextContains("person@example.test")
    }

    private fun gallery(prefix: String, scale: Float = 1f) {
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme { AccountForm(onBack = {}) { _, _ -> } }
            }
        }
        capture("login-$prefix")
        tap("account-register")
        capture("register-$prefix")
        compose.onNodeWithTag("account-back").performClick()
        tap("account-recover")
        capture("recover-$prefix")
        compose.onNodeWithTag("account-email").performTextInput("ana@example.test")
        tap("account-submit")
        capture("sent-$prefix")
        tap("account-submit")
        tap("account-resend")
        capture("resend-$prefix")
        // All actions remain reachable at large font sizes and narrow widths.
        tap("account-submit")
        compose.onNodeWithTag("account-title").assertExists()
    }

    @Test fun visualEnglish390() = gallery("en-390")

    @Test
    @Config(qualifiers = "es-w390dp-h844dp-mdpi")
    fun visualSpanish390() = gallery("es-390")

    @Test
    @Config(qualifiers = "w320dp-h720dp-mdpi")
    fun narrowLayout() = gallery("en-320")

    @Test
    @Config(qualifiers = "w480dp-h900dp-mdpi")
    fun largeLayout() = gallery("en-480")

    @Test
    @Config(qualifiers = "es-w320dp-h720dp-mdpi")
    fun enlargedText() = gallery("es-320-text200", 2f)

    @Test fun errorsHaveARecoveryAction() {
        compose.setContent { RealityOsTheme { AccountForm(onBack = {}) { _, _ -> error("offline") } } }
        tap("account-submit")
        compose.onNodeWithTag("account-email").assertIsFocused()
        compose.onNodeWithTag("account-email-help", useUnmergedTree = true).assertTextEquals("Enter your username or email.")
        compose.onNodeWithTag("account-email").performTextInput("person@example.test")
        compose.onNodeWithTag("account-password").performTextInput("PrivatePassword123!")
        tap("account-password-visibility")
        compose.onNodeWithContentDescription("Hide").assertExists()
        tap("account-submit")
        compose.onNodeWithTag("account-message").assertExists()
        compose.onNodeWithTag("account-submit").assertIsEnabled()
        capture("error-en-390")
    }

    @Test fun registrationSendsDetailsAndOffersConfirmationResend() {
        val actions = mutableListOf<String>()
        compose.setContent {
            RealityOsTheme {
                AccountForm(onBack = {}) { mode, payload ->
                    actions.add(mode)
                    assertEquals("ana@example.test", payload.getString("email"))
                    if (mode == "register") {
                        assertEquals("ana.solis", payload.getString("username"))
                        assertEquals("Ana Solis", payload.getString("display_name"))
                    }
                }
            }
        }
        tap("account-register")
        compose.onNodeWithTag("account-name").performTextInput("Ana Solis")
        compose.onNodeWithTag("account-username").performTextInput("ana.solis")
        compose.onNodeWithTag("account-email").performTextInput("ana@example.test")
        compose.onNodeWithTag("account-password").performTextInput("SecurePassword123!")
        tap("account-submit")
        compose.onNodeWithTag("account-recipient").assertTextEquals("ana@example.test")
        tap("account-send-again")
        compose.runOnIdle { assertEquals(listOf("register", "resend-confirmation"), actions) }
    }

    @Test fun keyboardInsetsKeepTheSubmitActionReachable() {
        compose.setContent { RealityOsTheme { AccountForm(onBack = {}) { _, _ -> } } }
        compose.onNodeWithTag("account-email").performClick()
        compose.runOnIdle {
            val insets = android.view.WindowInsets.Builder()
                .setInsets(android.view.WindowInsets.Type.ime(), android.graphics.Insets.of(0, 0, 0, 300))
                .setVisible(android.view.WindowInsets.Type.ime(), true).build()
            compose.activity.window.decorView.dispatchApplyWindowInsets(insets)
        }
        compose.onNodeWithTag("account-submit").performScrollTo().assertIsDisplayed()
        capture("keyboard-en-390")
    }
}
