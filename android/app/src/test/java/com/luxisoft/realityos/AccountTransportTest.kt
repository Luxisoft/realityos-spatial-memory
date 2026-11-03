package com.luxisoft.realityos

import android.app.Application
import java.net.HttpURLConnection
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], application = Application::class)
class AccountTransportTest {
    @Test fun duplicateRegistrationRetainsFieldErrorsAndCorrectionUsesChosenLanguage() {
        val original = SocialSession.openJsonConnection
        val language = AccountRequestLanguage.value
        val server = MockWebServer()
        server.start()
        try {
            SocialSession.clear()
            SocialSession.openJsonConnection = { path -> server.url("/$path").toUrl().openConnection() as HttpURLConnection }
            server.enqueue(MockResponse().setResponseCode(409).setBody("""{"detail":{"code":"registration_conflict","fields":["email"]}}"""))
            val conflict = assertThrows(AccountConflict::class.java) { SocialSession.request("auth/register", JSONObject()) }
            assertEquals(setOf("email"), conflict.fields)
            assertEquals("/auth/register", server.takeRequest().path)
            AccountRequestLanguage.value = "es"
            server.enqueue(MockResponse().setResponseCode(202).setBody("""{"status":"confirmation_sent"}"""))
            val payload = JSONObject().put("username", "pending.person").put("email", "corrected@example.test").put("password", "SyntheticPassword123!")
            SocialSession.request("auth/change-pending-email", payload)
            val request = server.takeRequest()
            assertEquals("/auth/change-pending-email", request.path)
            assertEquals("es", request.getHeader("Accept-Language"))
            assertEquals("corrected@example.test", JSONObject(request.body.readUtf8()).getString("email"))
        } finally {
            AccountRequestLanguage.value = language
            SocialSession.openJsonConnection = original
            SocialSession.clear()
            server.shutdown()
        }
    }

    @Test fun otherErrorsAreNotMisreportedAsDuplicates() {
        assertNull(accountConflict("auth/login", 409, "{}"))
        assertNull(accountConflict("auth/register", 503, "{}"))
        assertNull(accountConflict("auth/change-pending-email", 409, """{"detail":"Only an unconfirmed registration can change its email here."}"""))
        assertEquals(setOf("email", "username"), accountConflict("auth/register", 409, """{"detail":"This email or username cannot be registered."}""")!!.fields)
    }
}
