package com.luxisoft.realityos

import android.app.Application
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import com.luxisoft.realityos.host.RealityDrawer
import java.net.HttpURLConnection
import kotlinx.coroutines.launch
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35])
class LocalLogoutTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    private fun logout(status: Int) {
        LocalizedText.initialize(compose.activity)
        val server = MockWebServer().apply { start() }
        val original = SocialSession.openJsonConnection
        try {
            SocialSession.clear()
            SocialSession.workspaceId = "workspace"
            SocialSession.remember(JSONObject().put("access_token", "local-access").put("refresh_token", "local-refresh").put("local_access", true))
            SocialSession.active = true
            SocialSession.openJsonConnection = { server.url("/$it").toUrl().openConnection() as HttpURLConnection }
            server.enqueue(MockResponse().setResponseCode(status).setBody("{}"))
            val account = JSONObject().put("id", "one").put("username", "one").put("display_name", "Alex Rivera").put("workspace_name", "Pacific Ridge")
            compose.setContent {
                val scope = rememberCoroutineScope()
                RealityOsTheme {
                    if (SocialSession.active) {
                        RealityDrawer(RealityExperienceStore(compose.activity), onAbout = {}, onLogout = { scope.launch { SocialSession.signOut() } })
                    } else {
                        LocalAccountChooser(listOf(account), false, false, {}, {})
                    }
                }
            }
            compose.onNodeWithTag("drawer-logout").performTouchInput { click() }
            compose.waitUntil(10_000) { !SocialSession.active }
            compose.onNodeWithTag("local-account-one").assertIsDisplayed()
            assertFalse(compose.activity.isFinishing)
            assertNull(SocialSession.token)
            assertNull(SocialSession.workspaceId)
            assertNull(SocialSession.loginNotice)
            assertFalse(SocialSession.localAccount)
            assertEquals("/auth/logout", server.takeRequest().path)
            assertEquals(1, server.requestCount)
        } finally {
            SocialSession.openJsonConnection = original
            SocialSession.clear()
            server.shutdown()
        }
    }

    @Test fun successfulLogoutReturnsToChooserWithoutFacebookInitialization() = logout(200)

    @Test fun unavailableServerStillClearsLocalSessionAndReturnsToChooser() = logout(503)

    @Test fun rejectedAccessStillReturnsToChooserWithoutAnExpirationNotice() = logout(401)
}
