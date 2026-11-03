package com.luxisoft.realityos

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import android.media.MediaPlayer
import android.media.MediaRecorder
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.snapshotFlow
import androidx.compose.runtime.snapshots.SnapshotStateList
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import java.io.File
import java.util.Locale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

internal enum class ChatRole {
    USER,
    AI
}

internal data class ChatQuickReply(val id: String, val label: String)

/** Normalized probe box behind a 1:N face match, with its probe face identity. */
internal data class FaceProbeBox(
    val x: Float,
    val y: Float,
    val width: Float,
    val height: Float,
    val faceIndex: Int
)

/** One Display group row: every match keeps its face number and mark color. */
internal data class FaceGroupRow(
    val number: Int,
    val colorHex: String,
    val colorIndex: Int,
    val thumb: GalleryThumb
)

/** One numbered color box drawn over the group probe. */
internal data class FaceGroupMark(
    val number: Int,
    val box: FaceProbeBox,
    val colorHex: String
)

internal data class GalleryThumb(
    val thumbnailUrl: String,
    val mediaUrl: String,
    val caption: String = "",
    val boxedUrl: String = "",
    val imageUrl: String = "",
    val mediaId: String = "",
    val evidenceId: String = "",
    val mimeType: String = "image/jpeg",
    val frameTimestampMs: Long? = null,
    val noteText: String = "",
    val noteSource: String = "",
    val matchedLabels: List<String> = emptyList(),
    val confidence: Double? = null,
    val publishedAt: String = "",
    val simulated: Boolean = false,
    val matchKind: String = "",
    val localizationQuality: String = "",
    val localizedInformation: Map<String, EvidenceText> = emptyMap(),
    /** Face enrollment behind a 1:N match; Display-only, never persisted to chat history. */
    val faceEnrollmentId: String = "",
    /** Probe box behind a 1:N match; Display-only, never persisted to chat history. */
    val probeBox: FaceProbeBox? = null,
    /** Internal profile from a fresh face match; never a browser URL or history field. */
    val profileUserId: String = "",
    /** Workspace record behind a 1:N record match; opens the expediente. */
    val recordId: String = "",
    /** Display media-links kind for this thumb's enrollment thumbnail. */
    val faceDisplayKind: String = "avatar"
) {
    /** The chat keeps a small preview; the viewer requests the original dimensions. */
    val viewerUrl: String
        get() = if (imageUrl.isNotBlank()) {
            imageUrl
        } else if (boxedUrl.isBlank()) {
            mediaUrl
        } else {
            val base = boxedUrl.substringBefore('#')
            val fragment = boxedUrl.substringAfter('#', "").let { if (it.isEmpty()) "" else "#$it" }
            base + (if ('?' in base) "&" else "?") + "full_size=true" + fragment
        }
}

/** Null-safe string read: org.json optString leaks JSON null as the text "null". */
internal fun JSONObject.optText(key: String): String? {
    if (isNull(key)) return null
    return optString(key).ifBlank { null }?.takeUnless { it == "null" }
}

/** Make stored texts speak naturally: "foto(s)" must sound as "fotos". */
internal fun ttsNaturalText(raw: String): String = raw.replace(Regex("\\((s|es|S|ES)\\)"), "$1")
    .replace(Regex("\\s+"), " ")
    .trim()

internal data class ChatMessage(
    val id: Long = System.nanoTime(),
    val role: ChatRole,
    val responseLanguage: String? = null,
    val translationStatus: String = "ready",
    val text: String,
    val gallery: List<GalleryThumb> = emptyList(),
    val imagePreview: ByteArray? = null,
    val fromVoice: Boolean = false,
    val audioPaths: List<String> = emptyList(),
    val audioUrls: List<String> = emptyList(),
    val audioDurationMs: Int = 0,
    val serverId: Int? = null,
    val kind: String = "text",
    val evidenceUrl: String? = null,
    val evidenceMediaId: String = "",
    val simulated: Boolean = false,
    val speakText: String? = null,
    val faceAction: Boolean = false,
    val quickReplies: List<ChatQuickReply> = emptyList()
)

internal data class PendingChatProbe(val bytes: ByteArray, val mime: String)

internal fun mapHistoryRow(row: JSONObject): ChatMessage {
    val ai = row.optString("role") == "ai"
    val kind = row.optString("kind", "text")
    val urls = row.optJSONArray("audio_urls")?.let { array ->
        (0 until array.length()).mapNotNull { index ->
            if (array.isNull(index)) {
                null
            } else {
                array.optString(index).ifBlank { null }?.takeUnless { it == "null" }
            }
        }
    } ?: emptyList()
    val gallery = row.optJSONArray("gallery")?.let { array ->
        (0 until array.length()).mapNotNull { index ->
            val item = array.optJSONObject(index) ?: return@mapNotNull null
            decodeGalleryThumb(item)?.takeIf(::keepHistoryThumb)
        }
    } ?: emptyList()
    val replies = row.optJSONArray("quick_replies")?.let { array ->
        (0 until array.length()).mapNotNull { index ->
            val item = array.optJSONObject(index) ?: return@mapNotNull null
            val id = item.optText("id") ?: return@mapNotNull null
            val label = item.optText("label") ?: return@mapNotNull null
            ChatQuickReply(id, label)
        }
    } ?: emptyList()
    val built = ChatMessage(
        role = if (ai) ChatRole.AI else ChatRole.USER,
        text = row.optText("text").orEmpty(),
        fromVoice = kind == "voice",
        audioUrls = urls,
        audioDurationMs = row.optInt("audio_duration_ms"),
        evidenceUrl = row.optText("evidence_url"),
        gallery = gallery,
        simulated = row.optBoolean("simulated", false),
        faceAction = row.optBoolean("face_action", false),
        quickReplies = replies,
        speakText = if (ai) row.optText("text") else null,
        serverId = row.optInt("id"),
        kind = kind
    )
    return if (ai && row.has("translation_status")) applyChatLocalization(built, row) else built
}

internal fun recordedDurationMs(file: File): Int {
    val retriever = MediaMetadataRetriever()
    return try {
        retriever.setDataSource(file.absolutePath)
        retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toIntOrNull() ?: 0
    } catch (_: Exception) {
        0
    } finally {
        try {
            retriever.release()
        } catch (_: Exception) { }
    }
}
