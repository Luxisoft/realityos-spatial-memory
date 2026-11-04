package com.luxisoft.realityos

import com.luxisoft.realityos.data.JsonApi
import com.luxisoft.realityos.data.SessionJsonApi
import com.luxisoft.realityos.data.get
import com.luxisoft.realityos.data.post
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

internal data class ChatHistoryPage(val messages: List<ChatMessage>, val hasMore: Boolean)
internal data class ChatTurn(
    val role: String,
    val kind: String,
    val text: String,
    val evidenceUrl: String?,
    val gallery: List<GalleryThumb>,
    val simulated: Boolean,
    val quickReplies: List<ChatQuickReply>,
    val faceAction: Boolean,
    val responseLanguage: String?
)

internal data class RecordAnswer(
    val text: String?,
    val language: String?,
    val gallery: List<GalleryThumb> = emptyList()
)
internal data class ObjectAnswer(
    val text: String?,
    val speech: String?,
    val evidenceUrl: String?,
    val mediaId: String,
    val language: String?,
    val simulated: Boolean,
    val gallery: List<GalleryThumb>
)

/** Conversation persistence and object queries; biometric operations keep their own arm. */
internal class ChatRepository(
    private val identity: Long = SocialSession.identity,
    private val api: JsonApi = SessionJsonApi(identity)
) {
    suspend fun history(beforeId: Int?): ChatHistoryPage {
        val path = "chat/history?limit=10" + (beforeId?.let { "&before_id=$it" } ?: "")
        val result = JSONObject(api.get(path))
        val rows = result.optJSONArray("messages") ?: JSONArray()
        return ChatHistoryPage(List(rows.length()) { mapHistoryRow(rows.getJSONObject(it)) }, result.optBoolean("has_more"))
    }

    suspend fun append(turn: ChatTurn): Int {
        val payload = JSONObject().put("role", turn.role).put("kind", turn.kind).put("text", turn.text)
        turn.evidenceUrl?.takeIf(String::isNotBlank)?.let { payload.put("evidence_url", it) }
        if (turn.gallery.isNotEmpty()) payload.put("gallery", JSONArray().apply { turn.gallery.take(6).forEach { put(it.toJson()) } })
        if (turn.simulated) payload.put("simulated", true)
        if (turn.quickReplies.isNotEmpty()) {
            payload.put(
                "quick_replies",
                JSONArray().apply {
                    turn.quickReplies.take(4).forEach { put(JSONObject().put("id", it.id).put("label", it.label)) }
                }
            )
        }
        if (turn.faceAction) payload.put("face_action", true)
        if (turn.role == "ai") payload.put("response_language", turn.responseLanguage)
        return JSONObject(api.post("chat/append", payload)).optInt("id")
    }

    suspend fun answerRecords(workspaceId: String, question: String, language: String): RecordAnswer = guarded {
        val result = JSONObject(SocialSession.searchWorkspaceRecords(workspaceId, JSONObject().put("question", question).put("language", language)))
        val gallery = result.optJSONArray("gallery_matches")
        RecordAnswer(
            result.optText("answer"),
            result.optText("response_language"),
            (0 until (gallery?.length() ?: 0)).mapNotNull { gallery?.optJSONObject(it)?.let(::decodeGalleryThumb) }
        )
    }

    suspend fun query(workspaceId: String, question: String, language: String, probe: PendingChatProbe?): ObjectAnswer {
        val raw = if (probe == null) {
            api.post("queries", JSONObject().put("workspace_id", workspaceId).put("question", question).put("language", language))
        } else {
            guarded {
                SocialSession.requestMultipart(
                    "queries/image",
                    mapOf("workspace_id" to workspaceId, "question" to question, "language" to language),
                    probe.bytes,
                    "busqueda.jpg",
                    probe.mime,
                    fieldName = "image"
                )
            }
        }
        val result = JSONObject(raw)
        val gallery = result.optJSONArray("gallery_matches")
        return ObjectAnswer(
            result.optText("message"),
            result.optText("tts_text"),
            result.optText("highlighted_media_url"),
            result.optText("media_id").orEmpty(),
            result.optText("response_language"),
            result.optBoolean("simulated"),
            (0 until (gallery?.length() ?: 0)).mapNotNull { gallery?.optJSONObject(it)?.let(::decodeGalleryThumb) }
        )
    }

    suspend fun routeText(text: String): String = JSONObject(api.post("search/route", JSONObject().put("text", text))).optText("target") ?: "ask"

    suspend fun transcribe(file: File): String = guarded {
        JSONObject(SocialSession.requestMultipart("notes/transcribe", emptyMap(), file.readBytes(), "busqueda.m4a", "audio/mp4", fieldName = "audio")).optText("text").orEmpty().trim()
    }

    suspend fun mergeTranscript(parts: List<String>): String = JSONObject(api.post("notes/merge", JSONObject().put("texts", JSONArray(parts)))).optText("text").orEmpty().trim()

    private suspend fun <T> guarded(operation: () -> T): T = withContext(Dispatchers.IO) {
        SocialSession.requireCurrent(identity)
        operation().also { SocialSession.requireCurrent(identity) }
    }
}
