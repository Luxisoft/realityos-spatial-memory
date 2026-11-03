package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MediaAuthorizationTest {
    private val api = "https://realityos.example/v1"

    @Test fun `only the api origin receives the session token`() {
        assertEquals(mapOf("Authorization" to "Bearer session"), mediaAuthorization("https://realityos.example:443/v1/media/one", "session", api))
        for (url in listOf("https://avatar.example/photo.jpg", "https://realityos.example.avatar.example/image", "https://realityos.example@avatar.example/image", "http://realityos.example/image", "https://realityos.example:8443/image")) {
            assertTrue(url, mediaAuthorization(url, "session", api).isEmpty())
        }
    }

    @Test fun `missing sessions and malformed sources have no authorization`() {
        assertTrue(mediaAuthorization("https://realityos.example/image", null, api).isEmpty())
        assertTrue(mediaAuthorization("not a URL", "session", api).isEmpty())
        assertTrue(mediaAuthorization("file:///private/image", "session", api).isEmpty())
    }
}
