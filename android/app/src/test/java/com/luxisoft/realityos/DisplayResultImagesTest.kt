package com.luxisoft.realityos

import android.app.Application
import android.graphics.Bitmap
import android.graphics.Color
import java.io.ByteArrayOutputStream
import java.time.Instant
import javax.net.ssl.HttpsURLConnection
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.tls.HandshakeCertificates
import okhttp3.tls.HeldCertificate
import okio.Buffer
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35])
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class DisplayResultImagesTest {
    private lateinit var server: MockWebServer
    private lateinit var images: DisplayResultImages
    private var clock = Instant.parse("2026-11-01T12:00:00Z")
    private var requests = mutableListOf<JSONObject>()

    @Before fun start() {
        val certificate = HeldCertificate.Builder().commonName("localhost").addSubjectAlternativeName("localhost").build()
        val serverTls = HandshakeCertificates.Builder().heldCertificate(certificate).build()
        val clientTls = HandshakeCertificates.Builder().addTrustedCertificate(certificate.certificate).build()
        server = MockWebServer().apply {
            useHttps(serverTls.sslSocketFactory(), false)
            start()
        }
        images = DisplayResultImages(
            requestLink = {
                requests.add(it)
                JSONObject().put("url", server.url("/match").toString()).put("expires_at", clock.plusSeconds(300).toString())
            },
            openConnection = { (java.net.URL(it).openConnection() as HttpsURLConnection).apply { sslSocketFactory = clientTls.sslSocketFactory() } },
            now = { clock }
        )
    }

    @After fun stop() {
        server.shutdown()
    }

    private fun link() = DisplayImageLink(server.url("/group").toString(), clock.plusSeconds(300))
    private fun photo(width: Int = 600, height: Int = 280): ByteArray = ByteArrayOutputStream().use { output ->
        Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888).apply { eraseColor(Color.RED) }
            .compress(Bitmap.CompressFormat.PNG, 100, output)
        output.toByteArray()
    }
    private fun enqueuePhoto() = server.enqueue(MockResponse().setHeader("Content-Type", "image/png").setBody(Buffer().write(photo())))
    private fun rejects(block: suspend () -> Unit) = runBlocking {
        try {
            block()
            fail("The unavailable image must fail before rendering")
        } catch (_: IllegalStateException) { } catch (_: IllegalArgumentException) { }
    }

    @Test fun realHttpsDownloadKeepsPixelsDimensionsAndSendsNoAccountToken() = runBlocking {
        enqueuePhoto()
        SocialSession.token = "private-account-token"
        try {
            val bitmap = images.load(link())
            assertEquals(600, bitmap.width)
            assertEquals(280, bitmap.height)
            assertEquals(Color.RED, bitmap.getPixel(300, 140))
            assertNull(server.takeRequest().getHeader("Authorization"))
        } finally {
            SocialSession.token = null
        }
    }

    @Test fun eachCandidateNavigationRequestsAFreshAuthorizedEnrollmentLink() = runBlocking {
        repeat(3) { enqueuePhoto() }
        for (id in listOf("first", "second", "first")) {
            assertEquals(600, images.match("face_enrollment", id).width)
        }
        assertEquals(listOf("first", "second", "first"), requests.map { it.getString("resource_id") })
        assertTrue(requests.all { it.getString("kind") == "face_enrollment" })
    }

    @Test fun galleryRequestsPreserveEvidenceLabels() = runBlocking {
        enqueuePhoto()
        images.match("evidence", "evidence-id", listOf("pliers"))
        assertEquals("[\"pliers\"]", requests.single().getJSONArray("labels").toString())
    }

    @Test fun emptyResourceCannotProduceAnImagelessCard() {
        rejects { images.match("face_enrollment", "") }
        assertTrue(requests.isEmpty())
        assertEquals(0, server.requestCount)
    }

    @Test fun expiredLinksAreRejectedBeforeNetworkAndCachedPixelsExpire() {
        val link = link()
        val cached = LoadedDisplayImage(link, Bitmap.createBitmap(2, 2, Bitmap.Config.ARGB_8888))
        assertTrue(images.valid(cached))
        clock = link.expiresAt
        assertFalse(images.valid(cached))
        rejects { images.load(link) }
        assertEquals(0, server.requestCount)
    }

    @Test fun unauthorizedMissingAndServerErrorImagesAreNotDecoded() {
        for (status in listOf(401, 403, 404, 503)) {
            server.enqueue(MockResponse().setResponseCode(status))
            rejects { images.load(link()) }
        }
    }

    @Test fun redirectsAreRejectedInsteadOfLeakingCapabilityUrls() {
        server.enqueue(MockResponse().setResponseCode(302).setHeader("Location", server.url("/other")))
        rejects { images.load(link()) }
        assertEquals(1, server.requestCount)
    }

    @Test fun htmlAndBrokenImageBodiesAreRejected() {
        for (type in listOf("text/html", "image/png")) {
            server.enqueue(MockResponse().setHeader("Content-Type", type).setBody("not an image"))
            rejects { images.load(link()) }
        }
    }

    @Test fun oversizedImagesAreRejectedBeforeBitmapAllocation() {
        server.enqueue(MockResponse().setHeader("Content-Type", "image/png").setBody(Buffer().write(photo(601, 280))))
        rejects { images.load(link()) }
    }

    @Test fun missingOrEmptySignedLinksFailExplicitly() {
        assertThrows(Exception::class.java) { DisplayImageLink.decode(JSONObject().put("expires_at", clock.toString())) }
        assertThrows(IllegalArgumentException::class.java) { DisplayImageLink.decode(JSONObject().put("url", "").put("expires_at", clock.toString())) }
    }
}
