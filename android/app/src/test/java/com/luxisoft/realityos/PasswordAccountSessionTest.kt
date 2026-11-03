package com.luxisoft.realityos

import org.json.JSONObject
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.assertEquals
import org.junit.Test

@org.junit.runner.RunWith(org.robolectric.RobolectricTestRunner::class)
@org.robolectric.annotation.Config(sdk = [35], application = android.app.Application::class)
class PasswordAccountSessionTest {
    @Test
    fun `expired access token refreshes before confirming restored password account`() {
        val original = SocialSession.openJsonConnection
        val server = okhttp3.mockwebserver.MockWebServer()
        server.start()
        try {
            SocialSession.clear()
            SocialSession.remember(JSONObject().put("access_token", "expired").put("refresh_token", "refresh-first").put("password_account", true))
            SocialSession.passwordAccountConfirmed = false
            SocialSession.openJsonConnection = { path -> server.url("/$path").toUrl().openConnection() as java.net.HttpURLConnection }
            server.enqueue(okhttp3.mockwebserver.MockResponse().setResponseCode(401))
            server.enqueue(okhttp3.mockwebserver.MockResponse().setBody("""{"access_token":"renewed","refresh_token":"refresh-next"}"""))
            server.enqueue(okhttp3.mockwebserver.MockResponse().setBody("""{"password_account":true}"""))
            assertTrue(JSONObject(SocialSession.request("auth/account-session")).getBoolean("password_account"))
            assertEquals("/auth/account-session", server.takeRequest().path)
            val renewal = server.takeRequest()
            assertEquals("/auth/refresh", renewal.path)
            assertEquals("refresh-first", JSONObject(renewal.body.readUtf8()).getString("refresh_token"))
            assertEquals("Bearer renewed", server.takeRequest().getHeader("Authorization"))
            assertEquals("renewed", SocialSession.token)
        } finally {
            SocialSession.openJsonConnection = original
            SocialSession.clear()
            server.shutdown()
        }
    }
    @Test
    fun `confirmed password session is independent from local debug access`() {
        SocialSession.clear()
        SocialSession.remember(JSONObject().put("access_token", "a").put("refresh_token", "b").put("password_account", true))
        assertTrue(SocialSession.accountEntryAllowed)
        assertFalse(SocialSession.localAccount)
        SocialSession.clear()
        assertFalse(SocialSession.accountEntryAllowed)
    }

    @Test
    fun `unconfirmed restored flag cannot admit account`() {
        SocialSession.clear()
        SocialSession.passwordAccount = true
        assertFalse(SocialSession.accountEntryAllowed)
        SocialSession.clear()
    }
}
