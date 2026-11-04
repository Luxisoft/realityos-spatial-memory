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
import androidx.compose.foundation.background
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
import androidx.compose.ui.platform.LocalResources
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.luxisoft.realityos.chat.*
import java.io.File
import java.util.Locale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

/**
 * AI chat: text, voice and image search in one conversation. The AI answers
 * with text, evidence captures and spoken audio.
 */
@Composable
internal fun AiChat(
    messages: SnapshotStateList<ChatMessage>,
    viewModel: RealityViewModel?,
    onOpenEvidence: (List<GalleryThumb>, Int) -> Unit
) {
    val context = LocalContext.current
    val resources = LocalResources.current
    val scope = rememberCoroutineScope()
    val repository = remember(SocialSession.identity) { ChatRepository() }
    val groupsRepository = remember(SocialSession.identity) { GalleryRepository() }
    val guestsBlocked = SocialSession.isGuest
    var workspaceId by remember { mutableStateOf((SocialSession.workWorkspaceId ?: SocialSession.workspaceId).orEmpty()) }
    var input by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var routing by remember { mutableStateOf(false) }
    var pendingProbe by remember { mutableStateOf<PendingChatProbe?>(null) }
    var pendingText by remember { mutableStateOf<Pair<String, Boolean>?>(null) }
    var captureUri by remember { mutableStateOf<Uri?>(null) }
    var recording by remember { mutableStateOf(false) }
    var paused by remember { mutableStateOf(false) }
    var recordingSeconds by remember { mutableStateOf(0) }
    var transcribing by remember { mutableStateOf(false) }
    var pendingAttachment by remember { mutableStateOf<PendingChatProbe?>(null) }
    var lightboxBytes by remember { mutableStateOf<ByteArray?>(null) }
    var voiceSegments by remember { mutableStateOf<List<File>>(emptyList()) }
    var voiceAmplitudes by remember { mutableStateOf<List<Int>>(emptyList()) }
    var reviewPlaying by remember { mutableStateOf(false) }
    var reviewProgress by remember { mutableFloatStateOf(0f) }
    var reviewPlayer by remember { mutableStateOf<MediaPlayer?>(null) }
    var reviewIndex by remember { mutableStateOf(0) }
    var reviewDurationMs by remember { mutableStateOf(0) }
    val working = busy || routing || transcribing
    LaunchedEffect(recording) {
        if (recording) {
            recordingSeconds = 0
            while (recording) {
                delay(1000)
                recordingSeconds++
            }
        }
    }

    var recorder by remember { mutableStateOf<MediaRecorder?>(null) }
    var audioFile by remember { mutableStateOf<File?>(null) }
    val playback = remember { ChatAudioPlayback(context) }
    var speakingId by remember { mutableStateOf<Long?>(null) }
    val ttsSpeaking by (viewModel?.speaking?.collectAsState(initial = false) ?: remember { mutableStateOf(false) })
    LaunchedEffect(ttsSpeaking) {
        if (!ttsSpeaking) speakingId = null
    }
    val experienceStore = remember(context) { RealityExperienceStore(context) }
    val selectedLanguage by experienceStore.language.collectAsState()
    val deviceLanguage = selectedLanguage.languageTag
    ChatTranslationRecovery(messages, deviceLanguage)
    val listState = rememberLazyListState()
    var visibleCount by remember { mutableStateOf(ChatPagingPolicy.initialVisible(messages.size)) }
    var lastSeenSize by remember { mutableStateOf(messages.size) }
    var newTurn by remember { mutableLongStateOf(0L) }
    val displayed = ChatPagingPolicy.displaySlice(messages.toList(), visibleCount)
    ChatAutoScroll(listState, newTurn, working)
    LaunchedEffect(messages.size) {
        if (messages.size > lastSeenSize) {
            visibleCount = minOf(visibleCount + messages.size - lastSeenSize, messages.size)
        }
        lastSeenSize = messages.size
    }
    var historyLoading by remember { mutableStateOf(false) }
    var initialHistoryPending by remember { mutableStateOf(messages.isEmpty()) }
    var historyExhausted by remember { mutableStateOf(false) }

    fun mergeHistoryRows(rows: List<ChatMessage>, beforeId: Int?) {
        // Two chat surfaces can share this list; concurrent loads must merge
        // idempotently instead of duplicating bubbles.
        collapseChatDuplicates(messages)
        val fresh = refreshKnownChatRows(messages, rows)
        if (beforeId == null) {
            if (fresh.isEmpty()) {
                collapseChatDuplicates(messages)
                return
            }
            val ordered = (fresh.asReversed() + messages.toList()).sortedWith(
                compareBy<ChatMessage> { it.serverId ?: Int.MAX_VALUE }.thenBy { it.id }
            )
            messages.clear()
            messages.addAll(ordered)
        } else if (fresh.isNotEmpty()) {
            messages.addAll(0, fresh.asReversed())
        } else if (rows.isNotEmpty()) {
            historyExhausted = true
        } else {
            historyExhausted = true
        }
        collapseChatDuplicates(messages)
    }

    fun loadHistoryPage(beforeId: Int?) {
        if (historyLoading || (beforeId != null && historyExhausted)) return
        historyLoading = true
        scope.launch {
            var requestedLanguage: String? = null
            try {
                requestedLanguage = experienceStore.syncAccountLanguage().languageTag
                val page = repository.history(beforeId)
                val rows = withContext(Dispatchers.IO) {
                    page.messages.map { mapped ->
                        val probeId = mapped.serverId
                        if (mapped.role == ChatRole.USER && mapped.imagePreview == null && probeId != null) {
                            loadChatProbe(context, probeId)?.let { mapped.copy(imagePreview = it) } ?: mapped
                        } else {
                            mapped
                        }
                    }
                }
                if (requestedLanguage != experienceStore.selectedLanguage().languageTag) return@launch
                historyExhausted = !page.hasMore
                mergeHistoryRows(rows, beforeId)
            } catch (_: Exception) {
                if (beforeId != null) historyExhausted = true
            } finally {
                historyLoading = false
                initialHistoryPending = false
                if (requestedLanguage != null && requestedLanguage != experienceStore.selectedLanguage().languageTag) loadHistoryPage(beforeId)
            }
        }
    }

    fun persistTurn(
        role: String,
        kind: String,
        text: String,
        evidenceUrl: String?,
        localId: Long,
        gallery: List<GalleryThumb> = emptyList(),
        simulated: Boolean = false,
        quickReplies: List<ChatQuickReply> = emptyList(),
        faceAction: Boolean = false,
        responseLanguage: String? = null
    ) {
        if (text.isBlank()) return
        scope.launch {
            try {
                val id = repository.append(
                    ChatTurn(role, kind, text, evidenceUrl, gallery, simulated, quickReplies, faceAction, responseLanguage ?: deviceLanguage)
                )
                val index = messages.indexOfFirst { it.id == localId }
                if (index >= 0 && id > 0) {
                    val paths = messages[index].audioPaths
                    val preview = messages[index].imagePreview
                    messages[index] = messages[index].copy(serverId = id)
                    collapseChatDuplicates(messages)
                    if (role == "user" && paths.isNotEmpty()) uploadChatVoiceFiles(id, paths)
                    if (role == "user" && preview != null) {
                        withContext(Dispatchers.IO) { saveChatProbe(context, id, preview) }
                    }
                }
            } catch (_: Exception) {
            }
        }
    }

    fun chatText(id: Int): String = localizedText(id)

    fun pushUser(text: String, kind: String, message: ChatMessage? = null): ChatMessage {
        val built = message ?: ChatMessage(role = ChatRole.USER, text = text, kind = kind)
        messages.add(built)
        newTurn++
        persistTurn("user", kind, text.ifBlank { localizedText(R.string.ui_image) }, null, built.id)
        return built
    }

    fun speakNatural(request: LocalizedSpeech) {
        viewModel?.speak(request.text, request.language)
    }

    fun pushAi(text: String, evidenceUrl: String? = null, message: ChatMessage? = null): ChatMessage {
        val original = (message ?: ChatMessage(role = ChatRole.AI, text = text, evidenceUrl = evidenceUrl, speakText = text)).let {
            if (it.responseLanguage == null) it.copy(responseLanguage = experienceStore.selectedLanguage().languageTag) else it
        }
        val built = if (original.responseLanguage != experienceStore.selectedLanguage().languageTag) {
            original.copy(text = "", speakText = null, quickReplies = emptyList(), translationStatus = "pending")
        } else {
            original
        }
        messages.add(built)
        newTurn++
        persistTurn("ai", "text", text, evidenceUrl, built.id, original.gallery, original.simulated, original.quickReplies, original.faceAction, original.responseLanguage)
        val speak = chatSpeech(built, experienceStore.selectedLanguage().languageTag)
        if (speak != null) {
            playback.stopAudio()
            viewModel?.stopSpeak()
            speakNatural(speak)
            if (viewModel != null) speakingId = built.id
        }
        return built
    }

    // Refresh translations even when navigation reuses an already loaded list.
    LaunchedEffect(deviceLanguage) {
        playback.stopAudio()
        viewModel?.stopSpeak()
        speakingId = null
        messages.indices.forEach { index ->
            val row = messages[index]
            if (row.role == ChatRole.AI && row.responseLanguage != deviceLanguage) {
                messages[index] = row.copy(text = "", speakText = null, quickReplies = emptyList(), translationStatus = "pending")
            }
        }
        loadHistoryPage(null)
    }
    // Load persisted profile history on open; reload if the list was cleared by logout.
    LaunchedEffect(messages.isEmpty()) {
        if (messages.isEmpty() && !historyLoading) {
            historyExhausted = false
            loadHistoryPage(null)
        }
    }
    // Scrolling up onto the oldest displayed message reveals the previous page.
    LaunchedEffect(listState) {
        snapshotFlow { listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index }
            .collect { lastVisible ->
                val total = messages.size
                val shown = ChatPagingPolicy.displayCount(visibleCount, total)
                if (lastVisible == null || lastVisible < shown - 1) return@collect
                if (ChatPagingPolicy.hasMore(visibleCount, total)) {
                    visibleCount = ChatPagingPolicy.nextVisible(visibleCount, total)
                } else if (!historyExhausted && !historyLoading) {
                    messages.firstOrNull { it.serverId != null }?.serverId?.let { loadHistoryPage(it) }
                        ?: run { historyExhausted = true }
                }
            }
    }

    LaunchedEffect(Unit) {
        try {
            val spaces = groupsRepository.groups()
            workspaceId = queryWorkspaceId(spaces.map { it.id to it.name }, SocialSession.workWorkspaceId, SocialSession.workspaceId)
        } catch (_: Exception) {
        }
    }
    fun releaseRecorder() {
        try {
            recorder?.release()
        } catch (_: Exception) { }
        recorder = null
    }

    DisposableEffect(Unit) {
        onDispose {
            playback.stopAudio()
            viewModel?.stopSpeak()
            try {
                reviewPlayer?.release()
            } catch (_: Exception) { }
            releaseRecorder()
        }
    }

    fun toggleSpeak(message: ChatMessage) {
        if (speakingId == message.id && ttsSpeaking) {
            viewModel?.stopSpeak()
            speakingId = null
            return
        }
        val request = chatSpeech(message, experienceStore.selectedLanguage().languageTag) ?: return
        playback.stopAudio()
        viewModel?.stopSpeak()
        speakNatural(request)
        speakingId = message.id
    }

    fun toggleAudio(message: ChatMessage) {
        viewModel?.stopSpeak()
        speakingId = null
        if (playback.playingId == message.id) {
            playback.stopAudio()
            return
        }
        playback.stopAudio()
        val paths = message.audioPaths.filter { File(it).exists() }
        if (paths.isNotEmpty()) {
            playback.playingId = message.id
            playback.playAudioSequence(paths, 0)
            return
        }
        if (message.audioUrls.isNotEmpty()) {
            playback.playingId = message.id
            playback.playUrlSequence(message.audioUrls, 0)
        }
    }

    LaunchedEffect(recording) {
        while (recording) {
            delay(120)
            val level = try {
                recorder?.maxAmplitude ?: 0
            } catch (_: Exception) {
                0
            }
            voiceAmplitudes = (voiceAmplitudes + level).takeLast(100)
        }
    }
    LaunchedEffect(reviewPlaying) {
        while (reviewPlaying) {
            delay(120)
            val player = reviewPlayer
            val total = reviewDurationMs
            if (player == null || total <= 0) {
                reviewProgress = 0f
            } else {
                try {
                    val done = voiceSegments.take(reviewIndex).sumOf { recordedDurationMs(it) }
                    reviewProgress = ((done + player.currentPosition).toFloat() / total).coerceIn(0f, 1f)
                } catch (_: Exception) {
                }
            }
        }
    }

    fun runPeopleText(text: String, fromVoice: Boolean) {
        scope.launch {
            busy = true
            try {
                val requestLanguage = experienceStore.syncAccountLanguage().languageTag
                val response = repository.answerRecords(workspaceId, text, requestLanguage)
                val answer = response.text?.ifBlank { chatText(R.string.chat_no_answer) } ?: chatText(R.string.chat_no_answer)
                pushAi(answer, message = ChatMessage(role = ChatRole.AI, text = answer, gallery = response.gallery, speakText = answer, responseLanguage = response.language ?: requestLanguage))
            } catch (failure: Exception) {
                pushAi(chatText(R.string.chat_query_failed))
            } finally {
                busy = false
            }
        }
    }

    fun runFaceSearch(probe: PendingChatProbe, fromVoice: Boolean) {
        if (guestsBlocked) {
            pushAi(localizedText(R.string.ui_guests_cannot_search_for_meta_people))
            return
        }
        scope.launch {
            busy = true
            try {
                val raw = withContext(Dispatchers.IO) {
                    SocialSession.requestMultipart(
                        "faces/search",
                        mapOf("workspace_id" to workspaceId),
                        probe.bytes,
                        "busqueda.jpg",
                        probe.mime
                    )
                }
                val response = JSONObject(raw)
                val found = response.optJSONArray("matches") ?: JSONArray()
                val foundRecords = response.optJSONArray("matches_records") ?: JSONArray()
                val gallery = (0 until found.length()).mapNotNull { decodeFaceThumb(found.optJSONObject(it)) } +
                    (0 until foundRecords.length()).mapNotNull { decodeRecordFaceThumb(foundRecords.optJSONObject(it)) }
                val names = gallery.joinToString { faceMatchLabel(it.caption, it.confidence) }
                val message = if (gallery.isEmpty()) {
                    chatText(R.string.chat_face_none)
                } else {
                    localizedQuantityText(R.plurals.chat_face_found, gallery.size, gallery.size, names)
                }
                pushAi(
                    message,
                    null,
                    ChatMessage(
                        role = ChatRole.AI,
                        text = message,
                        gallery = gallery,
                        responseLanguage = deviceLanguage,
                        simulated = response.optBoolean("simulated"),
                        speakText = message
                    )
                )
            } catch (failure: Exception) {
                pushAi(chatText(R.string.chat_query_failed))
            } finally {
                busy = false
            }
        }
    }

    fun runObjectQuery(question: String, probe: PendingChatProbe?, fromVoice: Boolean) {
        scope.launch {
            busy = true
            try {
                val requestLanguage = experienceStore.syncAccountLanguage().languageTag
                val response = repository.query(workspaceId, question, requestLanguage, probe)
                val message = response.text ?: chatText(R.string.chat_no_evidence)
                val speak = response.speech ?: message
                val evidence = response.evidenceUrl
                pushAi(
                    message,
                    evidence,
                    ChatMessage(
                        role = ChatRole.AI,
                        text = message,
                        gallery = response.gallery,
                        evidenceUrl = evidence,
                        evidenceMediaId = response.mediaId,
                        responseLanguage = response.language ?: requestLanguage,
                        simulated = response.simulated,
                        speakText = speak
                    )
                )
            } catch (failure: Exception) {
                pushAi(chatText(R.string.chat_query_failed))
            } finally {
                busy = false
            }
        }
    }

    fun dispatchText(clean: String, fromVoice: Boolean) {
        scope.launch {
            routing = true
            val target = try {
                repository.routeText(clean)
            } catch (failure: Exception) {
                routing = false
                pendingProbe = null
                pushAi(chatText(R.string.chat_route_failed))
                return@launch
            }
            routing = false
            if (target == "person" && guestsBlocked) {
                pendingProbe = null
                pushAi(localizedText(R.string.ui_guests_cannot_search_for_meta_people))
                return@launch
            }
            when (ChatRoutePolicy.resolveAutoRoute(target)) {
                ChatRoutePolicy.ResolvedRoute.CHAT -> {
                    pushAi(ChatRoutePolicy.greeting(experienceStore.selectedLanguage().languageTag))
                }
                ChatRoutePolicy.ResolvedRoute.PEOPLE_SEARCH -> {
                    pendingProbe = null
                    runPeopleText(clean, fromVoice)
                }
                ChatRoutePolicy.ResolvedRoute.OBJECT_QUERY -> {
                    val probe = pendingProbe
                    pendingProbe = null
                    runObjectQuery(clean, probe, fromVoice)
                }
                ChatRoutePolicy.ResolvedRoute.ASK -> {
                    runObjectQuery(clean, null, fromVoice)
                }
            }
        }
    }

    fun routeImageWithText(probe: PendingChatProbe, question: String, fromVoice: Boolean) {
        if (workspaceId.isBlank()) {
            pushAi(chatText(R.string.chat_workspace_missing))
            return
        }
        scope.launch {
            busy = true
            try {
                // The user's words lead: image classification only assists.
                val faces = try {
                    val response = withContext(Dispatchers.IO) {
                        JSONObject(
                            SocialSession.requestMultipart(
                                "search/classify",
                                mapOf("workspace_id" to workspaceId),
                                probe.bytes,
                                "busqueda.jpg",
                                probe.mime,
                                fieldName = "image"
                            )
                        )
                    }
                    if (response.has("faces")) response.optInt("faces") else null
                } catch (_: Exception) {
                    null
                }
                val target = if (question.isBlank()) {
                    null
                } else {
                    try {
                        repository.routeText(question)
                    } catch (_: Exception) {
                        null
                    }
                }
                when (ChatRoutePolicy.imageRoute(question, target, faces)) {
                    ChatRoutePolicy.ImageRoute.PEOPLE_TEXT -> {
                        if (guestsBlocked) {
                            pushAi(localizedText(R.string.ui_guests_cannot_search_for_meta_people))
                        } else {
                            runPeopleText(question, fromVoice)
                        }
                    }
                    ChatRoutePolicy.ImageRoute.FACE_PROBE -> runFaceSearch(probe, fromVoice)
                    ChatRoutePolicy.ImageRoute.OBJECT_QUERY -> runObjectQuery(question, probe, fromVoice)
                    null -> pushAi(chatText(R.string.chat_image_failed))
                }
            } finally {
                busy = false
            }
        }
    }

    fun sendComposed() {
        if (working || recording) return
        val attachment = pendingAttachment
        val clean = input.trim()
        if (attachment == null) {
            if (!ChatRoutePolicy.canSend(clean)) return
            pushUser(clean, "text")
            input = ""
            dispatchText(clean, false)
            return
        }
        pendingAttachment = null
        input = ""
        pushUser(
            clean,
            "image",
            ChatMessage(role = ChatRole.USER, text = clean, imagePreview = attachment.bytes, kind = "image")
        )
        routeImageWithText(attachment, clean, false)
    }

    suspend fun transcribeAudioFile(file: File): String = repository.transcribe(file)

    fun sendVoiceFiles(files: List<File>) {
        scope.launch {
            transcribing = true
            try {
                val parts = files.map { transcribeAudioFile(it) }.filter { it.length >= 2 }
                val text = if (parts.size > 1) {
                    repository.mergeTranscript(parts)
                } else {
                    parts.joinToString(" ").trim()
                }
                if (text.length < 2) {
                    pushAi(chatText(R.string.chat_voice_missing))
                    return@launch
                }
                val duration = withContext(Dispatchers.IO) { files.sumOf { recordedDurationMs(it) } }
                val paths = files.map { it.absolutePath }
                val attachment = pendingAttachment
                pendingAttachment = null
                if (attachment == null) {
                    pushUser(
                        text,
                        "voice",
                        ChatMessage(
                            role = ChatRole.USER,
                            text = text,
                            fromVoice = true,
                            audioPaths = paths,
                            audioDurationMs = duration,
                            kind = "voice"
                        )
                    )
                    dispatchText(text, true)
                } else {
                    pushUser(
                        text,
                        "voice",
                        ChatMessage(
                            role = ChatRole.USER,
                            text = text,
                            fromVoice = true,
                            audioPaths = paths,
                            audioDurationMs = duration,
                            imagePreview = attachment.bytes,
                            kind = "voice"
                        )
                    )
                    routeImageWithText(attachment, text, true)
                }
            } catch (failure: Exception) {
                pushAi(chatText(R.string.chat_voice_failed))
            } finally {
                transcribing = false
            }
        }
    }

    fun stopReview() {
        try {
            reviewPlayer?.stop()
            reviewPlayer?.release()
        } catch (_: Exception) {
        }
        reviewPlayer = null
        reviewPlaying = false
    }

    fun playReviewSequence(index: Int) {
        val files = voiceSegments.filter { it.exists() }
        if (index >= files.size) {
            stopReview()
            return
        }
        try {
            MediaPlayer().apply {
                setDataSource(files[index].absolutePath)
                setOnCompletionListener {
                    try {
                        release()
                    } catch (_: Exception) { }
                    reviewPlayer = null
                    playReviewSequence(index + 1)
                }
                prepare()
                start()
                reviewPlayer = this
                reviewIndex = index
            }
        } catch (_: Exception) {
            stopReview()
        }
    }

    fun toggleReview() {
        if (reviewPlaying) {
            stopReview()
            reviewProgress = 0f
            return
        }
        if (voiceSegments.none { it.exists() }) return
        reviewProgress = 0f
        reviewPlaying = true
        playReviewSequence(0)
    }

    fun finishCurrentSegment(): File? {
        var failed = false
        try {
            recorder?.stop()
        } catch (_: Exception) {
            failed = true
        }
        releaseRecorder()
        recording = false
        val file = audioFile
        audioFile = null
        if (failed || file == null || !file.exists()) return null
        voiceSegments = voiceSegments + file
        return file
    }

    fun pauseVoice() {
        stopReview()
        if (finishCurrentSegment() == null && voiceSegments.isEmpty()) {
            pushAi(chatText(R.string.chat_recording_failed))
            return
        }
        paused = true
        reviewDurationMs = voiceSegments.sumOf { recordedDurationMs(it) }
    }

    fun sendVoiceSession() {
        stopReview()
        if (recording) finishCurrentSegment()
        recording = false
        paused = false
        val files = voiceSegments.filter { it.exists() }
        voiceSegments = emptyList()
        voiceAmplitudes = emptyList()
        reviewProgress = 0f
        if (files.isEmpty()) return
        sendVoiceFiles(files)
    }

    fun discardVoiceSession() {
        stopReview()
        recording = false
        paused = false
        try {
            recorder?.stop()
        } catch (_: Exception) { }
        releaseRecorder()
        (voiceSegments + listOfNotNull(audioFile)).forEach {
            try {
                it.delete()
            } catch (_: Exception) { }
        }
        audioFile = null
        voiceSegments = emptyList()
        voiceAmplitudes = emptyList()
        reviewProgress = 0f
    }

    fun startRecording() {
        stopReview()
        try {
            val file = File(File(context.cacheDir, "search").apply { mkdirs() }, "voz-${System.currentTimeMillis()}.m4a")
            audioFile = file
            recorder = MediaRecorder(context).apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioSamplingRate(44100)
                setAudioEncodingBitRate(128000)
                setOutputFile(file.absolutePath)
                prepare()
                start()
            }
            recording = true
            paused = false
        } catch (_: Exception) {
            pushAi(chatText(R.string.chat_recording_failed))
            releaseRecorder()
        }
    }

    val askAudio = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (!it) {
            pushAi(chatText(R.string.chat_microphone_permission))
        } else {
            startRecording()
        }
    }

    fun handleUri(uri: Uri?) {
        if (uri == null) return
        scope.launch {
            try {
                val (bytes, mime) = withContext(Dispatchers.IO) {
                    val raw = context.contentResolver.openInputStream(uri)?.use { stream -> stream.readBytes() }
                        ?: error(chatText(R.string.chat_image_read_failed))
                    val fixed = uprightImageBytes(raw)
                    if (fixed != null) {
                        fixed to "image/jpeg"
                    } else {
                        raw to (context.contentResolver.getType(uri) ?: "image/jpeg")
                    }
                }
                pendingAttachment = PendingChatProbe(bytes, mime)
            } catch (failure: Exception) {
                pushAi(chatText(R.string.chat_action_failed))
            }
        }
    }
    val pickImage = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { handleUri(it) }
    val takePicture = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (success) handleUri(captureUri)
    }
    fun launchCamera() {
        val file = File(File(context.cacheDir, "captures").apply { mkdirs() }, "busqueda.jpg")
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
        captureUri = uri
        takePicture.launch(uri)
    }
    val askCamera = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (it) {
            launchCamera()
        } else {
            pushAi(chatText(R.string.chat_camera_permission))
        }
    }

    fun answerQuickReply(reply: ChatQuickReply) {
        pushUser(reply.label, "text")
        val text = pendingText
        pendingText = null
        val probe = pendingProbe
        pendingProbe = null
        if (reply.id == "ask_person") {
            when (ChatRoutePolicy.resolvePersonReply(probe != null, text != null)) {
                ChatRoutePolicy.PersonReply.FACE_SEARCH ->
                    runFaceSearch(probe!!, text?.second ?: false)
                ChatRoutePolicy.PersonReply.TEXT_SEARCH ->
                    runPeopleText(text!!.first, text.second)
                ChatRoutePolicy.PersonReply.EXPIRED ->
                    pushAi(chatText(R.string.chat_question_expired))
            }
        } else {
            if (text != null) {
                runObjectQuery(text.first, probe, text.second)
            } else if (probe != null) {
                runObjectQuery("", probe, false)
            } else {
                pushAi(chatText(R.string.chat_image_expired))
            }
        }
    }

    ChatScreen(
        state = ChatScreenState(
            listState = listState,
            busy = busy,
            routing = routing,
            displayed = displayed,
            playingId = playback.playingId,
            speakingId = speakingId,
            ttsSpeaking = ttsSpeaking,
            historyLoading = historyLoading || initialHistoryPending,
            messages = messages,
            transcribing = transcribing,
            pendingAttachment = pendingAttachment,
            recording = recording,
            paused = paused,
            recordingSeconds = recordingSeconds,
            voiceAmplitudes = voiceAmplitudes,
            reviewPlaying = reviewPlaying,
            reviewProgress = reviewProgress,
            reviewDurationMs = reviewDurationMs,
            input = input,
            working = working
        ),
        actions = ChatScreenActions(
            retryTranslation = { message ->
                val index = messages.indexOfFirst { it.id == message.id }
                if (index >= 0) messages[index] = messages[index].copy(translationStatus = "pending")
            },
            toggleSpeak = ::toggleSpeak,
            answerQuickReply = ::answerQuickReply,
            onFaceAction = {
                val probe = pendingProbe
                if (probe != null) runFaceSearch(probe, false) else pushAi(chatText(R.string.chat_image_expired))
            },
            onOpenEvidence = onOpenEvidence,
            onPreviewImage = { lightboxBytes = it },
            toggleAudio = ::toggleAudio,
            clearAttachment = { pendingAttachment = null },
            discardVoiceSession = ::discardVoiceSession,
            pauseVoice = ::pauseVoice,
            sendVoiceSession = ::sendVoiceSession,
            toggleReview = ::toggleReview,
            startRecording = ::startRecording,
            updateInput = { input = it },
            pickImage = { pickImage.launch("image/*") },
            captureCamera = { if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) launchCamera() else askCamera.launch(Manifest.permission.CAMERA) },
            sendComposed = ::sendComposed,
            beginRecording = { if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) startRecording() else askAudio.launch(Manifest.permission.RECORD_AUDIO) }
        )
    )

    lightboxBytes?.let { bytes ->
        Dialog(
            onDismissRequest = { lightboxBytes = null },
            properties = DialogProperties(usePlatformDefaultWidth = false)
        ) {
            Box(
                Modifier.fillMaxSize().background(Color.Black).clickable { lightboxBytes = null },
                contentAlignment = Alignment.Center
            ) {
                val bitmap = remember(bytes) {
                    runCatching { BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap() }.getOrNull()
                }
                bitmap?.let {
                    Image(
                        bitmap = it,
                        contentDescription = localizedText(R.string.ui_image_sent),
                        modifier = Modifier.fillMaxWidth(),
                        contentScale = ContentScale.Fit
                    )
                }
                IconButton(
                    onClick = { lightboxBytes = null },
                    modifier = Modifier.align(Alignment.TopEnd).statusBarsPadding()
                ) {
                    Icon(Icons.Filled.Close, contentDescription = localizedText(R.string.ui_close), tint = Color.White)
                }
            }
        }
    }
}
