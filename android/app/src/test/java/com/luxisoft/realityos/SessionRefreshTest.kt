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
        assertFalse(SocialSession.loginNotice.isNullOrBlank())
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

    @Test fun allSectionsKeepSessionForPermissionValidationAndServerErrors() {
        val paths = listOf("me/profile", "gallery/page", "groups", "workspaces/work/records", "chat/history", "queries", STORAGE_BASE, "me/publication-uploads/one")
        for (path in paths) {
            for (status in listOf(403, 404, 409, 422, 429, 500, 503)) {
                server.enqueue(MockResponse().setResponseCode(status))
                assertThrows(IllegalStateException::class.java) { SocialSession.request(path) }
                assertTrue("$path / $status", SocialSession.active)
                assertEquals("expired", SocialSession.token)
            }
        }
    }

    @Test fun privateAuthRoutesRenewBeforeRestoringAccount() {
        for (path in listOf("auth/me", "auth/local-session", "auth/account-session", "auth/account-capture-profile")) {
            signIn("expired", "refresh-first")
            server.enqueue(MockResponse().setResponseCode(401))
            server.enqueue(MockResponse().setBody("""{"access_token":"renewed","refresh_token":"refresh-next"}"""))
            server.enqueue(MockResponse().setBody("{}"))
            assertEquals("{}", SocialSession.request(path))
            assertEquals("renewed", SocialSession.token)
            assertTrue(SocialSession.active)
        }
    }

    @Test fun resourceRejectionAfterValidRenewalDoesNotRevokeWholeSession() {
        val actions = listOf<() -> Any>(
            { SocialSession.request("me/profile") },
            { SocialSession.requestMultipart("me/publication-uploads", emptyMap(), byteArrayOf(1), "a.png", "image/png") },
            { storageDownload("$STORAGE_BASE/one/content", SocialSession.identity) }
        )
        for (action in actions) {
            signIn("expired", "refresh-first")
            server.enqueue(MockResponse().setResponseCode(401))
            server.enqueue(MockResponse().setBody("""{"access_token":"renewed","refresh_token":"refresh-next"}"""))
            server.enqueue(MockResponse().setResponseCode(401))
            assertThrows(IllegalStateException::class.java) { action() }
            assertEquals("renewed", SocialSession.token)
            assertTrue(SocialSession.active)
            server.enqueue(MockResponse().setBody("{}"))
            assertEquals("{}", SocialSession.request("me/profile"))
        }
    }

    @Test fun downloadRefreshesWithinSameAccountAndRejectsPreviousAccount() {
        val identity = SocialSession.identity
        server.enqueue(MockResponse().setResponseCode(401))
        server.enqueue(MockResponse().setBody("""{"access_token":"renewed","refresh_token":"refresh-next"}"""))
        server.enqueue(MockResponse().setBody("image bytes"))
        assertEquals("image bytes", storageDownload("$STORAGE_BASE/one/content", identity).decodeToString())
        assertTrue(SocialSession.isCurrent(identity))
        assertEquals("renewed", SocialSession.token)
        signIn("other-account", "other-refresh")
        assertThrows(IllegalStateException::class.java) { storageDownload("$STORAGE_BASE/one/content", identity) }
        SocialSession.clearIfCurrent(identity)
        assertEquals("other-account", SocialSession.token)
        assertEquals(3, server.requestCount)
    }

    @Test fun slowSectionDoesNotBlockAnotherSectionOrResendUnderAnotherAccount() {
        val arrived = CountDownLatch(2)
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                arrived.countDown()
                check(arrived.await(5, TimeUnit.SECONDS))
                return MockResponse().setBody("{}")
            }
        }
        val first = executor.submit<String> { SocialSession.request("me/profile") }
        val second = executor.submit<String> { SocialSession.request("groups") }
        assertEquals("{}", first.get(10, TimeUnit.SECONDS))
        assertEquals("{}", second.get(10, TimeUnit.SECONDS))
        assertTrue(SocialSession.active)
    }

    @Test fun networkTimeoutsDoNotEraseSessionAcrossTransportTypes() {
        val previous = SocialSession.openJsonConnection
        SocialSession.openJsonConnection = {
            object : HttpURLConnection(java.net.URL("https://example.test/v1/resource")) {
                override fun connect() = Unit
                override fun disconnect() = Unit
                override fun usingProxy() = false
                override fun getOutputStream() = java.io.ByteArrayOutputStream()
                override fun getResponseCode(): Int = throw java.net.SocketTimeoutException("offline")
            }
        }
        try {
            val actions = listOf<() -> Any>(
                { SocialSession.request("groups") },
                { SocialSession.requestMultipart("me/publication-uploads", emptyMap(), byteArrayOf(1), "a.png", "image/png") },
                { storageDownload("$STORAGE_BASE/one/content", SocialSession.identity) }
            )
            for (action in actions) {
                assertThrows(java.net.SocketTimeoutException::class.java) { action() }
                assertTrue(SocialSession.active)
                assertEquals("expired", SocialSession.token)
            }
        } finally {
            SocialSession.openJsonConnection = previous
        }
    }

    @Test fun queuedLogoutCannotRevokeTheNextAccountOnTheServer() {
        val identity = SocialSession.identity
        signIn("other-account", "other-refresh")
        assertThrows(IllegalStateException::class.java) { SocialSession.request("auth/logout", JSONObject(), identity) }
        assertEquals(0, server.requestCount)
        assertEquals("other-account", SocialSession.token)
        assertTrue(SocialSession.active)
    }
}
