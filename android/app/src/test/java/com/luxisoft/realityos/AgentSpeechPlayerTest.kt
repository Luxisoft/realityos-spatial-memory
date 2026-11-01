package com.luxisoft.realityos

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = android.app.Application::class)
class AgentSpeechPlayerTest {
    private val context: Context = ApplicationProvider.getApplicationContext()

    private class Connection(private val code: Int) : HttpURLConnection(URL("https://example.test/v1/tts")) {
        val sent = ByteArrayOutputStream()
        var disconnected = false
        override fun connect() = Unit
        override fun usingProxy() = false
        override fun disconnect() {
            disconnected = true
        }
        override fun getOutputStream() = sent
        override fun getResponseCode() = code
    }

    @After
    fun clearSession() {
        SocialSession.token = null
    }

    @Test
    fun serverFailureUsesExistingVoiceOnceWithoutClientRetry() = runBlocking {
        SocialSession.token = "speech-account-token"
        val language = RealityExperienceStore(context).selectedLanguage().languageTag
        val connection = Connection(503)
        var fallback = 0
        var notices = 0
        var requests = 0
        val player = AgentSpeechPlayer(
            context,
            this,
            { null },
            {},
            {},
            { fallback++ },
            { notices++ },
            {
                requests++
                connection
            }
        )
        player.speak(LocalizedSpeech("Hello", language))
        withTimeout(3000) { while (fallback == 0) delay(10) }
        assertEquals(1, fallback)
        assertEquals(1, requests)
        assertEquals(1, notices)
        assertEquals("Bearer speech-account-token", connection.getRequestProperty("Authorization"))
        assertTrue(connection.sent.toString().contains("Hello"))
        assertTrue(connection.disconnected)
        player.stop()
    }

    @Test
    fun unauthorizedSpeechDoesNotRetryOrFallBack() = runBlocking {
        SocialSession.token = "expired-token"
        val language = RealityExperienceStore(context).selectedLanguage().languageTag
        var done = false
        var fallback = false
        val player = AgentSpeechPlayer(
            context,
            this,
            { null },
            {},
            { done = true },
            { fallback = true },
            {},
            { Connection(401) }
        )
        player.speak(LocalizedSpeech("Private response", language))
        withTimeout(3000) { while (!done) delay(10) }
        assertFalse(fallback)
        player.stop()
    }

    @Test
    fun stoppingDownloadPreventsDelayedFallback() = runBlocking {
        SocialSession.token = "speech-token"
        val entered = CountDownLatch(1)
        val released = CountDownLatch(1)
        var fallback = false
        val connection = object : HttpURLConnection(URL("https://example.test/v1/tts")) {
            override fun connect() = Unit
            override fun usingProxy() = false
            override fun getOutputStream() = ByteArrayOutputStream()
            override fun disconnect() {
                released.countDown()
            }
            override fun getResponseCode(): Int {
                entered.countDown()
                released.await(3, TimeUnit.SECONDS)
                return 503
            }
        }
        val player = AgentSpeechPlayer(context, this, { null }, {}, {}, { fallback = true }, {}, { connection })
        player.speak(LocalizedSpeech("Old response", RealityExperienceStore(context).selectedLanguage().languageTag))
        withTimeout(3000) { while (entered.count > 0) delay(10) }
        player.stop()
        delay(50)
        assertFalse(fallback)
        assertEquals(0L, released.count)
    }
}
