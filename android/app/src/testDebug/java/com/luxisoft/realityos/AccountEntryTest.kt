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
        tap("account-correct-email")
        capture("correct-email-$prefix")
        compose.onNodeWithTag("account-email").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("account-password").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("account-back").performClick()
        tap("account-resend")
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
        compose.onNodeWithTag("app-notice").assertExists()
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

    private fun fillRegistration() {
        tap("account-register")
        compose.onNodeWithTag("account-name").performTextInput("Ana Solis")
        compose.onNodeWithTag("account-username").performTextInput("ana.solis")
        compose.onNodeWithTag("account-email").performTextInput("initial@example.test")
        compose.onNodeWithTag("account-password").performTextInput("SecurePassword123!")
    }

    @Test fun changingEmailReplacesRegistrationAndResendsOnlyToTheNewAddress() {
        val actions = mutableListOf<Pair<String, String>>()
        compose.setContent {
            RealityOsTheme {
                AccountForm(onBack = {}) { mode, payload ->
                    actions.add(mode to payload.getString("email"))
                    if (mode == "change-pending-email") {
                        assertEquals("ana.solis", payload.getString("username"))
                        assertEquals("SecurePassword123!", payload.getString("password"))
                    }
                }
            }
        }
        fillRegistration()
        tap("account-submit")
        tap("account-edit-email")
        compose.onNodeWithTag("account-title").assertTextEquals("Change your registration email")
        compose.onNodeWithTag("account-identifier").assertTextContains("ana.solis")
        compose.onNodeWithTag("account-password").assert(SemanticsMatcher.expectValue(androidx.compose.ui.semantics.SemanticsProperties.EditableText, androidx.compose.ui.text.AnnotatedString("")))
        compose.onNodeWithTag("account-email").performTextReplacement("corrected@example.test")
        compose.onNodeWithTag("account-password").performTextInput("SecurePassword123!")
        tap("account-submit")
        compose.onNodeWithTag("account-recipient").assertTextEquals("corrected@example.test")
        tap("account-send-again")
        compose.runOnIdle {
            assertEquals(listOf("register" to "initial@example.test", "change-pending-email" to "corrected@example.test", "resend-confirmation" to "corrected@example.test"), actions)
        }
    }

    @Test fun duplicateEmailOffersRecoveryAndKeepsTheRegisteredAddress() {
        val actions = mutableListOf<String>()
        compose.setContent {
            RealityOsTheme {
                AccountForm(onBack = {}) { mode, payload ->
                    actions.add(mode)
                    if (mode == "register") throw AccountConflict(setOf("email"))
                    assertEquals("initial@example.test", payload.getString("email"))
                }
            }
        }
        fillRegistration()
        tap("account-submit")
        compose.onNodeWithTag("account-email-help", useUnmergedTree = true).assertTextEquals("This email is already registered.")
        compose.onNodeWithTag("account-submit").assertIsNotEnabled()
        compose.onNodeWithTag("account-conflict").performScrollTo()
        capture("duplicate-email-en-390")
        tap("account-conflict-recover")
        compose.onNodeWithTag("account-title").assertTextEquals("Recover your access")
        tap("account-submit")
        compose.runOnIdle { assertEquals(listOf("register", "forgot-password"), actions) }
    }

    @Test fun duplicateUsernameCanBeReplacedBeforeAnotherRegistrationAttempt() {
        var requests = 0
        compose.setContent {
            RealityOsTheme {
                AccountForm(onBack = {}) { _, payload ->
                    requests++
                    if (payload.getString("username") == "ana.solis") throw AccountConflict(setOf("username"))
                    assertEquals("ana.other", payload.getString("username"))
                }
            }
        }
        fillRegistration()
        tap("account-submit")
        compose.onNodeWithTag("account-submit").assertIsNotEnabled()
        compose.runOnIdle { assertEquals(1, requests) }
        tap("account-conflict-edit")
        compose.onNodeWithTag("account-email").assertTextContains("initial@example.test")
        compose.onNodeWithTag("account-username").performTextInput("ana.other")
        tap("account-submit")
        compose.onNodeWithTag("account-title").assertTextEquals("Check your email")
        compose.runOnIdle { assertEquals(2, requests) }
    }

    @Test fun duplicatePendingAccountCanRequestConfirmationInsteadOfRegisteringAgain() {
        val actions = mutableListOf<String>()
        compose.setContent {
            RealityOsTheme {
                AccountForm(onBack = {}) { mode, _ ->
                    actions.add(mode)
                    if (mode == "register") throw AccountConflict(setOf("email", "username"))
                }
            }
        }
        fillRegistration()
        tap("account-submit")
        tap("account-conflict-resend")
        compose.onNodeWithTag("account-title").assertTextEquals("Confirm your email")
        tap("account-submit")
        compose.runOnIdle { assertEquals(listOf("register", "resend-confirmation"), actions) }
    }

    @Test fun rejectedRegistrationUsernameDoesNotCarryIntoEmailCorrection() {
        val actions = mutableListOf<String>()
        compose.setContent {
            RealityOsTheme {
                AccountForm(onBack = {}) { mode, payload ->
                    actions.add(mode)
                    if (mode == "register") throw AccountConflict(setOf("email"))
                    if (mode == "change-pending-email") {
                        assertEquals("initial@example.test", payload.getString("username"))
                        assertEquals("corrected@example.test", payload.getString("email"))
                    }
                }
            }
        }
        fillRegistration()
        tap("account-submit")
        tap("account-conflict-resend")
        tap("account-submit")
        tap("account-edit-email")
        compose.onNodeWithTag("account-identifier").assertTextContains("initial@example.test")
        compose.onNodeWithTag("account-email").performTextReplacement("corrected@example.test")
        compose.onNodeWithTag("account-password").performTextInput("SecurePassword123!")
        tap("account-submit")
        compose.onNodeWithTag("account-recipient").assertTextEquals("corrected@example.test")
        tap("account-edit-email")
        compose.onNodeWithTag("account-identifier").assertTextContains("corrected@example.test")
        compose.runOnIdle { assertEquals(listOf("register", "resend-confirmation", "change-pending-email"), actions) }
    }

    @Test fun duplicateUsernameOpensCorrectionForThatExistingAccount() {
        compose.setContent {
            RealityOsTheme {
                AccountForm(onBack = {}) { _, _ -> throw AccountConflict(setOf("username")) }
            }
        }
        fillRegistration()
        tap("account-submit")
        tap("account-conflict-correct")
        compose.onNodeWithTag("account-identifier").assertTextContains("ana.solis")
        compose.onNodeWithTag("account-email").assertTextContains("initial@example.test")
        compose.onNodeWithTag("account-password").assertTextContains("")
    }

    @Test fun correctionExplainsInvalidCredentialsAndRecoveryUsesExistingAddress() {
        compose.setContent {
            RealityOsTheme {
                AccountForm(onBack = {}) { _, _ -> throw AccountFailure(R.string.account_correction_credentials_error) }
            }
        }
        tap("account-resend")
        compose.onNodeWithTag("account-email").performTextInput("initial@example.test")
        tap("account-correct-email")
        compose.onNodeWithTag("account-email").performTextReplacement("corrected@example.test")
        compose.onNodeWithTag("account-password").performTextInput("WrongPassword123!")
        tap("account-submit")
        compose.onNodeWithText(compose.activity.getString(R.string.account_correction_credentials_error)).assertExists()
        compose.onNodeWithTag("account-identifier").assertTextContains("initial@example.test")
        compose.onNodeWithTag("account-email").assertTextContains("corrected@example.test")
        compose.onNodeWithTag("app-notice").assertIsDisplayed()
        capture("correction-credentials-en-390")
        tap("account-recover")
        compose.onNodeWithTag("account-email").assertTextContains("initial@example.test")
    }
}
