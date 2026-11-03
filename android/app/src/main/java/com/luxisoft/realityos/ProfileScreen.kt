package com.luxisoft.realityos

import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ProfileScreen(
    userId: String? = null,
    onBack: (() -> Unit)? = null,
    viewModel: RealityViewModel? = null,
    onViewerChange: (Boolean) -> Unit = {},
    sharedProfile: ProfileState? = null,
    active: Boolean = true,
    captureUploadStatus: String? = null
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val ownProfile = userId == null
    val state = sharedProfile ?: rememberProfileState(userId)
    val profile = state.profile
    val current = profile
    var busy by remember(userId) { mutableStateOf(false) }
    var error by remember(userId) { mutableStateOf("") }
    var mediaLoaded by remember(userId) { mutableStateOf(false) }
    var answerLoading by remember(userId) { mutableStateOf(false) }
    var question by remember(userId) { mutableStateOf("") }
    var answer by remember(userId) { mutableStateOf("") }
    var media by remember(userId) { mutableStateOf<List<JSONObject>>(emptyList()) }
    var mediaCursor by remember(userId) { mutableStateOf<String?>(null) }
    var mediaBusy by remember(userId) { mutableStateOf(false) }
    var refreshPending by remember(userId) { mutableStateOf(false) }
    var selectedMedia by remember(userId) { mutableStateOf<JSONObject?>(null) }
    var publishSpaces by remember { mutableStateOf(emptyList<JSONObject>()) }
    var publishWorkspace by remember { mutableStateOf<String?>(null) }
    var chooseWorkspace by remember { mutableStateOf(false) }
    LaunchedEffect(ownProfile, active) {
        if (ownProfile && active) {
            try {
                publishSpaces = withContext(Dispatchers.IO) { storageRows(JSONArray(SocialSession.request("workspaces"))).filter { !it.optString("name").startsWith("home:") } }
            } catch (failure: kotlinx.coroutines.CancellationException) {
                throw failure
            } catch (failure: Exception) {
                AppNotices.show(failure.message.orEmpty(), NoticeKind.ERROR)
            }
        }
    }
    var publishMenuExpanded by remember { mutableStateOf(false) }
    var pendingPhoto by remember { mutableStateOf<PendingPublishPhoto?>(null) }
    var showNoteDialog by remember { mutableStateOf(false) }
    var storageOpen by remember(profile?.optString("user_id")) { mutableStateOf(false) }
    LaunchedEffect(active) { if (!active) storageOpen = false }
    var captureUri by remember { mutableStateOf<Uri?>(null) }
    LaunchedEffect(selectedMedia) { onViewerChange(selectedMedia != null) }

    fun loadMedia(reset: Boolean = false) {
        val targetId = profile?.optString("user_id").orEmpty()
        if (mediaBusy) {
            if (reset) refreshPending = true
            return
        }
        if (targetId.isBlank() || (!reset && mediaCursor == null && media.isNotEmpty())) return
        scope.launch {
            mediaBusy = true
            try {
                val cursor = if (reset) null else mediaCursor
                val suffix = cursor?.let { "&cursor=${Uri.encode(it)}" }.orEmpty()
                val page = withContext(Dispatchers.IO) {
                    JSONObject(SocialSession.request("profiles/$targetId/media?limit=12$suffix"))
                }
                val values = page.optJSONArray("items") ?: JSONArray()
                val incoming = (0 until values.length()).map { values.getJSONObject(it) }
                media = if (reset) incoming else (media + incoming).distinctBy { it.getString("id") }
                mediaCursor = page.optString("next_cursor").takeIf { it.isNotBlank() && it != "null" }
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                mediaBusy = false
                mediaLoaded = true
                if (refreshPending) {
                    refreshPending = false
                    loadMedia(reset = true)
                }
            }
        }
    }

    LaunchedEffect(profile?.optString("user_id"), active, captureUploadStatus) {
        if (active && profile?.optString("user_id").orEmpty().isNotBlank()) loadMedia(reset = true)
    }

    val publicationUploader = rememberPublicationUploader(onPublished = { loadMedia(reset = true) }, onBusy = { busy = it })
    PublicationUploadDialog(publicationUploader)
    fun uploadPublication(photo: PendingPublishPhoto, noteText: String, noteSource: String) {
        val target = publishWorkspace ?: return
        publicationUploader.submit(photo, noteText, noteSource, "work", target)
    }

    fun stagePhoto(bytes: ByteArray, mime: String, name: String) {
        pendingPhoto = PendingPublishPhoto(bytes, mime, name)
        showNoteDialog = true
    }

    val pickPublication = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            busy = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error(localizedText(R.string.ui_could_not_read_the_image))
                val mime = context.contentResolver.getType(uri) ?: "image/jpeg"
                val name = uri.lastPathSegment?.substringAfterLast('/') ?: "publicacion"
                stagePhoto(bytes, mime, name)
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                busy = false
            }
        }
    }

    val takePublishPhoto = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (!success) return@rememberLauncherForActivityResult
        val uri = captureUri ?: return@rememberLauncherForActivityResult
        scope.launch {
            busy = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error(localizedText(R.string.ui_could_not_read_the_photo))
                stagePhoto(bytes, "image/jpeg", "camara.jpg")
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                busy = false
            }
        }
    }

    fun launchPhoneCamera() {
        val file = File(File(context.cacheDir, "captures").apply { mkdirs() }, "publicacion.jpg")
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
        captureUri = uri
        takePublishPhoto.launch(uri)
    }

    val askPublishCamera = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (it) launchPhoneCamera() else error = localizedText(R.string.ui_camera_permission_is_required)
    }

    fun launchPhoneCameraChecked() {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            launchPhoneCamera()
        } else {
            askPublishCamera.launch(Manifest.permission.CAMERA)
        }
    }

    fun onCameraOption() {
        publishMenuExpanded = false
        val vm = viewModel
        if (vm == null) {
            launchPhoneCameraChecked()
            return
        }
        scope.launch {
            busy = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) { vm.captureStillForPublish() }
                if (bytes != null) {
                    stagePhoto(bytes, "image/jpeg", "camara.jpg")
                } else {
                    launchPhoneCameraChecked()
                }
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                busy = false
            }
        }
    }

    if (storageOpen && ownProfile) {
        key(profile?.optString("user_id")) {
            StorageConnectionsScreen {
                storageOpen = false
                loadMedia(reset = true)
            }
        }
        return
    }
    Box(Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxSize()) {
            if (sharedProfile == null && selectedMedia == null) {
                ProfileHeader(state = state, onBack = onBack)
            }
            LazyColumn(
                modifier = Modifier.weight(1f).fillMaxWidth(),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                if (busy) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
                item { NoticeEffect(error, { error = "" }) }
                if (current != null) {
                    if (!ownProfile) {
                        item {
                            Card {
                                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                    Text(localizedText(R.string.ui_ask_about_this_profile), style = MaterialTheme.typography.titleMedium)
                                    OutlinedTextField(question, { question = it }, label = { Text(localizedText(R.string.ui_e_g_how_much_do_they_know_about_architecture)) }, modifier = Modifier.fillMaxWidth())
                                    Button(onClick = {
                                        scope.launch {
                                            busy = true
                                            answerLoading = true
                                            error = ""
                                            try {
                                                val language = RealityExperienceStore(context).syncAccountLanguage().languageTag
                                                val response = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("profiles/search", JSONObject().put("question", question).put("user_id", userId).put("language", language))) }
                                                if (language != RealityExperienceStore(context).selectedLanguage().languageTag) return@launch
                                                answer = response.optString("answer") + if (response.optBoolean("simulated")) localizedText(R.string.ui_simulated) else ""
                                            } catch (failure: Exception) {
                                                error = failure.message.orEmpty()
                                            } finally {
                                                busy = false
                                                answerLoading = false
                                            }
                                        }
                                    }, enabled = question.length >= 2 && !busy) { Text(localizedText(R.string.ui_ask)) }
                                    if (answerLoading) {
                                        SkeletonLines()
                                    } else if (answer.isNotBlank()) {
                                        Text(answer)
                                    }
                                }
                            }
                        }
                    }
                    item { HorizontalDivider(Modifier.padding(vertical = 4.dp)) }
                    item {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(localizedText(R.string.ui_publications), style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                            if (ownProfile) {
                                Box {
                                    IconButton(
                                        onClick = {
                                            publishWorkspace = publishSpaces.firstOrNull { it.optString("id") == SocialSession.workWorkspaceId }?.getString("id")
                                                ?: publishSpaces.singleOrNull()?.getString("id")
                                            if (publishSpaces.isEmpty()) {
                                                AppNotices.show(localizedText(R.string.publish_needs_group), NoticeKind.WARNING)
                                            } else if (publishWorkspace == null) {
                                                chooseWorkspace = true
                                            } else {
                                                publishMenuExpanded = true
                                            }
                                        },
                                        enabled = !busy
                                    ) {
                                        Icon(Icons.Default.Add, contentDescription = localizedText(R.string.ui_publish))
                                    }
                                    DropdownMenu(expanded = publishMenuExpanded, onDismissRequest = { publishMenuExpanded = false }) {
                                        DropdownMenuItem(
                                            text = { Text(localizedText(R.string.ui_take_photo)) },
                                            leadingIcon = { Icon(Icons.Default.CameraAlt, contentDescription = null) },
                                            onClick = { onCameraOption() }
                                        )
                                        DropdownMenuItem(
                                            text = { Text(localizedText(R.string.profile_choose_media)) },
                                            leadingIcon = { Icon(Icons.Default.PhotoLibrary, contentDescription = null) },
                                            onClick = {
                                                publishMenuExpanded = false
                                                pickPublication.launch(arrayOf("image/jpeg", "image/png", "image/webp", "video/mp4"))
                                            }
                                        )
                                    }
                                }
                            }
                        }
                    }
                    if (media.isEmpty() && mediaLoaded && !mediaBusy && error.isBlank()) {
                        item {
                            Box(Modifier.fillMaxWidth().height(180.dp), contentAlignment = Alignment.Center) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Icon(Icons.Default.PhotoLibrary, null, Modifier.size(48.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                                    Text(localizedText(R.string.ui_no_publications_yet), color = MaterialTheme.colorScheme.onSurfaceVariant)
                                }
                            }
                        }
                    }
                    items(media.distinctBy { it.optString("original_id").ifBlank { it.getString("id") } }.chunked(3)) { row ->
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                            row.forEach { item ->
                                Box(Modifier.weight(1f).aspectRatio(.78f).clickable { selectedMedia = item }) {
                                    DatabaseImage(
                                        model = profileImageRequest(context, item.optString("thumbnail_url")),
                                        contentDescription = item.optString("caption"),
                                        contentScale = ContentScale.Crop,
                                        modifier = Modifier.fillMaxSize()
                                    )
                                    PublicationSourceBadge(item.optString("source"), Modifier.align(Alignment.BottomStart).padding(4.dp))
                                    if (item.optString("mime_type").startsWith("video/")) {
                                        Icon(Icons.Default.PlayCircle, localizedText(R.string.profile_play_video), Modifier.align(Alignment.Center), tint = androidx.compose.ui.graphics.Color.White)
                                    }
                                }
                            }
                            repeat(3 - row.size) { Spacer(Modifier.weight(1f)) }
                        }
                        if (row.lastOrNull()?.optString("id") == media.lastOrNull()?.optString("id") && mediaCursor != null && !mediaBusy) {
                            LaunchedEffect(media.size, mediaCursor) { loadMedia() }
                        }
                    }
                    if (!mediaLoaded) {
                        item { SkeletonGrid() }
                    } else if (mediaBusy) {
                        item { CircularProgressIndicator(Modifier.size(24.dp)) }
                    }
                }
            }
        }
        if (chooseWorkspace) {
            AlertDialog(
                onDismissRequest = { chooseWorkspace = false },
                title = { Text(localizedText(R.string.ui_select_workspace)) },
                text = {
                    Column {
                        publishSpaces.forEach { space ->
                            TextButton(onClick = {
                                publishWorkspace = space.getString("id")
                                SocialSession.workWorkspaceId = publishWorkspace
                                chooseWorkspace = false
                                publishMenuExpanded = true
                            }) { Text(space.getString("name")) }
                        }
                    }
                },
                confirmButton = {}
            )
        }
        if (showNoteDialog) {
            pendingPhoto?.let { pending ->
                PublishNoteDialog(
                    onPublish = { noteText, noteSource ->
                        showNoteDialog = false
                        pendingPhoto = null
                        uploadPublication(pending, noteText, noteSource)
                    },
                    onDismiss = {
                        showNoteDialog = false
                        pendingPhoto = null
                    }
                )
            }
        }
        selectedMedia?.let { item ->
            MediaViewerScreen(
                title = item.optString("caption"),
                mediaUrl = profileMediaUrl(item.optString("media_url")),
                thumbnailUrl = profileMediaUrl(item.optString("thumbnail_url")),
                mimeType = item.optString("mime_type"),
                authToken = SocialSession.token,
                noteText = item.optString("note_text"),
                noteSource = item.optString("note_source"),
                metaLines = listOf(
                    item.optString("published_at").substringBefore("T").let {
                        if (it.isNotBlank()) localizedText(R.string.ui_published_on_1_s, it) else ""
                    }
                ),
                onClose = { selectedMedia = null }
            )
        }
    }
}
