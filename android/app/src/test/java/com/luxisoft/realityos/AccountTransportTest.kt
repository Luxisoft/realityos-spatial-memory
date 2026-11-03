package com.luxisoft.realityos

import android.app.Application
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL
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
    @Test fun imageQueryWaitsForLongAnalysisWhileOrdinaryUploadsKeepTheirLimit() {
        class DelayedConnection : HttpURLConnection(URL("https://example.test/v1/query")) {
            val body = ByteArrayOutputStream()
            var disconnected = false
            override fun connect() { }
            override fun disconnect() {
                disconnected = true
            }
            override fun usingProxy() = false
            override fun getOutputStream() = body
            override fun getResponseCode(): Int {
                // Simulate a provider response after 90 seconds without sleeping
                // or allowing a unit test to contact the production server.
                if (readTimeout < 90000) throw SocketTimeoutException("Analysis still running")
                return 200
            }
            override fun getInputStream() = ByteArrayInputStream("{}".toByteArray())
        }
        val original = SocialSession.openJsonConnection
        val connections = mutableListOf<DelayedConnection>()
        try {
            SocialSession.clear()
            SocialSession.token = "synthetic-session"
            SocialSession.openJsonConnection = { DelayedConnection().also { connections.add(it) } }
            val response = SocialSession.requestMultipart("queries/image", mapOf("workspace_id" to "qa"), byteArrayOf(1, 2, 3), "probe.png", "image/png", "image")
            assertEquals("{}", response)
            assertEquals("Bearer synthetic-session", connections[0].getRequestProperty("Authorization"))
            assertTrue(connections[0].body.toString("UTF-8").contains("name=\"image\"; filename=\"probe.png\""))
            assertTrue(connections[0].disconnected)
            assertThrows(SocketTimeoutException::class.java) {
                SocialSession.requestMultipart("me/publication-uploads", emptyMap(), byteArrayOf(1), "upload.png", "image/png")
            }
            assertTrue(connections[1].disconnected)
        } finally {
            SocialSession.openJsonConnection = original
            SocialSession.clear()
        }
    }

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

    @Test fun correctionErrorsKeepTheirCauseAndDoNotClearAnExistingSession() {
        val original = SocialSession.openJsonConnection
        val server = MockWebServer()
        server.start()
        try {
            SocialSession.clear()
            SocialSession.token = "synthetic-session"
            SocialSession.openJsonConnection = { path -> server.url("/$path").toUrl().openConnection() as HttpURLConnection }
            val expected = mapOf(
                401 to R.string.account_correction_credentials_error,
                409 to R.string.account_correction_unavailable,
                429 to R.string.account_too_many_attempts,
                503 to R.string.account_delivery_failed
            )
            expected.forEach { (status, message) ->
                server.enqueue(MockResponse().setResponseCode(status).setBody("""{"detail":"private server explanation"}"""))
                val failure = assertThrows(AccountFailure::class.java) {
                    SocialSession.request("auth/change-pending-email", JSONObject().put("username", "initial@example.test"))
                }
                assertEquals(message, failure.messageResource)
                assertEquals("synthetic-session", SocialSession.token)
                assertEquals("/auth/change-pending-email", server.takeRequest().path)
            }
            assertNull(accountFailure("auth/facebook", 401))
            assertNull(accountFailure("auth/account-session", 401))
            assertNull(accountFailure("gallery", 503))
        } finally {
            SocialSession.openJsonConnection = original
            SocialSession.clear()
            server.shutdown()
        }
    }
}
