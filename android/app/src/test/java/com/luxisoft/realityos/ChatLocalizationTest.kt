package com.luxisoft.realityos

import org.junit.Assert.*
import org.junit.Test

class ChatLocalizationTest {
    @Test
    fun pendingTranslationNeverDisplaysOrSpeaksOriginalEnglish() {
        val old = ChatMessage(role = ChatRole.AI, text = "English", speakText = "English", serverId = 30)
        val pending = applyChatLocalization(old, ChatLocalizedText("es", "pending"))
        assertEquals("", pending.text)
        assertNull(pending.speakText)
        assertEquals("pending", pending.translationStatus)
        assertEquals(old.id, pending.id)
        assertEquals(old.serverId, pending.serverId)
    }

    @Test
    fun completedTranslationPreservesEvidenceAndActionIds() {
        val original = ChatMessage(
            role = ChatRole.AI,
            text = "English",
            serverId = 28,
            gallery = listOf(GalleryThumb("small", "full", evidenceId = "proof"))
        )
        val ready = applyChatLocalization(
            original,
            ChatLocalizedText(
                "es",
                "ready",
                "Encontré cuatro resultados señalizados.",
                listOf(ChatQuickReply("ask_object", "Objeto"))
            )
        )
        assertEquals(ready.text, ready.speakText)
        assertEquals("es", ready.responseLanguage)
        assertEquals(original.gallery, ready.gallery)
        assertEquals(original.id, ready.id)
        assertEquals(listOf("ask_object"), ready.quickReplies.map { it.id })
    }

    @Test
    fun userHistoryRetainsOriginalTextWhileAiUsesSavedTranslation() {
        val original = ChatMessage(role = ChatRole.USER, text = "Please find a hammer")
        val user = applyChatLocalization(original, ChatLocalizedText("es", "ready", "Texto distinto"))
        assertEquals("Please find a hammer", user.text)
        val ai = applyChatLocalization(original.copy(role = ChatRole.AI), ChatLocalizedText("es", "ready", "Español"))
        assertEquals("Español", ai.text)
        assertEquals("Español", ai.speakText)
    }

    @Test
    fun englishQuickRepliesRetainRoutingIdentifiers() {
        assertEquals(listOf("Person", "Object"), chatQuickReplies(false, "en").map { it.label })
        assertEquals(listOf("ask_person", "ask_object"), chatQuickReplies(false, "en").map { it.id })
    }

    @Test
    fun replayNeverRelabelsASpanishBubbleAsEnglishSpeech() {
        val message = ChatMessage(role = ChatRole.AI, text = "Respuesta en español", speakText = "Respuesta en español", responseLanguage = "es")
        assertNull(chatSpeech(message, "en"))
        assertEquals(LocalizedSpeech("Respuesta en español", "es"), chatSpeech(message, "es"))
        assertEquals("Respuesta en español", message.text)
    }

    @Test
    fun replayUsesTheCompletedTranslationAndPreservesItsSourceLanguage() {
        val message = ChatMessage(role = ChatRole.AI, text = "Español", speakText = "Español", responseLanguage = "es")
        val translated = applyChatLocalization(message, ChatLocalizedText("en", "ready", "English answer"))
        assertEquals(LocalizedSpeech("English answer", "en"), chatSpeech(translated, "en"))
        assertNull(chatSpeech(translated, "es"))
        assertNull(chatSpeech(translated.copy(translationStatus = "pending"), "en"))
        assertNull(chatSpeech(translated.copy(translationStatus = "failed"), "en"))
    }

    @Test
    fun unknownLanguageAndUserTextCannotBecomeAssistantSpeech() {
        val message = ChatMessage(role = ChatRole.AI, text = "Unlabelled", speakText = "Unlabelled")
        assertNull(chatSpeech(message, "en"))
        assertNull(chatSpeech(message.copy(role = ChatRole.USER, responseLanguage = "en"), "en"))
        assertNull(chatSpeech(message.copy(responseLanguage = "en", speakText = " "), "en"))
    }
}
