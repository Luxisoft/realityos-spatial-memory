package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatRoutePolicyTest {
    @Test
    fun serverPersonResolvesToPeopleSearch() {
        assertEquals(
            ChatRoutePolicy.ResolvedRoute.PEOPLE_SEARCH,
            ChatRoutePolicy.resolveRoute("person"),
        )
    }

    @Test
    fun serverObjectResolvesToQuery() {
        assertEquals(
            ChatRoutePolicy.ResolvedRoute.OBJECT_QUERY,
            ChatRoutePolicy.resolveRoute("object"),
        )
    }

    @Test
    fun askAndUnknownResolveToAsk() {
        assertEquals(ChatRoutePolicy.ResolvedRoute.ASK, ChatRoutePolicy.resolveRoute("ask"))
        assertEquals(ChatRoutePolicy.ResolvedRoute.ASK, ChatRoutePolicy.resolveRoute(""))
        assertEquals(ChatRoutePolicy.ResolvedRoute.ASK, ChatRoutePolicy.resolveRoute("weird"))
    }

    @Test
    fun serverChatResolvesToChat() {
        assertEquals(ChatRoutePolicy.ResolvedRoute.CHAT, ChatRoutePolicy.resolveRoute("chat"))
    }

    @Test
    fun greetingFollowsDeviceLanguage() {
        assertTrue(ChatRoutePolicy.greeting("es").startsWith("¡Hola!"))
        assertTrue(ChatRoutePolicy.greeting("pt-BR").startsWith("Olá!"))
        assertTrue(ChatRoutePolicy.greeting("en").startsWith("Hi!"))
        assertTrue(ChatRoutePolicy.greeting("xx").startsWith("Hi!"))
    }

    @Test
    fun peopleAllowedOnlyForRegistered() {
        assertTrue(ChatRoutePolicy.peopleAllowed(isGuest = false))
        assertFalse(ChatRoutePolicy.peopleAllowed(isGuest = true))
    }

    @Test
    fun formatDurationShowsMinutesAndSeconds() {
        assertEquals("0:00", ChatRoutePolicy.formatDuration(0))
        assertEquals("0:05", ChatRoutePolicy.formatDuration(4800))
        assertEquals("1:07", ChatRoutePolicy.formatDuration(67000))
        assertEquals("0:00", ChatRoutePolicy.formatDuration(-100))
    }

    @Test
    fun roundButtonShowsSendOnTextAttachmentOrRecording() {
        assertFalse(ChatRoutePolicy.showSendButton(false, false, false))
        assertTrue(ChatRoutePolicy.showSendButton(true, false, false))
        assertTrue(ChatRoutePolicy.showSendButton(false, true, false))
        assertTrue(ChatRoutePolicy.showSendButton(false, false, true))
    }

    @Test
    fun personReplyWithProbeAndTextKeepsFaceSearch() {
        assertEquals(
            ChatRoutePolicy.PersonReply.FACE_SEARCH,
            ChatRoutePolicy.resolvePersonReply(hasProbe = true, hasText = true),
        )
    }

    @Test
    fun personReplyWithProbeOnlyKeepsFaceSearch() {
        assertEquals(
            ChatRoutePolicy.PersonReply.FACE_SEARCH,
            ChatRoutePolicy.resolvePersonReply(hasProbe = true, hasText = false),
        )
    }

    @Test
    fun personReplyWithTextOnlyUsesProfileSearch() {
        assertEquals(
            ChatRoutePolicy.PersonReply.TEXT_SEARCH,
            ChatRoutePolicy.resolvePersonReply(hasProbe = false, hasText = true),
        )
    }

    @Test
    fun personReplyWithoutProbeOrTextExpires() {
        assertEquals(
            ChatRoutePolicy.PersonReply.EXPIRED,
            ChatRoutePolicy.resolvePersonReply(hasProbe = false, hasText = false),
        )
    }

    @Test
    fun autoRouteKeepsPersonObjectAndChat() {
        assertEquals(ChatRoutePolicy.ResolvedRoute.PEOPLE_SEARCH, ChatRoutePolicy.resolveAutoRoute("person"))
        assertEquals(ChatRoutePolicy.ResolvedRoute.OBJECT_QUERY, ChatRoutePolicy.resolveAutoRoute("object"))
        assertEquals(ChatRoutePolicy.ResolvedRoute.CHAT, ChatRoutePolicy.resolveAutoRoute("chat"))
    }

    @Test
    fun autoRouteSendsAmbiguousToObjectSearch() {
        assertEquals(ChatRoutePolicy.ResolvedRoute.OBJECT_QUERY, ChatRoutePolicy.resolveAutoRoute("ask"))
        assertEquals(ChatRoutePolicy.ResolvedRoute.OBJECT_QUERY, ChatRoutePolicy.resolveAutoRoute(""))
        assertEquals(ChatRoutePolicy.ResolvedRoute.OBJECT_QUERY, ChatRoutePolicy.resolveAutoRoute("weird"))
    }

    @Test
    fun shortTextCannotSend() {
        assertFalse(ChatRoutePolicy.canSend(""))
        assertFalse(ChatRoutePolicy.canSend(" "))
        assertFalse(ChatRoutePolicy.canSend("a"))
        assertTrue(ChatRoutePolicy.canSend("ab"))
        assertTrue(ChatRoutePolicy.canSend("  hola  "))
    }

    @Test
    fun imageRouteLetsWordsWinOverFaces() {
        assertEquals(
            ChatRoutePolicy.ImageRoute.PEOPLE_TEXT,
            ChatRoutePolicy.imageRoute("Find people with arrest warrants", "person", 2),
        )
        assertEquals(
            ChatRoutePolicy.ImageRoute.OBJECT_QUERY,
            ChatRoutePolicy.imageRoute("Find the hammer", "object", 1),
        )
        assertEquals(
            ChatRoutePolicy.ImageRoute.OBJECT_QUERY,
            ChatRoutePolicy.imageRoute("buscalo", "ask", 1),
        )
    }

    @Test
    fun imageRouteWithoutWordsFollowsFaces() {
        assertEquals(
            ChatRoutePolicy.ImageRoute.FACE_PROBE,
            ChatRoutePolicy.imageRoute("", null, 1),
        )
        assertEquals(
            ChatRoutePolicy.ImageRoute.OBJECT_QUERY,
            ChatRoutePolicy.imageRoute("   ", null, 0),
        )
    }

    @Test
    fun imageRouteFallsBackToFacesWithoutTarget() {
        assertEquals(
            ChatRoutePolicy.ImageRoute.FACE_PROBE,
            ChatRoutePolicy.imageRoute("Find people", null, 1),
        )
        assertEquals(
            ChatRoutePolicy.ImageRoute.OBJECT_QUERY,
            ChatRoutePolicy.imageRoute("Find people", null, 0),
        )
    }

    @Test
    fun imageRouteNeedsWordsOrFaces() {
        assertNull(ChatRoutePolicy.imageRoute("", null, null))
        assertNull(ChatRoutePolicy.imageRoute("   ", "object", null))
        assertNull(ChatRoutePolicy.imageRoute("Find people", null, null))
    }
}
