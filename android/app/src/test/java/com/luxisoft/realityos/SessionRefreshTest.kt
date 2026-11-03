package com.luxisoft.realityos

import android.app.Application
import java.io.File
import java.net.HttpURLConnection
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], application = Application::class)
class SessionRefreshTest {
    private val server = MockWebServer()
    private val original = SocialSession.openJsonConnection
    private val executor = Executors.newFixedThreadPool(2)

    @Before fun start() {
        LocalizedText.initialize(RuntimeEnvironment.getApplication())
        server.start()
        SocialSession.clear()
        signIn("expired", "refresh-first")
        SocialSession.openJsonConnection = { path -> server.url("/$path").toUrl().openConnection() as HttpURLConnection }
    }

    @After fun stop() {
        executor.shutdownNow()
        executor.awaitTermination(10, TimeUnit.SECONDS)
        SocialSession.openJsonConnection = original
        SocialSession.clear()
        server.shutdown()
    }

    private fun signIn(access: String, refresh: String) {
        SocialSession.remember(JSONObject().put("access_token", access).put("refresh_token", refresh).put("password_account", true))
        SocialSession.active = true
    }

    private fun simultaneousRefresh(background: () -> String) {
        val expiredRequests = CountDownLatch(2)
        val refreshes = AtomicInteger()
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                if (request.path == "/auth/refresh") {
                    val count = refreshes.incrementAndGet()
                    return if (count == 1) {
                        MockResponse().setBody("""{"access_token":"renewed","refresh_token":"refresh-next"}""").setBodyDelay(250, TimeUnit.MILLISECONDS)
                    } else {
                        MockResponse().setResponseCode(401)
                    }
                }
                if (request.getHeader("Authorization") == "Bearer expired") {
                    expiredRequests.countDown()
                    check(expiredRequests.await(5, TimeUnit.SECONDS))
                    return MockResponse().setResponseCode(401)
                }
                return if (request.getHeader("Authorization") == "Bearer renewed") MockResponse().setBody("[]") else MockResponse().setResponseCode(401)
            }
        }
        val profile = executor.submit<String> { background() }
        val connections = executor.submit<String> { SocialSession.requestJson(STORAGE_BASE, "GET") }
        assertEquals("[]", connections.get(10, TimeUnit.SECONDS))
        assertEquals("[]", profile.get(10, TimeUnit.SECONDS))
        assertEquals(1, refreshes.get())
        assertEquals("renewed", SocialSession.token)
        assertTrue(SocialSession.active)
        assertTrue(SocialSession.accountEntryAllowed)
    }

    @Test fun openingConnectionsDuringProfileRefreshRotatesOnlyOnce() = simultaneousRefresh { SocialSession.request("me/profile") }

    @Test fun openingConnectionsDuringPhotoUploadRotatesOnlyOnce() = simultaneousRefresh {
        SocialSession.requestMultipart("me/publication-uploads", emptyMap(), byteArrayOf(1, 2, 3), "photo.png", "image/png")
    }

    @Test fun openingConnectionsDuringVideoUploadRotatesOnlyOnce() {
        val video = File.createTempFile("session-upload", ".mp4")
        try {
            video.writeBytes(byteArrayOf(1, 2, 3))
            simultaneousRefresh { SocialSession.requestMultipartFile("me/publication-uploads", emptyMap(), video, "video/mp4") }
        } finally {
            video.delete()
        }
    }

    @Test fun connectionErrorsKeepSessionButRevokedRefreshSignsOut() {
        for (status in listOf(403, 500, 503)) {
            server.enqueue(MockResponse().setResponseCode(status))
            assertThrows(IllegalStateException::class.java) { SocialSession.requestJson(STORAGE_BASE, "GET") }
            assertEquals("expired", SocialSession.token)
            assertTrue(SocialSession.active)
        }
        server.enqueue(MockResponse().setResponseCode(401))
        server.enqueue(MockResponse().setResponseCode(401))
        assertThrows(IllegalStateException::class.java) { SocialSession.requestJson(STORAGE_BASE, "GET") }
        assertNull(SocialSession.token)
        assertFalse(SocialSession.active)
    }

    @Test fun previousAccountResponseCannotClearOrQueryTheNewAccount() {
        val started = CountDownLatch(1)
        val release = CountDownLatch(1)
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                started.countDown()
                check(release.await(5, TimeUnit.SECONDS))
                return MockResponse().setResponseCode(401)
            }
        }
        val pending = executor.submit<Boolean> {
            runCatching { SocialSession.requestJson(STORAGE_BASE, "GET") }.isFailure
        }
        assertTrue(started.await(5, TimeUnit.SECONDS))
        SocialSession.clear()
        signIn("other-account", "other-refresh")
        release.countDown()
        assertTrue(pending.get(10, TimeUnit.SECONDS))
        assertEquals("other-account", SocialSession.token)
        assertTrue(SocialSession.active)
        assertEquals(1, server.requestCount)
    }

    @Test fun logoutDuringRenewalCannotRestoreThePreviousAccount() {
        val renewing = CountDownLatch(1)
        val release = CountDownLatch(1)
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                if (request.path != "/auth/refresh") return MockResponse().setResponseCode(401)
                renewing.countDown()
                check(release.await(5, TimeUnit.SECONDS))
                return MockResponse().setBody("""{"access_token":"renewed","refresh_token":"refresh-next"}""")
            }
        }
        val pending = executor.submit<Boolean> {
            runCatching { SocialSession.requestJson(STORAGE_BASE, "GET") }.isFailure
        }
        assertTrue(renewing.await(5, TimeUnit.SECONDS))
        SocialSession.clear()
        release.countDown()
        assertTrue(pending.get(10, TimeUnit.SECONDS))
        assertNull(SocialSession.token)
        assertFalse(SocialSession.active)
        assertEquals(2, server.requestCount)
    }

    @Test fun temporaryRefreshFailureCanBeRetriedWithoutLoggingOut() {
        server.enqueue(MockResponse().setResponseCode(401))
        server.enqueue(MockResponse().setResponseCode(503))
        assertThrows(IllegalStateException::class.java) { SocialSession.requestJson(STORAGE_BASE, "GET") }
        assertEquals("expired", SocialSession.token)
        assertTrue(SocialSession.active)
        server.enqueue(MockResponse().setResponseCode(401))
        server.enqueue(MockResponse().setBody("""{"access_token":"renewed","refresh_token":"refresh-next"}"""))
        server.enqueue(MockResponse().setBody("[]"))
        assertEquals("[]", SocialSession.requestJson(STORAGE_BASE, "GET"))
        assertTrue(SocialSession.active)
    }
}
