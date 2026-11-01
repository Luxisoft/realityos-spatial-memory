package com.luxisoft.realityos

import androidx.compose.runtime.mutableStateListOf
import org.junit.Assert.assertEquals
import org.junit.Test

class ChatHistoryTest {
    @Test
    fun historyReloadKeepsFirstServerTurnAndEveryUnpersistedTurn() {
        val first = ChatMessage(role = ChatRole.USER, text = "First", serverId = 7)
        val duplicate = first.copy(id = first.id + 1, text = "Reloaded")
        val local = ChatMessage(role = ChatRole.USER, text = "Pending")
        val anotherLocal = local.copy(id = local.id + 1)
        val messages = mutableStateListOf(first, local, duplicate, anotherLocal)

        collapseChatDuplicates(messages)
        collapseChatDuplicates(messages)

        assertEquals(listOf(first, local, anotherLocal), messages.toList())
    }

    @Test
    fun guestRepliesKeepObjectSearchWithoutOfferingPeopleSearch() {
        assertEquals(listOf("ask_object"), chatQuickReplies(true).map { it.id })
        assertEquals(listOf("ask_person", "ask_object"), chatQuickReplies(false).map { it.id })
    }

    @Test
    fun refreshUpdatesExistingTranslationsWithoutLosingLocalKeysOrOlderRows() {
        val english = GalleryThumb("preview", "original", evidenceId = "saved", caption = "Workshop")
        val old = ChatMessage(role = ChatRole.AI, text = "Encontré una foto", serverId = 7, gallery = listOf(english))
        val older = ChatMessage(role = ChatRole.USER, text = "Anterior", serverId = 1)
        val local = ChatMessage(role = ChatRole.USER, text = "Pendiente")
        val messages = mutableStateListOf(older, old, local)
        val spanish = english.copy(localizedInformation = mapOf("es" to EvidenceText("Taller", "Nota", listOf("alicates"))))
        val fresh = refreshKnownChatRows(messages, listOf(old.copy(id = old.id + 1, gallery = listOf(spanish))))
        assertEquals(emptyList<ChatMessage>(), fresh)
        assertEquals(old.id, messages[1].id)
        assertEquals("Taller", messages[1].gallery[0].localizedInformation["es"]?.title)
        assertEquals(listOf(older.id, old.id, local.id), messages.map { it.id })
    }
}
