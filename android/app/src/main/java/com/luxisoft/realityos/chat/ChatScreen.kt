package com.luxisoft.realityos.chat

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
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.luxisoft.realityos.*
import com.luxisoft.realityos.R
import com.luxisoft.realityos.localizedText
import java.io.File
import java.util.Locale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

internal data class ChatScreenState(
    val listState: androidx.compose.foundation.lazy.LazyListState,
    val busy: Boolean,
    val routing: Boolean,
    val displayed: List<ChatMessage>,
    val playingId: Long?,
    val speakingId: Long?,
    val ttsSpeaking: Boolean,
    val historyLoading: Boolean,
    val messages: List<ChatMessage>,
    val transcribing: Boolean,
    val pendingAttachment: PendingChatProbe?,
    val recording: Boolean,
    val paused: Boolean,
    val recordingSeconds: Int,
    val voiceAmplitudes: List<Int>,
    val reviewPlaying: Boolean,
    val reviewProgress: Float,
    val reviewDurationMs: Int,
    val input: String,
    val working: Boolean
)

internal data class ChatScreenActions(
    val retryTranslation: (ChatMessage) -> Unit,
    val toggleSpeak: (ChatMessage) -> Unit,
    val answerQuickReply: (ChatQuickReply) -> Unit,
    val onFaceAction: () -> Unit,
    val onOpenEvidence: (List<GalleryThumb>, Int) -> Unit,
    val onPreviewImage: (ByteArray) -> Unit,
    val toggleAudio: (ChatMessage) -> Unit,
    val clearAttachment: () -> Unit,
    val discardVoiceSession: () -> Unit,
    val pauseVoice: () -> Unit,
    val sendVoiceSession: () -> Unit,
    val toggleReview: () -> Unit,
    val startRecording: () -> Unit,
    val updateInput: (String) -> Unit,
    val pickImage: () -> Unit,
    val captureCamera: () -> Unit,
    val sendComposed: () -> Unit,
    val beginRecording: () -> Unit
)

@Composable
internal fun ChatScreen(state: ChatScreenState, actions: ChatScreenActions) {
    with(state) {
        with(actions) {
            Column(Modifier.fillMaxSize()) {
                LazyColumn(
                    state = listState,
                    reverseLayout = true,
                    modifier = Modifier.weight(1f).fillMaxWidth(),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    if (busy || routing) {
                        item(key = "typing") {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Start) {
                                Surface(shape = RoundedCornerShape(16.dp), color = MaterialTheme.colorScheme.surfaceVariant) {
                                    Row(
                                        Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        SkeletonLines(Modifier.width(110.dp), rows = 2)
                                        Text(localizedText(R.string.ui_searching), style = MaterialTheme.typography.bodySmall)
                                    }
                                }
                            }
                        }
                    }
                    items(displayed, key = { it.id }) { message ->
                        ChatBubble(
                            message = message,
                            isPlayingAudio = playingId == message.id,
                            isSpeakingTts = speakingId == message.id && ttsSpeaking,
                            onToggleSpeak = { toggleSpeak(message) },
                            onRetryTranslation = { retryTranslation(message) },
                            onQuickReply = answerQuickReply,
                            onFaceAction = onFaceAction,
                            onEvidence = onOpenEvidence,
                            onPreviewImage = onPreviewImage,
                            onToggleAudio = { toggleAudio(message) }
                        )
                    }
                    if (historyLoading && messages.isNotEmpty()) {
                        item(key = "history-loading") {
                            SkeletonList(rows = 1)
                        }
                    }
                    if (messages.isEmpty()) {
                        item {
                            Box(Modifier.fillParentMaxSize(), contentAlignment = Alignment.Center) {
                                if (historyLoading) {
                                    SkeletonList(Modifier.align(Alignment.TopCenter).padding(top = 16.dp))
                                } else {
                                    Column(
                                        horizontalAlignment = Alignment.CenterHorizontally,
                                        verticalArrangement = Arrangement.spacedBy(8.dp)
                                    ) {
                                        Icon(
                                            painter = painterResource(R.drawable.ic_muse),
                                            contentDescription = null,
                                            modifier = Modifier.size(56.dp),
                                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                        Text(
                                            localizedText(R.string.ui_ask_record_your_voice_or_attach_an_image),
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
                if (transcribing) LinearProgressIndicator(Modifier.fillMaxWidth())
                Surface(
                    color = MaterialTheme.colorScheme.secondaryContainer,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(Modifier.fillMaxWidth()) {
                        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                        pendingAttachment?.let { probe ->
                            Row(
                                Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                val preview = remember(probe.bytes) {
                                    try {
                                        BitmapFactory.decodeByteArray(probe.bytes, 0, probe.bytes.size)?.asImageBitmap()
                                    } catch (_: Exception) {
                                        null
                                    }
                                }
                                preview?.let {
                                    Image(
                                        bitmap = it,
                                        contentDescription = localizedText(R.string.ui_attached_image),
                                        modifier = Modifier.size(48.dp).clip(RoundedCornerShape(8.dp)),
                                        contentScale = ContentScale.Crop
                                    )
                                    Spacer(Modifier.width(8.dp))
                                }
                                Text(
                                    localizedText(R.string.ui_it_will_be_sent_with_your_message),
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.weight(1f)
                                )
                                IconButton(onClick = { clearAttachment() }, modifier = Modifier.size(32.dp)) {
                                    Icon(Icons.Filled.Close, contentDescription = localizedText(R.string.ui_remove_image))
                                }
                            }
                        }
                        if (recording) {
                            Row(
                                Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    ChatRoutePolicy.formatDuration(recordingSeconds * 1000),
                                    style = MaterialTheme.typography.labelLarge,
                                    color = MaterialTheme.colorScheme.error
                                )
                                Spacer(Modifier.width(12.dp))
                                VoiceWaveform(
                                    amplitudes = voiceAmplitudes,
                                    progress = 1f,
                                    modifier = Modifier.weight(1f).height(36.dp)
                                )
                            }
                            Row(
                                Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                IconButton(onClick = discardVoiceSession, modifier = Modifier.size(48.dp)) {
                                    Icon(
                                        Icons.Filled.Delete,
                                        contentDescription = localizedText(R.string.ui_discard_recording),
                                        tint = MaterialTheme.colorScheme.error
                                    )
                                }
                                OutlinedButton(onClick = pauseVoice, modifier = Modifier.weight(1f)) {
                                    Icon(Icons.Filled.Pause, contentDescription = null)
                                    Spacer(Modifier.width(8.dp))
                                    Text(localizedText(R.string.ui_pause))
                                }
                                Spacer(Modifier.width(8.dp))
                                ChatRoundButton(icon = Icons.Filled.Send, description = localizedText(R.string.ui_send_audio), onClick = sendVoiceSession)
                            }
                        } else if (paused) {
                            Row(
                                Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                IconButton(onClick = toggleReview, modifier = Modifier.size(44.dp)) {
                                    Icon(
                                        if (reviewPlaying) Icons.Filled.Stop else Icons.Filled.PlayArrow,
                                        contentDescription = if (reviewPlaying) localizedText(R.string.ui_stop) else localizedText(R.string.ui_play_recording)
                                    )
                                }
                                VoiceWaveform(
                                    amplitudes = voiceAmplitudes,
                                    progress = reviewProgress,
                                    modifier = Modifier.weight(1f).height(36.dp)
                                )
                                Spacer(Modifier.width(12.dp))
                                Text(
                                    ChatRoutePolicy.formatDuration(reviewDurationMs),
                                    style = MaterialTheme.typography.labelLarge
                                )
                            }
                            Row(
                                Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                IconButton(onClick = discardVoiceSession, modifier = Modifier.size(48.dp)) {
                                    Icon(
                                        Icons.Filled.Delete,
                                        contentDescription = localizedText(R.string.ui_discard_recording),
                                        tint = MaterialTheme.colorScheme.error
                                    )
                                }
                                OutlinedButton(onClick = { startRecording() }, modifier = Modifier.weight(1f)) {
                                    Icon(Icons.Filled.Mic, contentDescription = null)
                                    Spacer(Modifier.width(8.dp))
                                    Text(localizedText(R.string.ui_continue))
                                }
                                Spacer(Modifier.width(8.dp))
                                ChatRoundButton(icon = Icons.Filled.Send, description = localizedText(R.string.ui_send_audio), onClick = sendVoiceSession)
                            }
                        } else {
                            Row(
                                Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 8.dp),
                                verticalAlignment = Alignment.Bottom
                            ) {
                                Surface(
                                    shape = RoundedCornerShape(28.dp),
                                    color = MaterialTheme.colorScheme.surfaceVariant,
                                    modifier = Modifier.weight(1f)
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        modifier = Modifier.padding(start = 16.dp, end = 4.dp, top = 4.dp, bottom = 4.dp)
                                    ) {
                                        TextField(
                                            value = input,
                                            onValueChange = { updateInput(it) },
                                            placeholder = { Text(localizedText(R.string.ui_type)) },
                                            modifier = Modifier.weight(1f),
                                            maxLines = 5,
                                            colors = TextFieldDefaults.colors(
                                                focusedContainerColor = Color.Transparent,
                                                unfocusedContainerColor = Color.Transparent,
                                                disabledContainerColor = Color.Transparent,
                                                focusedIndicatorColor = Color.Transparent,
                                                unfocusedIndicatorColor = Color.Transparent,
                                                disabledIndicatorColor = Color.Transparent
                                            )
                                        )
                                        IconButton(
                                            onClick = pickImage,
                                            enabled = !working,
                                            modifier = Modifier.size(44.dp)
                                        ) {
                                            Icon(Icons.Filled.AttachFile, contentDescription = localizedText(R.string.ui_attach_image))
                                        }
                                        IconButton(
                                            onClick = {
                                                captureCamera()
                                            },
                                            enabled = !working,
                                            modifier = Modifier.size(44.dp)
                                        ) {
                                            Icon(Icons.Filled.CameraAlt, contentDescription = localizedText(R.string.ui_capture))
                                        }
                                    }
                                }
                                Spacer(Modifier.width(8.dp))
                                val showSend = ChatRoutePolicy.showSendButton(input.isNotBlank(), pendingAttachment != null, false)
                                ChatRoundButton(
                                    icon = if (showSend) Icons.Filled.Send else Icons.Filled.Mic,
                                    description = if (showSend) localizedText(R.string.ui_send) else localizedText(R.string.ui_record_voice),
                                    onClick = {
                                        if (showSend) {
                                            sendComposed()
                                        } else {
                                            beginRecording()
                                        }
                                    },
                                    enabled = !working
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ChatRoundButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    description: String,
    onClick: () -> Unit,
    enabled: Boolean = true
) {
    Surface(
        shape = CircleShape,
        color = MaterialTheme.colorScheme.primary,
        modifier = Modifier.size(52.dp)
    ) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
            IconButton(onClick = onClick, enabled = enabled, modifier = Modifier.size(52.dp)) {
                Icon(icon, contentDescription = description, tint = MaterialTheme.colorScheme.onPrimary)
            }
        }
    }
}

@Composable
private fun VoiceWaveform(amplitudes: List<Int>, progress: Float, modifier: Modifier = Modifier) {
    val played = MaterialTheme.colorScheme.primary
    val idle = MaterialTheme.colorScheme.onSurfaceVariant
    Canvas(modifier) {
        val bars = amplitudes.takeLast(64)
        if (bars.isEmpty()) {
            drawLine(
                idle.copy(alpha = 0.4f),
                Offset(0f, center.y),
                Offset(size.width, center.y),
                strokeWidth = 4f,
                cap = StrokeCap.Round
            )
            return@Canvas
        }
        val gap = 3.dp.toPx()
        val barWidth = ((size.width - gap * (bars.size - 1)) / bars.size).coerceAtLeast(2f)
        bars.forEachIndexed { index, amplitude ->
            val fraction = (amplitude / 2800f).coerceIn(0.12f, 1f)
            val height = size.height * fraction
            drawRoundRect(
                color = if (index.toFloat() / bars.size <= progress) played else idle.copy(alpha = 0.55f),
                topLeft = Offset(index * (barWidth + gap), (size.height - height) / 2),
                size = Size(barWidth, height),
                cornerRadius = CornerRadius(barWidth / 2)
            )
        }
    }
}

@Composable
private fun ChatMuseAvatar() {
    Surface(
        shape = CircleShape,
        color = MaterialTheme.colorScheme.secondaryContainer,
        modifier = Modifier.size(36.dp)
    ) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
            Icon(
                painter = painterResource(R.drawable.ic_muse),
                contentDescription = "Muse",
                modifier = Modifier.size(22.dp),
                tint = MaterialTheme.colorScheme.onSecondaryContainer
            )
        }
    }
}

@Composable
private fun ChatPersonAvatar() {
    val context = LocalContext.current
    val photoUrl = SocialSession.profilePictureUrl
    if (photoUrl != null) {
        coil.compose.SubcomposeAsyncImage(
            model = profileImageRequest(context, photoUrl),
            contentDescription = localizedText(R.string.ui_you),
            contentScale = ContentScale.Crop,
            loading = { SkeletonBlock(Modifier.fillMaxSize().clip(CircleShape)) },
            error = { ChatPersonFallback() },
            modifier = Modifier.size(36.dp).clip(CircleShape)
        )
    } else {
        ChatPersonFallback()
    }
}

@Composable
private fun ChatPersonFallback() {
    Surface(
        shape = CircleShape,
        color = MaterialTheme.colorScheme.secondaryContainer,
        modifier = Modifier.size(36.dp)
    ) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
            Icon(
                Icons.Filled.Person,
                contentDescription = localizedText(R.string.ui_you),
                modifier = Modifier.size(22.dp),
                tint = MaterialTheme.colorScheme.onSecondaryContainer
            )
        }
    }
}

@Composable
private fun AudioPlayButton(playing: Boolean, onToggle: () -> Unit, label: String) {
    Surface(
        shape = CircleShape,
        color = MaterialTheme.colorScheme.surface,
        modifier = Modifier.size(48.dp)
    ) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
            IconButton(onClick = onToggle, modifier = Modifier.size(48.dp)) {
                Icon(
                    if (playing) Icons.Filled.Stop else Icons.Filled.PlayArrow,
                    contentDescription = if (playing) stringResource(R.string.ui_stop_recording) else stringResource(R.string.ui_play_recording),
                    tint = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}

@Composable
private fun ChatBubble(
    message: ChatMessage,
    isPlayingAudio: Boolean,
    isSpeakingTts: Boolean,
    onQuickReply: (ChatQuickReply) -> Unit,
    onFaceAction: () -> Unit,
    onEvidence: (List<GalleryThumb>, Int) -> Unit,
    onPreviewImage: (ByteArray) -> Unit,
    onToggleAudio: () -> Unit,
    onToggleSpeak: () -> Unit,
    onRetryTranslation: () -> Unit
) {
    val context = LocalContext.current
    val viewerItems = message.viewerItems()
    val isUser = message.role == ChatRole.USER
    val hasAudio = message.audioPaths.any { File(it).exists() } || message.audioUrls.isNotEmpty()
    Row(
        Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.Top
    ) {
        if (!isUser) {
            ChatMuseAvatar()
            Spacer(Modifier.width(8.dp))
        }
        Surface(
            shape = RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.weight(1f)
        ) {
            Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                message.imagePreview?.let { bytes ->
                    val bitmap = remember(bytes) {
                        try {
                            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
                        } catch (_: Exception) {
                            null
                        }
                    }
                    bitmap?.let {
                        Image(
                            bitmap = it,
                            contentDescription = localizedText(R.string.ui_attached_image),
                            modifier = Modifier.size(160.dp).clip(RoundedCornerShape(8.dp))
                                .clickable { onPreviewImage(bytes) },
                            contentScale = ContentScale.Crop
                        )
                    }
                }
                when (message.translationStatus) {
                    "pending" -> SkeletonLines(rows = 2)
                    "preparing" -> Text(stringResource(R.string.chat_translation_preparing))
                    "failed" -> Column {
                        Text(stringResource(R.string.chat_translation_failed))
                        TextButton(onClick = onRetryTranslation) { Text(stringResource(R.string.chat_translation_retry)) }
                    }
                }
                if (message.text.isNotBlank() || hasAudio || message.speakText != null) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        if (message.text.isNotBlank()) {
                            Text(
                                message.text,
                                modifier = Modifier.weight(1f),
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                        if (hasAudio) {
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(4.dp)
                            ) {
                                AudioPlayButton(playing = isPlayingAudio, onToggle = onToggleAudio, label = "audio")
                                Text(
                                    ChatRoutePolicy.formatDuration(message.audioDurationMs),
                                    style = MaterialTheme.typography.labelSmall
                                )
                            }
                        }
                        if (message.speakText != null) {
                            AudioPlayButton(playing = isSpeakingTts, onToggle = onToggleSpeak, label = "respuesta")
                        }
                    }
                }
                message.evidenceUrl?.let { path ->
                    DatabaseImage(
                        model = coil.request.ImageRequest.Builder(context)
                            .data(authorizedMediaUrl(path))
                            .addHeader("Authorization", "Bearer ${SocialSession.token}")
                            .build(),
                        contentDescription = localizedText(R.string.ui_evidence),
                        modifier = Modifier.fillMaxWidth().height(160.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .clickable { onEvidence(viewerItems, 0) },
                        contentScale = ContentScale.Crop
                    )
                }
                if (message.gallery.isNotEmpty()) {
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        items(orderedEvidence(message.gallery)) { thumb ->
                            val language = RealityExperienceStore(context).selectedLanguage().languageTag
                            val translated = thumb.localizedInformation[language]
                            Column(Modifier.width(96.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                DatabaseImage(
                                    model = coil.request.ImageRequest.Builder(context)
                                        .data(authorizedMediaUrl(thumb.boxedUrl.ifBlank { thumb.thumbnailUrl }))
                                        .addHeader("Authorization", "Bearer ${SocialSession.token}")
                                        .build(),
                                    contentDescription = thumb.caption.ifBlank { localizedText(R.string.ui_matching_publication) },
                                    modifier = Modifier.size(96.dp)
                                        .clip(RoundedCornerShape(8.dp))
                                        .clickable { onEvidence(viewerItems, viewerItems.indexOfFirst { it.mediaId == thumb.mediaId && it.viewerUrl == thumb.viewerUrl }.coerceAtLeast(0)) },
                                    contentScale = ContentScale.Crop
                                )
                                if (thumb.matchKind.isNotBlank()) {
                                    Text(
                                        when (thumb.matchKind) {
                                            "family" -> stringResource(R.string.evidence_family)
                                            "similar" -> stringResource(R.string.evidence_similar)
                                            else -> stringResource(R.string.evidence_exact)
                                        },
                                        style = MaterialTheme.typography.labelSmall
                                    )
                                }
                                if (!translated?.labels.isNullOrEmpty()) Text(translated!!.labels.joinToString(), style = MaterialTheme.typography.labelSmall, maxLines = 2)
                            }
                        }
                    }
                }
                if (message.simulated) {
                    Text(
                        localizedText(R.string.ui_simulated),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.tertiary
                    )
                }
                if (message.faceAction) {
                    Button(onClick = onFaceAction, modifier = Modifier.fillMaxWidth()) {
                        Text(localizedText(R.string.ui_find_person))
                    }
                }
                if (message.quickReplies.isNotEmpty()) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        message.quickReplies.forEach { reply ->
                            SuggestionChip(onClick = { onQuickReply(reply) }, label = { Text(reply.label) })
                        }
                    }
                }
            }
        }
        if (isUser) {
            Spacer(Modifier.width(8.dp))
            ChatPersonAvatar()
        }
    }
}
