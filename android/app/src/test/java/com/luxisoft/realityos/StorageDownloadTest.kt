package com.luxisoft.realityos

import java.net.HttpURLConnection
import java.net.URL
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.*
import org.junit.Test

class StorageDownloadTest {
    @Test
    fun snapshotCredentialAndNoRedirectFollowing() {
        val server = MockWebServer()
        server.start()
        val previous = SocialSession.openJsonConnection
        try {
            SocialSession.openJsonConnection = { path -> URL(server.url("/$path").toString()).openConnection() as HttpURLConnection }
            server.enqueue(MockResponse().setBody("image bytes"))
            assertEquals("image bytes", storageDownload("me/storage-connections/one/content", "snapshot-token").decodeToString())
            assertEquals("Bearer snapshot-token", server.takeRequest().getHeader("Authorization"))
            server.enqueue(MockResponse().setResponseCode(302).setHeader("Location", "https://untrusted.example/media"))
            assertThrows(IllegalStateException::class.java) { storageDownload("redirect", "snapshot-token") }
            assertEquals(2, server.requestCount)
        } finally {
            SocialSession.openJsonConnection = previous
            server.shutdown()
        }
    }

    @Test
    fun rejectsOversizedResourceBeforeReadingBody() {
        val server = MockWebServer()
        server.start()
        val previous = SocialSession.openJsonConnection
        try {
            SocialSession.openJsonConnection = { path -> URL(server.url("/$path").toString()).openConnection() as HttpURLConnection }
            server.enqueue(MockResponse().setHeader("Content-Length", 128L * 1024 * 1024))
            assertThrows(IllegalStateException::class.java) { storageDownload("large", "snapshot-token") }
        } finally {
            SocialSession.openJsonConnection = previous
            server.shutdown()
        }
    }
}
