package com.luxisoft.realityos

import android.app.Application
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35])
class DisplayProfileNavigationTest {
    private val first = "d678c6d6-8d86-48f9-9d30-59dcf08c6799"
    private val second = "48bbde50-535b-49af-a505-a0d4945f0685"

    @Test fun matchKeepsInternalUserIdForNativeProfileInsteadOfFacebookUrl() {
        val match = JSONObject().put("user_id", first).put("display_name", "Ana")
            .put("profile_link", "https://facebook.com/example")
            .put("evidence", JSONObject().put("thumbnail_url", "/v1/faces/enrollments/example/thumbnail"))
        assertEquals(first, decodeFaceThumb(match)?.profileUserId)
        match.put("user_id", JSONObject.NULL)
        assertEquals("", decodeFaceThumb(match)?.profileUserId)
    }

    @Test fun malformedIdsAndUrlsCannotBecomeProfilePaths() {
        for (id in listOf(null, "", "1-1-1-1-1", "../me/profile", "https://example.test/profile", "$first/other")) {
            assertNull(normalizedProfileId(id))
        }
        assertEquals(first, normalizedProfileId(first.uppercase()))
    }

    @Test fun pickerContainsOnlyDistinctProfilesFromMatches() {
        val alpha = GalleryThumb("thumb", "full", caption = "Ana", profileUserId = first, confidence = 0.91)
        val beta = alpha.copy(caption = "Luis", profileUserId = second)
        val targets = displayProfileTargets(listOf(alpha, alpha, beta, alpha.copy(profileUserId = "")))
        assertEquals(listOf(first, second), targets.map { it.userId })
        assertEquals(listOf("Ana", "Luis"), targets.map { it.name })
        assertEquals(0.91, targets.first().confidence!!, 0.001)
    }

    @Test fun runtimeProfileIdentityIsNotPersistedInChatHistory() {
        val thumb = GalleryThumb("thumb", "full", profileUserId = first)
        assertFalse(thumb.toJson().toString().contains(first))
        assertTrue(displayProfileTargets(listOf(thumb.copy(profileUserId = ""))).isEmpty())
    }
}
