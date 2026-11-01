package com.luxisoft.realityos

import androidx.compose.runtime.snapshots.SnapshotStateList
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

internal fun collapseChatDuplicates(messages: SnapshotStateList<ChatMessage>) {
    // A fresh turn can briefly coexist with its own history row when a
    // reload lands between persist and the local id update. Same server
    // id means the same turn: keep the first copy.
    val seen = mutableSetOf<Int>()
    val iterator = messages.iterator()
    while (iterator.hasNext()) {
        val id = iterator.next().serverId
        if (id != null && !seen.add(id)) iterator.remove()
    }
}

internal fun chatQuickReplies(guestsBlocked: Boolean, language: String = "en"): List<ChatQuickReply> = buildList {
    if (ChatRoutePolicy.peopleAllowed(guestsBlocked)) add(ChatQuickReply("ask_person", if (language == "es") "Persona" else "Person"))
    add(ChatQuickReply("ask_object", if (language == "es") "Objeto" else "Object"))
}

/** Refresh server snapshots while keeping Compose keys and unsent attachments. */
internal fun refreshKnownChatRows(messages: SnapshotStateList<ChatMessage>, rows: List<ChatMessage>): List<ChatMessage> {
    val incoming = rows.mapNotNull { row -> row.serverId?.let { it to row } }.toMap()
    messages.indices.forEach { index ->
        val old = messages[index]
        incoming[old.serverId]?.let { row ->
            messages[index] = row.copy(id = old.id, imagePreview = old.imagePreview, audioPaths = old.audioPaths)
        }
    }
    val known = messages.mapNotNullTo(mutableSetOf()) { it.serverId }
    return rows.filter { it.serverId == null || known.add(it.serverId) }
}

/** Upload original user recordings without translating their content. */
internal suspend fun uploadChatVoiceFiles(serverId: Int, paths: List<String>) {
    try {
        withContext(Dispatchers.IO) {
            paths.filter { File(it).exists() }.take(8).forEach { path ->
                val file = File(path)
                SocialSession.requestMultipart(
                    "chat/audio",
                    mapOf("message_id" to serverId.toString(), "duration_ms" to recordedDurationMs(file).toString()),
                    file.readBytes(),
                    "voice.m4a",
                    "audio/mp4",
                    fieldName = "audio"
                )
            }
        }
    } catch (cancelled: kotlinx.coroutines.CancellationException) {
        throw cancelled
    } catch (_: Exception) {
    }
}
