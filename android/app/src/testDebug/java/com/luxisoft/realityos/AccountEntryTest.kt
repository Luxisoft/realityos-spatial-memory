package com.luxisoft.realityos

import android.app.Application
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import kotlinx.coroutines.CompletableDeferred
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "w400dp-h1200dp")
class AccountEntryTest {
    @get:Rule val compose = createComposeRule()

    @Test fun entryStartsWithLoginAndClearsPasswordOnNavigation() {
        compose.setContent { RealityOsTheme { AccountForm(onBack = {}) { _, _ -> } } }
        compose.onNodeWithTag("account-title").assertTextEquals("Sign in")
        compose.onNodeWithTag("account-email").performTextInput("person@example.test")
        compose.onNodeWithTag("account-password").performTextInput("PrivatePassword123!")
        compose.onNodeWithText("Don’t have an account? Create account").performScrollTo().performClick()
        compose.onNodeWithTag("account-title").assertTextEquals("Create account")
        compose.onNodeWithTag("account-email").assertTextContains("person@example.test")
        compose.onNodeWithTag("account-password").assertTextContains("")
        compose.onNodeWithTag("account-submit").assertIsNotEnabled()
        compose.onNodeWithText("Back to sign in").performScrollTo().performClick()
        compose.onNodeWithText("Forgot your password?").performScrollTo().performClick()
        compose.onNodeWithTag("account-title").assertTextEquals("Recover password")
        compose.onNodeWithTag("account-password").assertDoesNotExist()
    }

    @Test fun pendingRequestBlocksDuplicatesAndSuccessCanReturnToLogin() {
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
        compose.onNodeWithText("Forgot your password?").performClick()
        compose.onNodeWithTag("account-email").performTextInput("person@example.test")
        compose.onNodeWithTag("account-submit").performClick()
        compose.onNodeWithTag("account-submit").assertIsNotEnabled()
        compose.runOnIdle {
            assertEquals(1, requests)
            completion.complete(Unit)
        }
        compose.waitForIdle()
        compose.onNodeWithTag("account-message").assertIsDisplayed()
        compose.onNodeWithTag("account-submit").assertDoesNotExist()
        compose.onNodeWithText("Back to sign in").performClick()
        compose.onNodeWithTag("account-title").assertTextEquals("Sign in")
    }

    @Test fun failedRequestAllowsRetry() {
        compose.setContent { RealityOsTheme { AccountForm(onBack = {}) { _, _ -> error("offline") } } }
        compose.onNodeWithTag("account-email").performTextInput("person@example.test")
        compose.onNodeWithTag("account-password").performTextInput("PrivatePassword123!")
        compose.onNodeWithTag("account-submit").performClick()
        compose.onNodeWithTag("account-message").assertIsDisplayed()
        compose.onNodeWithTag("account-submit").assertIsEnabled()
    }
}
