package com.luxisoft.realityos

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.luxisoft.realityos.host.GalleryActions
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

@Composable
@SuppressLint("LocalContextGetResourceValueCall")
fun SocialGallery(
    viewModel: RealityViewModel,
    onWelcome: () -> Unit = {},
    onViewerChange: (Boolean) -> Unit = {},
    galleryBar: GalleryTopBarState? = null,
    onAdminDrawerChange: (Boolean) -> Unit = {},
    capturePublicationRevision: Long = 0
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val repository = remember(SocialSession.identity) { GalleryRepository() }
    var authenticated by remember { mutableStateOf(SocialSession.token != null) }
    var loginBusy by remember { mutableStateOf(false) }
    var showImport by remember { mutableStateOf(false) }
    var showRecords by remember { mutableStateOf(false) }
    var groupId by rememberSaveable { mutableStateOf(SocialSession.workWorkspaceId) }
    var filters by remember(groupId) { mutableStateOf(if (galleryBar != null && galleryBar.selectedId == groupId) galleryBar.filters else GalleryFilterSelection()) }
    var editingClassification by remember { mutableStateOf<PublicationSummary?>(null) }
    var draftCategories by remember { mutableStateOf(emptyList<String>()) }
    var draftTags by remember { mutableStateOf(emptyList<String>()) }
    var posts by remember(groupId) { mutableStateOf<List<PublicationSummary>>(emptyList()) }
    var error by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var pageFailed by remember { mutableStateOf(false) }
    var pageLoaded by remember(groupId) { mutableStateOf(false) }
    var groupsLoading by remember { mutableStateOf(true) }
    var commentsLoading by remember { mutableStateOf(false) }
    var inviteLoading by remember { mutableStateOf(false) }
    var selected by remember { mutableStateOf<PublicationSummary?>(null) }
    var interaction by remember { mutableStateOf<String?>(null) }
    var text by remember { mutableStateOf("") }
    var comments by remember { mutableStateOf<List<ViewerComment>>(emptyList()) }
    var reply by remember { mutableStateOf<String?>(null) }
    var groups by remember { mutableStateOf<List<WorkGroup>>(emptyList()) }
    var groupDialog by remember { mutableStateOf<String?>(null) }
    var groupPin by remember { mutableStateOf("") }
    var groupText by remember { mutableStateOf("") }
    var liked by remember { mutableStateOf(setOf<String>()) }
    var revision by remember { mutableIntStateOf(0) }
    var cursor by remember(groupId) { mutableStateOf<String?>(null) }
    var nextCursor by remember(groupId) { mutableStateOf<String?>(null) }
    var endReached by remember(groupId) { mutableStateOf(false) }
    var publishing by remember { mutableStateOf(false) }
    var workPublishMenu by remember { mutableStateOf(false) }
    var workPendingPhoto by remember { mutableStateOf<PendingPublishPhoto?>(null) }
    var workNoteDialog by remember { mutableStateOf(false) }
    var workCaptureUri by remember { mutableStateOf<Uri?>(null) }
    var showAdministration by remember { mutableStateOf(false) }
    var entryConsent by remember { mutableStateOf(false) }
    var faceConsentAsk by remember { mutableStateOf(false) }
    var faceCaptureDone by remember { mutableStateOf<Boolean?>(null) }
    var identityVerified by remember { mutableStateOf<Boolean?>(null) }
    var deniedLastTime by remember { mutableStateOf(false) }
    val resumedSession = remember { SocialSession.token != null }
    val publicationUploader = rememberPublicationUploader(onPublished = {
        cursor = null
        endReached = false
        revision++
    }, onBusy = { publishing = it })
    PublicationUploadDialog(publicationUploader)
    fun uploadWorkPublication(photo: PendingPublishPhoto, noteText: String, noteSource: String, classification: PublicationClassification) {
        val target = groupId ?: return
        publicationUploader.submit(photo, noteText, noteSource, target, classification)
    }

    fun stageWorkPhoto(bytes: ByteArray, mime: String, name: String) {
        workPendingPhoto = PendingPublishPhoto(bytes, mime, name)
        workNoteDialog = true
    }

    val pickWorkPublication = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            publishing = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error(localizedText(R.string.ui_could_not_read_the_image))
                val mime = context.contentResolver.getType(uri) ?: "image/jpeg"
                val name = uri.lastPathSegment?.substringAfterLast('/') ?: "publicacion"
                stageWorkPhoto(bytes, mime, name)
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                publishing = false
            }
        }
    }

    val takeWorkPhoto = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (!success) return@rememberLauncherForActivityResult
        val uri = workCaptureUri ?: return@rememberLauncherForActivityResult
        scope.launch {
            publishing = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error(localizedText(R.string.ui_could_not_read_the_photo))
                stageWorkPhoto(bytes, "image/jpeg", "camara.jpg")
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                publishing = false
            }
        }
    }

    fun launchWorkPhoneCamera() {
        val file = File(File(context.cacheDir, "captures").apply { mkdirs() }, "publicacion.jpg")
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
        workCaptureUri = uri
        takeWorkPhoto.launch(uri)
    }

    val askWorkCamera = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (it) launchWorkPhoneCamera() else error = localizedText(R.string.ui_camera_permission_is_required)
    }

    fun launchWorkPhoneCameraChecked() {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            launchWorkPhoneCamera()
        } else {
            askWorkCamera.launch(Manifest.permission.CAMERA)
        }
    }

    fun onWorkCameraOption() {
        workPublishMenu = false
        scope.launch {
            publishing = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) { viewModel.captureStillForPublish() }
                if (bytes != null) {
                    stageWorkPhoto(bytes, "image/jpeg", "camara.jpg")
                } else {
                    launchWorkPhoneCameraChecked()
                }
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                publishing = false
            }
        }
    }

    fun requireFreshLogin() {
        SocialSession.clear()
        if (!BuildConfig.LOCAL_DEVELOPMENT) com.facebook.login.LoginManager.getInstance().logOut()
        authenticated = false
        posts = emptyList()
        faceCaptureDone = null
        identityVerified = null
        deniedLastTime = false
        SocialSession.loginNotice = context.getString(R.string.face_login_required)
    }
    fun runRequest(action: suspend () -> Unit) {
        scope.launch {
            try {
                action()
            } catch (cancelled: kotlinx.coroutines.CancellationException) {
                throw cancelled
            } catch (e: Exception) {
                error = e.message ?: localizedText(R.string.ui_connection_error)
                if (SocialSession.token == null && SocialSession.loginNotice == null) SocialSession.loginNotice = error
            }
        }
    }
    galleryBar?.let { bar ->
        bar.filters = filters
        bar.onFilters = { selection ->
            if (selection.valid && selection != filters) {
                filters = selection
                cursor = null
                nextCursor = null
                endReached = false
                pageLoaded = false
                posts = emptyList()
            }
        }
        bar.onCreate = {
            groupText = ""
            groupPin = ""
            draftCategories = emptyList()
            draftTags = emptyList()
            groupDialog = "create"
        }
        bar.onRecords = { showRecords = true }
        bar.onImport = { showImport = true }
        bar.loading = groupsLoading
        bar.options = if (authenticated) {
            groups.map { WorkspaceOption(it.id, it.name, it.role) }
        } else {
            emptyList()
        }
        bar.selectedId = groupId
        bar.publishEnabled = !loading && !publishing && !groupsLoading && groups.isNotEmpty()
        val currentGroup = groups.firstOrNull { it.id == groupId }
        val iCanInvite = currentGroup != null && GroupAdminPolicy.canInvite(currentGroup.role, currentGroup.canInvite)
        bar.showInvite = groupId != null && iCanInvite
        bar.showAdmin = groupId != null && iCanInvite
        bar.onSelect = { selectedGroup ->
            if (selectedGroup != groupId) {
                groupId = selectedGroup
                SocialSession.workWorkspaceId = selectedGroup
                posts = emptyList()
                pageLoaded = false
                cursor = null
                nextCursor = null
                endReached = false
            }
        }
        bar.onPublish = {
            if (groupId == null) {
                error = localizedText(R.string.ui_select_a_workspace_to_publish)
            } else {
                workPublishMenu = true
            }
        }
        bar.onInvite = {
            groupText = ""
            groupPin = ""
            error = ""
            groupDialog = "invite"
            inviteLoading = true
            runRequest {
                try {
                    groupText = repository.invite(requireNotNull(groupId))
                    groupPin = if (iCanInvite) {
                        try {
                            repository.pin(requireNotNull(groupId))
                        } catch (_: Exception) {
                            ""
                        }
                    } else {
                        ""
                    }
                } finally {
                    inviteLoading = false
                }
            }
        }
        bar.onAdmin = { showAdministration = true }
    }
    var showAccountEntry by remember { mutableStateOf(false) }
    if (!authenticated) {
        if (showAccountEntry) {
            AccountEntry(viewModel, onSuccess = { authenticated = true }, onBack = { showAccountEntry = false })
            return
        }
        if (LocalAccountEntry(viewModel, onSuccess = { authenticated = true })) return
        LaunchedEffect(Unit) {
            SocialSession.loginNotice?.let {
                error = it
                SocialSession.loginNotice = null
            }
        }
        FacebookAccessScreen(loginBusy, error, entryConsent, onConsentChange = { entryConsent = it }, onLogin = {
            startFacebookAccess(
                context,
                scope,
                viewModel,
                onBusy = { loginBusy = it },
                onError = { error = it },
                onSuccess = {
                    // Set before SocialSession.active flips: the host-shell gallery
                    // instance reads it on mount.
                    SocialSession.freshLogin = true
                    runRequest {
                        withContext(Dispatchers.IO) { SocialSession.request("faces/consent", JSONObject().put("confirm", true)) }
                        authenticated = true
                    }
                }
            )
        }, onGuest = {
            showAccountEntry = true
        }, onWelcome = onWelcome)
        return
    }
    if (SocialSession.passwordAccount && !SocialSession.passwordAccountConfirmed) {
        RestoredAccountSession(local = false, onConfirmed = { SocialSession.passwordAccountConfirmed = true })
        return
    }
    if (BuildConfig.LOCAL_DEVELOPMENT && SocialSession.localAccount && !SocialSession.localAccountConfirmed) {
        RestoredAccountSession(local = true, onConfirmed = { SocialSession.localAccountConfirmed = true })
        return
    }
    LaunchedEffect(authenticated) {
        if (authenticated && !SocialSession.isGuest && !SocialSession.localEntryAllowed && !SocialSession.accountEntryAllowed && (faceCaptureDone == null || identityVerified == null)) {
            try {
                val status = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("faces/consent")) }
                if (resumedSession && !status.optBoolean("consented") && !faceConsentAsk) faceConsentAsk = true
                faceCaptureDone = status.optBoolean("face_capture_done")
                identityVerified = status.optBoolean("identity_verified")
                if (!SocialSession.freshLogin && faceCaptureDone == false) requireFreshLogin()
            } catch (e: Exception) { /* Face search stays unavailable until consent succeeds. */ }
        }
    }
    if (!SocialSession.isGuest && !SocialSession.localEntryAllowed && !SocialSession.accountEntryAllowed && (faceCaptureDone != true || identityVerified != true || deniedLastTime)) {
        if (faceCaptureDone == null || identityVerified == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        } else {
            FaceCaptureScreen(
                hasCapture = faceCaptureDone == true && !deniedLastTime,
                onDone = {
                    faceCaptureDone = true
                    identityVerified = true
                    deniedLastTime = false
                    SocialSession.freshLogin = false
                },
                onDenied = { message ->
                    SocialSession.clear()
                    if (!BuildConfig.LOCAL_DEVELOPMENT) com.facebook.login.LoginManager.getInstance().logOut()
                    authenticated = false
                    posts = emptyList()
                    faceCaptureDone = null
                    identityVerified = null
                    deniedLastTime = true
                    SocialSession.loginNotice = message
                },
                allowPhoto = SocialSession.freshLogin,
                onRequireLogin = { requireFreshLogin() }
            )
        }
        return
    }
    LaunchedEffect(capturePublicationRevision) {
        if (capturePublicationRevision > 0) {
            cursor = null
            endReached = false
            revision++
        }
    }
    LaunchedEffect(authenticated, groupId, revision, cursor, filters) {
        if (!authenticated) return@LaunchedEffect
        if (cursor != null && endReached) return@LaunchedEffect
        val requestedGroup = groupId
        val requestedFilters = filters
        val requestedCursor = cursor
        val requestedRevision = revision
        fun isCurrentRequest() = authenticated && groupId == requestedGroup &&
            filters == requestedFilters && cursor == requestedCursor && revision == requestedRevision
        loading = true
        pageFailed = false
        error = ""
        try {
            val page = repository.page(requestedGroup, requestedCursor, requestedFilters)
            coroutineContext.ensureActive()
            if (!isCurrentRequest()) return@LaunchedEffect
            posts = if (requestedCursor == null) page.publications else (posts + page.publications).distinctBy { it.id }
            nextCursor = page.nextCursor
            endReached = nextCursor == null
            liked = posts.filter { it.liked }.map { it.id }.toSet()
        } catch (e: Exception) {
            if (e is kotlinx.coroutines.CancellationException) throw e
            coroutineContext.ensureActive()
            if (isCurrentRequest()) {
                pageFailed = true
                error = e.message.orEmpty()
            }
        } finally {
            if (isActive && isCurrentRequest()) {
                loading = false
                pageLoaded = true
            }
        }
    }
    LaunchedEffect(authenticated, revision) {
        if (!authenticated) return@LaunchedEffect
        groupsLoading = true
        try {
            groups = repository.groups()
            if (groupId == null && groups.size == 1) {
                groupId = groups.first().id
                SocialSession.workWorkspaceId = groupId
            }
        } catch (e: Exception) {
            if (e is kotlinx.coroutines.CancellationException) throw e
            error = e.message.orEmpty()
        } finally {
            groupsLoading = false
        }
    }
    if (showRecords && groupId != null) {
        WorkspaceRecords(groupId!!, canWrite = groups.firstOrNull { it.id == groupId }?.role in setOf("admin", "register"), onBack = { showRecords = false })
        return
    }
    Column(Modifier.fillMaxSize()) {
        if (selected == null) galleryBar?.let { GalleryActions(it) }
        NoticeEffect(error, { error = "" })
        if (publishing) LinearProgressIndicator(Modifier.fillMaxWidth())
        if (posts.isEmpty() && (loading || !pageLoaded) && error.isBlank()) {
            LazyVerticalGrid(columns = GridCells.Fixed(3), modifier = Modifier.weight(1f)) {
                items(9) { SkeletonBlock(Modifier.padding(1.dp).aspectRatio(0.75f)) }
            }
        } else if (pageFailed && posts.isEmpty()) {
            TextButton(onClick = { revision++ }) { Text(localizedText(R.string.ui_retry)) }
        } else if (authenticated && posts.isEmpty() && !loading && pageLoaded && error.isBlank()) {
            Box(Modifier.fillMaxWidth().weight(1f), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Icon(Icons.Default.PhotoLibrary, null, modifier = Modifier.size(58.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(localizedText(if (filters.active) R.string.gallery_no_results else R.string.ui_no_publications_in_this_workspace_yet), color = MaterialTheme.colorScheme.onSurfaceVariant)
                    if (groupsLoading) {
                        SkeletonList(Modifier.padding(16.dp), rows = 2)
                    } else if (groups.isEmpty()) {
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(onClick = {
                                groupText = ""
                                groupPin = ""
                                draftCategories = emptyList()
                                draftTags = emptyList()
                                groupDialog = "create"
                            }) { Text(localizedText(R.string.ui_create_group)) }
                            Button(onClick = {
                                groupText = ""
                                groupPin = ""
                                groupDialog = "join"
                            }) { Text(localizedText(R.string.ui_join)) }
                        }
                    }
                }
            }
        } else {
            LazyVerticalGrid(columns = GridCells.Fixed(3), modifier = Modifier.weight(1f)) {
                items(posts, key = { it.id }) { post ->
                    PublicationThumbnail(post, Modifier.padding(1.dp).aspectRatio(0.75f)) { selected = post }
                }
                if (authenticated && posts.isNotEmpty()) {
                    item(span = { GridItemSpan(maxLineSpan) }) {
                        val loadMore = GalleryPagingPolicy.shouldLoadMore(loading, endReached)
                        Box(Modifier.fillMaxWidth().heightIn(min = 56.dp), contentAlignment = Alignment.Center) {
                            if (loading) {
                                CircularProgressIndicator(Modifier.size(24.dp))
                            } else if (!loadMore) {
                                Text(
                                    localizedText(R.string.ui_no_more_publications),
                                    style = MaterialTheme.typography.labelMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            } else {
                                LaunchedEffect(posts.size, groupId) { cursor = nextCursor }
                            }
                        }
                    }
                }
            }
        }
    }
    LaunchedEffect(selected) {
        onViewerChange(selected != null)
        comments = emptyList()
        val post = selected ?: return@LaunchedEffect
        commentsLoading = true
        try {
            comments = repository.comments(post.id)
        } catch (failure: Exception) {
            if (failure is kotlinx.coroutines.CancellationException) throw failure
            error = failure.message.orEmpty()
        } finally {
            commentsLoading = false
        }
    }
    selected?.let { post ->
        val likedNow = post.id in liked
        MediaViewerScreen(
            title = post.caption.display(),
            mediaUrl = "${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/${post.mediaUrl}",
            thumbnailUrl = "${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/${post.thumbnailUrl}",
            mimeType = post.mimeType,
            authToken = SocialSession.token,
            noteText = post.note.display(),
            noteSource = post.noteSource,
            metaLines = listOf(
                post.classificationText(),
                post.ownerName.let { if (it.isNotBlank()) localizedText(R.string.ui_by_1_s, it) else "" },
                post.publishedAt.substringBefore("T").let { if (it.isNotBlank()) localizedText(R.string.ui_published_on_1_s, it) else "" }
            ),
            commentsLoading = commentsLoading,
            comments = comments,
            onCommentClick = {
                reply = it
                interaction = "comment"
            },
            topActions = {
                IconButton(onClick = { interaction = if (likedNow) "unlike" else "like" }) {
                    Icon(if (likedNow) Icons.Filled.Favorite else Icons.Filled.FavoriteBorder, contentDescription = if (likedNow) localizedText(R.string.ui_unlike) else "Like", tint = Color.White)
                }
                IconButton(onClick = {
                    interaction = "comment"
                    reply = null
                }) { Icon(Icons.Filled.Comment, contentDescription = localizedText(R.string.ui_comment), tint = Color.White) }
                IconButton(onClick = { interaction = "report" }) { Icon(Icons.Filled.Flag, contentDescription = localizedText(R.string.ui_report), tint = Color.White) }
                if (post.owned) {
                    IconButton(onClick = { editingClassification = post }) { Icon(Icons.Filled.Label, localizedText(R.string.catalog_classify), tint = Color.White) }
                    IconButton(onClick = { interaction = "work" }) { Icon(Icons.Filled.Group, contentDescription = localizedText(R.string.ui_share_with_group), tint = Color.White) }
                    IconButton(onClick = { interaction = "remove" }) { Icon(Icons.Filled.Delete, contentDescription = localizedText(R.string.ui_delete), tint = Color.White) }
                }
            },
            onClose = { selected = null }
        )
        interaction?.let { action ->
            var shareGroup by remember(action) { mutableStateOf<String?>(null) }
            var shareClassification by remember(shareGroup) { mutableStateOf(PublicationClassification()) }
            var shareValid by remember(shareGroup) { mutableStateOf(false) }
            AlertDialog(
                onDismissRequest = { interaction = null },
                title = { Text(if (reply != null) localizedText(R.string.ui_reply) else action) },
                text = {
                    if (action in listOf("comment", "report")) {
                        OutlinedTextField(value = text, onValueChange = { text = it }, label = { Text(localizedText(R.string.ui_text)) })
                    } else if (action == "work") {
                        Column(Modifier.verticalScroll(rememberScrollState())) {
                            Text(localizedText(R.string.ui_choose_the_group_to_share_this_publication_with))
                            if (groupsLoading) {
                                SkeletonList(rows = 3)
                            } else if (groups.isEmpty()) {
                                Text(localizedText(R.string.ui_create_or_join_a_group_from_work))
                            }
                            shareGroup?.let { ClassificationFields(it, shareClassification, onValid = { shareValid = it }) { value -> shareClassification = value } }
                            groups.forEach { group ->
                                TextButton(onClick = { shareGroup = group.id }) {
                                    Text((if (shareGroup == group.id) "✓ " else "") + group.name)
                                }
                            }
                        }
                    } else {
                        Text(
                            if (action == "remove") {
                                localizedText(R.string.ui_the_publication_will_no_longer_appear_in_the_gallery_the_original_evidence_is_preserv)
                            } else {
                                localizedText(R.string.ui_confirm_reaction)
                            }
                        )
                    }
                },
                confirmButton = {
                    TextButton(enabled = action != "work" || shareValid, onClick = {
                        runRequest {
                            when (action) {
                                "work" -> repository.share(post.id, requireNotNull(shareGroup) { localizedText(R.string.ui_select_a_group_in_work) }, shareClassification)
                                "remove" -> repository.remove(post.id)
                                else -> repository.interact(post.id, action, text, reply)
                            }
                            if (action == "like") liked = liked + post.id
                            if (action == "unlike") liked = liked - post.id
                            if (action == "comment") {
                                comments = repository.comments(post.id)
                            }
                            interaction = null
                            text = ""
                            if (action in listOf("work", "remove")) {
                                selected = null
                                cursor = null
                                endReached = false
                                revision++
                            }
                        }
                    }) { Text(localizedText(R.string.ui_confirm)) }
                },
                dismissButton = { TextButton(onClick = { interaction = null }) { Text(localizedText(R.string.ui_cancel)) } }
            )
        }
    }
    if (workPublishMenu) {
        AlertDialog(
            onDismissRequest = { workPublishMenu = false },
            title = { Text(localizedText(R.string.ui_publish_to_workspace)) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(Modifier.fillMaxWidth().clickable { onWorkCameraOption() }.padding(vertical = 12.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Icon(Icons.Filled.CameraAlt, contentDescription = null)
                        Text(localizedText(R.string.ui_take_photo))
                    }
                    Row(
                        Modifier.fillMaxWidth().clickable {
                            workPublishMenu = false
                            pickWorkPublication.launch("image/*")
                        }.padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(Icons.Filled.PhotoLibrary, contentDescription = null)
                        Text(localizedText(R.string.ui_choose_image))
                    }
                }
            },
            confirmButton = {}
        )
    }
    if (workNoteDialog) {
        workPendingPhoto?.let { pending ->
            PublishNoteDialog(
                workspaceId = groupId.orEmpty(),
                onPublish = { noteText, noteSource, classification ->
                    workNoteDialog = false
                    workPendingPhoto = null
                    uploadWorkPublication(pending, noteText, noteSource, classification)
                },
                onDismiss = {
                    workNoteDialog = false
                    workPendingPhoto = null
                }
            )
        }
    }
    groupDialog?.let { action ->
        AlertDialog(
            onDismissRequest = { groupDialog = null },
            title = { Text(if (action == "invite") localizedText(R.string.ui_invitation_code) else localizedText(R.string.ui_work_group)) },
            text = {
                Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (action == "create") CatalogDraftFields(draftCategories, draftTags, { draftCategories = it }, { draftTags = it })
                    if (action == "invite" && error.isNotBlank()) {
                        NoticeEffect(error, {})
                    } else if (action == "invite" && inviteLoading) {
                        SkeletonLines(rows = 3)
                    } else if (action == "created") {
                        Text(localizedText(R.string.ui_share_this_pin_so_others_can_join_the_group))
                        OutlinedTextField(value = groupPin, onValueChange = {}, readOnly = true, label = { Text(localizedText(R.string.ui_group_pin)) })
                    } else {
                        OutlinedTextField(value = groupText, onValueChange = { groupText = it }, readOnly = action == "invite", label = { Text(if (action == "create") localizedText(R.string.ui_name) else localizedText(R.string.ui_code_or_pin)) })
                        if (action == "invite" && groupPin.isNotBlank()) {
                            OutlinedTextField(value = groupPin, onValueChange = {}, readOnly = true, label = { Text(localizedText(R.string.ui_group_pin)) })
                        }
                    }
                }
            },
            confirmButton = {
                if ((action == "invite" && !inviteLoading && groupText.isNotBlank()) || action == "created") {
                    TextButton(onClick = {
                        val code = if (action == "created") groupPin else groupText
                        val clipboard = context.getSystemService(android.content.Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
                        clipboard.setPrimaryClip(android.content.ClipData.newPlainText("RealityOS", code))
                        AppNotices.show(localizedText(R.string.ui_copied), NoticeKind.SUCCESS)
                    }) { Icon(Icons.Default.ContentCopy, localizedText(R.string.ui_copy)) }
                    TextButton(onClick = {
                        val code = if (action == "created") groupPin else groupText
                        context.startActivity(
                            android.content.Intent.createChooser(
                                android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                                    type = "text/plain"
                                    putExtra(android.content.Intent.EXTRA_TEXT, localizedText(R.string.share_group_invitation, code))
                                },
                                localizedText(R.string.ui_invite)
                            )
                        )
                    }) { Text(localizedText(R.string.share_invitation)) }
                }
                TextButton(onClick = {
                    if (action == "create" && (draftCategories.isEmpty() || draftTags.isEmpty())) {
                        error = localizedText(R.string.catalog_owner_needed)
                    } else if (action == "invite" || action == "created") {
                        groupDialog = null
                    } else {
                        runRequest {
                            if (action == "create") {
                                val created = repository.createGroup(groupText, draftCategories, draftTags)
                                groupId = created.id
                                SocialSession.workWorkspaceId = groupId
                                showImport = true
                                groupPin = created.joinPin
                                groupText = ""
                                groupDialog = "created"
                            } else {
                                groupId = repository.joinGroup(groupText)
                                SocialSession.workWorkspaceId = groupId
                                showImport = true
                                groupDialog = null
                                groupText = ""
                            }
                            groups = repository.groups()
                        }
                    }
                }) { Text(localizedText(R.string.ui_accept)) }
            },
            dismissButton = { TextButton(onClick = { groupDialog = null }) { Text(localizedText(R.string.ui_cancel)) } }
        )
    }
    if (faceConsentAsk) {
        AlertDialog(
            onDismissRequest = { faceConsentAsk = false },
            title = { Text(stringResource(R.string.face_consent_title)) },
            text = { Text(stringResource(R.string.face_consent_body)) },
            confirmButton = {
                TextButton(onClick = {
                    runRequest {
                        withContext(Dispatchers.IO) { SocialSession.request("faces/consent", JSONObject().put("confirm", true)) }
                        faceConsentAsk = false
                    }
                }) { Text(stringResource(R.string.face_consent_accept)) }
            },
            dismissButton = { TextButton(onClick = { faceConsentAsk = false }) { Text(stringResource(R.string.face_consent_later)) } }
        )
    }
    editingClassification?.let { post ->
        ClassificationDialog(post.workspaceId, post.classification, onSave = { value ->
            selected = repository.classify(post, value)
            cursor = null
            endReached = false
            revision++
        }, onClose = { editingClassification = null })
    }
    LaunchedEffect(showAdministration) { onAdminDrawerChange(showAdministration) }
    DisposableEffect(Unit) { onDispose { onAdminDrawerChange(false) } }
    if (showImport && groupId != null && groupDialog == null) {
        GroupPublicationPicker(groupId!!, onClose = { showImport = false }, onImported = {
            cursor = null
            endReached = false
            revision++
        })
    }
    if (showAdministration && groupId != null) {
        SocialAdministration(
            groupId!!,
            onDismiss = { showAdministration = false },
            onChanged = {
                cursor = null
                endReached = false
                revision++
            },
            onGroupDeleted = {
                groupId = null
                showAdministration = false
                cursor = null
                endReached = false
                revision++
            }
        )
    }
}
