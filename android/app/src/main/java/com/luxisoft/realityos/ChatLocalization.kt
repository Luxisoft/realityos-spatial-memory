package com.luxisoft.realityos

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.snapshots.SnapshotStateList
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

internal data class ChatLocalizedText(
    val language: String?,
    val status: String,
    val text: String? = null,
    val quickReplies: List<ChatQuickReply> = emptyList(),
    val simulated: Boolean = false
)

/** An old bubble must never be relabelled with the currently selected voice. */
internal fun chatSpeech(message: ChatMessage, selectedLanguage: String): LocalizedSpeech? {
    if (message.role != ChatRole.AI || message.translationStatus != "ready" || message.responseLanguage != selectedLanguage) return null
    val text = message.speakText?.let(::ttsNaturalText)?.takeIf { it.isNotBlank() } ?: return null
    return LocalizedSpeech(text, selectedLanguage)
}

internal fun applyChatLocalization(message: ChatMessage, value: ChatLocalizedText): ChatMessage {
    if (message.role == ChatRole.USER) return message
    val ready = value.status == "ready"
    val text = if (ready) value.text.orEmpty() else ""
    return message.copy(
        text = text,
        speakText = text.takeIf { ready && it.isNotBlank() },
        quickReplies = if (ready) value.quickReplies else emptyList(),
        responseLanguage = value.language,
        translationStatus = value.status,
        simulated = message.simulated || value.simulated
    )
}

internal fun applyChatLocalization(message: ChatMessage, row: JSONObject): ChatMessage {
    val replies = row.optJSONArray("localized_quick_replies")
    return applyChatLocalization(
        message,
        ChatLocalizedText(
            language = row.optText("response_language"),
            status = row.optString("translation_status", "pending"),
            text = row.optText("localized_text"),
            quickReplies = replies?.let { array ->
                (0 until array.length()).map { index ->
                    val reply = array.getJSONObject(index)
                    ChatQuickReply(reply.getString("id"), reply.getString("label"))
                }
            } ?: emptyList(),
            simulated = row.optBoolean("translation_simulated")
        )
    )
}

/** Explicit recovery writes once, then polls read-only status with a bounded wait. */
@Composable
internal fun ChatTranslationRecovery(messages: SnapshotStateList<ChatMessage>, language: String) {
    val pending = messages.filter {
        it.role == ChatRole.AI && it.serverId != null && it.translationStatus in listOf("pending", "preparing")
    }.mapNotNull { it.serverId }.takeLast(50)
    LaunchedEffect(pending, language) {
        if (pending.isEmpty()) return@LaunchedEffect
        fun applyRows(response: JSONObject) {
            val rows = response.optJSONArray("messages") ?: return
            for (index in 0 until rows.length()) {
                val row = rows.getJSONObject(index)
                if (row.optString("response_language") != language) continue
                val existing = messages.indexOfFirst { it.serverId == row.optInt("id") }
                if (existing >= 0) messages[existing] = applyChatLocalization(messages[existing], row)
            }
        }
        val started = android.os.SystemClock.elapsedRealtime()
        val progressTimer = launch {
            delay(10000)
            messages.indices.forEach { index ->
                val row = messages[index]
                if (row.serverId in pending && row.translationStatus == "pending") {
                    messages[index] = row.copy(translationStatus = "preparing")
                }
            }
        }
        try {
            applyRows(
                withContext(Dispatchers.IO) {
                    JSONObject(SocialSession.chatTranslations(JSONObject().put("message_ids", JSONArray(pending))))
                }
            )
            while (messages.any { it.serverId in pending && it.translationStatus in listOf("pending", "preparing") }) {
                val elapsed = android.os.SystemClock.elapsedRealtime() - started
                if (elapsed >= 45000) break
                delay(1500)
                applyRows(
                    withContext(Dispatchers.IO) {
                        JSONObject(SocialSession.chatTranslations(ids = pending))
                    }
                )
                if (elapsed >= 10000) {
                    messages.indices.forEach { index ->
                        val row = messages[index]
                        if (row.serverId in pending && row.translationStatus == "pending") {
                            messages[index] = row.copy(translationStatus = "preparing")
                        }
                    }
                }
            }
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            // The same retry affordance covers transport and translation failures.
        } finally {
            progressTimer.cancel()
        }
        messages.indices.forEach { index ->
            val row = messages[index]
            if (row.serverId in pending && row.translationStatus in listOf("pending", "preparing")) {
                messages[index] = row.copy(translationStatus = "failed")
            }
        }
    }
}
