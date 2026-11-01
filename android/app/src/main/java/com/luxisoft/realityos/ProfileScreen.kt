package com.luxisoft.realityos

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.widget.Toast
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.AnnotatedString
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

private data class EditableProfileLink(val label: String = "", val url: String = "")

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ProfileScreen(
    userId: String? = null,
    onBack: (() -> Unit)? = null,
    viewModel: RealityViewModel? = null,
    onViewerChange: (Boolean) -> Unit = {},
    onEditDrawerChange: (Boolean) -> Unit = {},
) {
    val context = LocalContext.current
    val clipboardManager = LocalClipboardManager.current
    val scope = rememberCoroutineScope()
    val ownProfile = userId == null
    var profile by remember(userId) { mutableStateOf<JSONObject?>(null) }
    var busy by remember { mutableStateOf(false) }
    var profileLoading by remember(userId) { mutableStateOf(true) }
    var mediaLoaded by remember(userId) { mutableStateOf(false) }
    var answerLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    var headline by remember { mutableStateOf("") }
    var biography by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var website by remember { mutableStateOf("") }
    var links by remember { mutableStateOf(listOf<EditableProfileLink>()) }
    var webUrl by remember { mutableStateOf<String?>(null) }
    var question by remember { mutableStateOf("") }
    var answer by remember { mutableStateOf("") }
    var media by remember(userId) { mutableStateOf<List<JSONObject>>(emptyList()) }
    var mediaCursor by remember(userId) { mutableStateOf<String?>(null) }
    var mediaBusy by remember(userId) { mutableStateOf(false) }
    var selectedMedia by remember { mutableStateOf<JSONObject?>(null) }
    var profileSectionExpanded by rememberSaveable(userId) { mutableStateOf(false) }
    var publishMenuExpanded by remember { mutableStateOf(false) }
    var pendingPhoto by remember { mutableStateOf<PendingPublishPhoto?>(null) }
    var showNoteDialog by remember { mutableStateOf(false) }
    var captureUri by remember { mutableStateOf<Uri?>(null) }

    fun applyProfile(value: JSONObject) {
        profile = value
        if (ownProfile) {
            SocialSession.profilePictureUrl = value.optString("picture_url")
                .takeIf { it.isNotBlank() && it != "null" }
        }
        headline = value.optString("headline")
        biography = value.optString("biography")
        phone = value.optString("phone")
        website = value.optString("website")
        val values = value.optJSONArray("social_links") ?: JSONArray()
        links = (0 until values.length()).map { index ->
            values.getJSONObject(index).let { EditableProfileLink(it.optString("label"), it.optString("url")) }
        }
    }

    fun load() {
        scope.launch {
            profileLoading = true
            busy = true
            error = ""
            try {
                val path = if (ownProfile) "me/profile" else "profiles/$userId"
                val loaded = withContext(Dispatchers.IO) { JSONObject(SocialSession.request(path)) }
                applyProfile(loaded)
            } catch (failure: Exception) { error = failure.message.orEmpty() }
            finally { busy = false; profileLoading = false }
        }
    }

    LaunchedEffect(userId) { load() }
    LaunchedEffect(selectedMedia) { onViewerChange(selectedMedia != null) }

    fun loadMedia(reset: Boolean = false) {
        val targetId = profile?.optString("user_id").orEmpty()
        if (targetId.isBlank() || mediaBusy || (!reset && mediaCursor == null && media.isNotEmpty())) return
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
            } catch (failure: Exception) { error = failure.message.orEmpty() }
            finally { mediaBusy = false; mediaLoaded = true }
        }
    }

    LaunchedEffect(profile?.optString("user_id")) {
        if (profile?.optString("user_id").orEmpty().isNotBlank()) loadMedia(reset = true)
    }

    val pickCv = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            busy = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error(localizedText(R.string.ui_could_not_read_the_resume))
                val mime = context.contentResolver.getType(uri)
                    ?: if (uri.toString().endsWith(".pdf", true)) "application/pdf"
                    else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                val name = uri.lastPathSegment?.substringAfterLast('/') ?: "cv"
                val loaded = withContext(Dispatchers.IO) {
                    JSONObject(SocialSession.requestMultipart("me/profile/cv", emptyMap(), bytes, name, mime))
                }
                applyProfile(loaded)
            } catch (failure: Exception) { error = failure.message.orEmpty() }
            finally { busy = false }
        }
    }

    val publicationUploader = rememberPublicationUploader(onPublished = { loadMedia(reset = true) }, onBusy = { busy = it })
    PublicationUploadDialog(publicationUploader)
    fun uploadPublication(photo: PendingPublishPhoto, noteText: String, noteSource: String) {
        publicationUploader.submit(photo, noteText, noteSource, "home")
    }

    fun stagePhoto(bytes: ByteArray, mime: String, name: String) {
        pendingPhoto = PendingPublishPhoto(bytes, mime, name)
        showNoteDialog = true
    }

    val pickPublication = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
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
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) launchPhoneCamera()
        else askPublishCamera.launch(Manifest.permission.CAMERA)
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
                if (bytes != null) stagePhoto(bytes, "image/jpeg", "camara.jpg")
                else launchPhoneCameraChecked()
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                busy = false
            }
        }
    }

    fun openLink(url: String, facebook: Boolean = false) {
        if (url.isBlank()) return
        if (facebook) {
            try {
                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).setPackage("com.facebook.katana"))
                return
            } catch (_: ActivityNotFoundException) { }
        }
        webUrl = url
    }

    if (webUrl != null) {
        ProfileWebView(webUrl!!, onBack = { webUrl = null })
        return
    }

    val current = profile
    if (profileLoading && current == null) {
        Column(Modifier.fillMaxSize().padding(20.dp)) {
            if (onBack != null) IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, localizedText(R.string.ui_back)) }
            SkeletonProfile()
        }
        return
    }
    val editDrawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    LaunchedEffect(editDrawerState.isOpen) { onEditDrawerChange(editDrawerState.isOpen) }
    DisposableEffect(Unit) { onDispose { onEditDrawerChange(false) } }

    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        ModalNavigationDrawer(
            drawerState = editDrawerState,
            gesturesEnabled = editDrawerState.isOpen,
            drawerContent = {
                CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
                    ProfileEditDrawer(
                        headline = headline,
                        onHeadlineChange = { headline = it },
                        biography = biography,
                        onBiographyChange = { biography = it },
                        phone = phone,
                        onPhoneChange = { phone = it },
                        website = website,
                        onWebsiteChange = { website = it },
                        links = links,
                        onLinksChange = { links = it },
                        cv = current?.optJSONObject("cv") ?: JSONObject(),
                        busy = busy,
                        onClose = { scope.launch { editDrawerState.close() } },
                        onSave = {
                            scope.launch {
                                busy = true
                                error = ""
                                try {
                                    val payload = JSONObject().put("headline", headline).put("biography", biography)
                                        .put("phone", phone).put("website", website).put("social_links", JSONArray().apply {
                                            links.filter { it.label.isNotBlank() && it.url.isNotBlank() }
                                                .forEach { put(JSONObject().put("label", it.label).put("url", it.url)) }
                                        })
                                    applyProfile(withContext(Dispatchers.IO) {
                                        JSONObject(SocialSession.requestJson("me/profile", "PATCH", payload))
                                    })
                                    editDrawerState.close()
                                } catch (failure: Exception) {
                                    error = failure.message.orEmpty()
                                } finally {
                                    busy = false
                                }
                            }
                        },
                    )
                }
            },
        ) {
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
                LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        if (onBack != null) {
            item {
                IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, localizedText(R.string.ui_back)) }
            }
        }
        if (busy) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
        if (error.isNotBlank()) item { Text(error, color = MaterialTheme.colorScheme.error) }
        if (current != null) {
            item {
                Column(modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                    val picture = current.optString("picture_url").takeIf { it.isNotBlank() && it != "null" }
                    Box(modifier = Modifier.size(if (ownProfile) 90.dp else 82.dp)) {
                        if (picture != null) DatabaseImage(
                            model = profileImageRequest(context, picture),
                            contentDescription = current.optString("display_name"),
                            contentScale = ContentScale.Crop,
                            modifier = Modifier.size(82.dp).clip(CircleShape),
                        ) else Icon(
                            Icons.Default.AccountCircle,
                            contentDescription = null,
                            modifier = Modifier.size(82.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        if (ownProfile) {
                            FilledIconButton(
                                onClick = { scope.launch { editDrawerState.open() } },
                                colors = IconButtonDefaults.filledIconButtonColors(
                                    containerColor = MaterialTheme.colorScheme.primary,
                                    contentColor = MaterialTheme.colorScheme.onPrimary,
                                ),
                                modifier = Modifier
                                    .align(Alignment.BottomEnd)
                                    .size(32.dp),
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Edit,
                                    contentDescription = localizedText(R.string.ui_edit_profile),
                                    modifier = Modifier.size(18.dp),
                                )
                            }
                        }
                    }
                    Column(
                        modifier = Modifier.weight(1f),
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                current.optString("display_name"),
                                style = MaterialTheme.typography.titleLarge,
                                modifier = Modifier.weight(1f),
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                            IconButton(
                                onClick = { profileSectionExpanded = !profileSectionExpanded },
                                modifier = Modifier.size(36.dp),
                            ) {
                                Icon(
                                    imageVector = if (profileSectionExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                                    contentDescription = if (profileSectionExpanded) localizedText(R.string.ui_hide_information) else localizedText(R.string.ui_show_information),
                                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                        val location = current.optString("location").takeIf { it.isNotBlank() && it != "null" }
                        val hometown = current.optString("hometown").takeIf { it.isNotBlank() && it != "null" }
                        if (location != null || hometown != null) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp),
                            ) {
                                Row(
                                    modifier = Modifier.weight(1f),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(5.dp),
                                ) {
                                    if (location != null) {
                                        Icon(
                                            Icons.Default.LocationOn,
                                            contentDescription = localizedText(R.string.ui_location),
                                            modifier = Modifier.size(15.dp),
                                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                        )
                                        Text(
                                            location,
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                        )
                                    }
                                }
                                Row(
                                    modifier = Modifier.weight(1f),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(5.dp),
                                ) {
                                    if (hometown != null) {
                                        Icon(
                                            Icons.Default.Home,
                                            contentDescription = localizedText(R.string.ui_hometown),
                                            modifier = Modifier.size(15.dp),
                                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                        )
                                        Text(
                                            hometown,
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                        )
                                    }
                                }
                            }
                        }
                        current.optString("email").takeIf { it.isNotBlank() && it != "null" }?.let { email ->
                            Row(
                                modifier = Modifier
                                    .padding(top = 7.dp)
                                    .clickable {
                                        clipboardManager.setText(AnnotatedString(email))
                                        Toast.makeText(context, localizedText(R.string.ui_email_copied), Toast.LENGTH_SHORT).show()
                                    },
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp),
                            ) {
                                Icon(
                                    Icons.Default.Email,
                                    contentDescription = null,
                                    modifier = Modifier.size(15.dp),
                                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                                Text(
                                    email,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                            }
                        }
                    }
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        val facebook = current.optString("facebook_link")
                        if (facebook.isNotBlank() && facebook != "null") {
                            IconButton(onClick = { openLink(facebook, true) }) {
                                Icon(
                                    imageVector = Icons.Default.Facebook,
                                    contentDescription = localizedText(R.string.ui_open_facebook),
                                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                        if (ownProfile) {
                            IconButton(
                                onClick = { pickCv.launch(arrayOf("application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")) },
                                enabled = !busy,
                            ) {
                                Icon(
                                    imageVector = Icons.Default.UploadFile,
                                    contentDescription = if (current.optJSONObject("cv")?.optBoolean("present") == true) localizedText(R.string.ui_update_resume) else localizedText(R.string.ui_upload_resume),
                                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }
                    }
                    AnimatedVisibility(
                        visible = profileSectionExpanded,
                        enter = expandVertically(),
                        exit = shrinkVertically(),
                    ) {
                        Column(
                            modifier = Modifier.padding(top = 12.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            ProfileInformation(
                                profile = current,
                                headline = headline,
                                phone = phone,
                                website = website,
                                links = links,
                                onOpenLink = { openLink(it) },
                            )
                            if (biography.isNotBlank()) {
                                Text(biography, style = MaterialTheme.typography.bodyLarge)
                            }
                        }
                    }
                }
            }
            val friends = current.optJSONArray("friends") ?: JSONArray()
            if (friends.length() > 0) item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(localizedText(R.string.ui_friends), style = MaterialTheme.typography.titleMedium)
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        (0 until minOf(friends.length(), 6)).forEach { index ->
                            val friend = friends.getJSONObject(index)
                            Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.width(54.dp).clickable {
                                friend.optString("profile_link").takeIf { it.isNotBlank() && it != "null" }?.let { openLink(it, true) }
                            }) {
                                val avatar = friend.optString("picture_url")
                                if (avatar.isNotBlank() && avatar != "null") DatabaseImage(profileImageRequest(context, avatar), friend.optString("name"), Modifier.size(44.dp).clip(CircleShape), contentScale = ContentScale.Crop)
                                else Icon(Icons.Default.AccountCircle, null, Modifier.size(44.dp))
                                Text(friend.optString("name"), style = MaterialTheme.typography.labelSmall, maxLines = 1)
                            }
                        }
                    }
                }
            }
            if (!ownProfile) item {
                Card {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text(localizedText(R.string.ui_ask_about_this_profile), style = MaterialTheme.typography.titleMedium)
                        OutlinedTextField(question, { question = it }, label = { Text(localizedText(R.string.ui_e_g_how_much_do_they_know_about_architecture)) }, modifier = Modifier.fillMaxWidth())
                        Button(onClick = {
                            scope.launch {
                                busy = true; answerLoading = true; error = ""
                                try {
                                    val language = RealityExperienceStore(context).syncAccountLanguage().languageTag
                                    val response = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("profiles/search", JSONObject().put("question", question).put("user_id", userId).put("language", language))) }
                                    if (language != RealityExperienceStore(context).selectedLanguage().languageTag) return@launch
                                    answer = response.optString("answer") + if (response.optBoolean("simulated")) localizedText(R.string.ui_simulated) else ""
                                } catch (failure: Exception) { error = failure.message.orEmpty() }
                                finally { busy = false; answerLoading = false }
                            }
                        }, enabled = question.length >= 2 && !busy) { Text(localizedText(R.string.ui_ask)) }
                        if (answerLoading) SkeletonLines() else if (answer.isNotBlank()) Text(answer)
                    }
                }
            }
            item { HorizontalDivider(Modifier.padding(vertical = 4.dp)) }
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(localizedText(R.string.ui_publications), style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    if (ownProfile) {
                        Box {
                            IconButton(
                                onClick = { publishMenuExpanded = true },
                                enabled = !busy,
                            ) {
                                Icon(Icons.Default.Add, contentDescription = localizedText(R.string.ui_publish))
                            }
                            DropdownMenu(expanded = publishMenuExpanded, onDismissRequest = { publishMenuExpanded = false }) {
                                DropdownMenuItem(
                                    text = { Text(localizedText(R.string.ui_take_photo)) },
                                    leadingIcon = { Icon(Icons.Default.CameraAlt, contentDescription = null) },
                                    onClick = { onCameraOption() },
                                )
                                DropdownMenuItem(
                                    text = { Text(localizedText(R.string.ui_choose_image)) },
                                    leadingIcon = { Icon(Icons.Default.PhotoLibrary, contentDescription = null) },
                                    onClick = { publishMenuExpanded = false; pickPublication.launch("image/*") },
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
            items(media.chunked(3)) { row ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                    row.forEach { item ->
                        DatabaseImage(
                            model = profileImageRequest(context, item.optString("thumbnail_url")),
                            contentDescription = item.optString("caption"),
                            contentScale = ContentScale.Crop,
                            modifier = Modifier.weight(1f).aspectRatio(.78f).clickable { selectedMedia = item },
                        )
                    }
                    repeat(3 - row.size) { Spacer(Modifier.weight(1f)) }
                }
                if (row.lastOrNull()?.optString("id") == media.lastOrNull()?.optString("id") && mediaCursor != null && !mediaBusy) {
                    LaunchedEffect(media.size, mediaCursor) { loadMedia() }
                }
            }
            if (mediaBusy || !mediaLoaded) item { SkeletonGrid() }
        }
                }
                if (showNoteDialog) {
                    pendingPhoto?.let { pending ->
                        PublishNoteDialog(
                            onPublish = { noteText, noteSource ->
                                showNoteDialog = false
                                pendingPhoto = null
                                uploadPublication(pending, noteText, noteSource)
                            },
                            onDismiss = { showNoteDialog = false; pendingPhoto = null },
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
                            },
                        ),
                        onClose = { selectedMedia = null },
                    )
                }
            }
        }
    }
}

@Composable
private fun ProfileEditDrawer(
    headline: String,
    onHeadlineChange: (String) -> Unit,
    biography: String,
    onBiographyChange: (String) -> Unit,
    phone: String,
    onPhoneChange: (String) -> Unit,
    website: String,
    onWebsiteChange: (String) -> Unit,
    links: List<EditableProfileLink>,
    onLinksChange: (List<EditableProfileLink>) -> Unit,
    cv: JSONObject,
    busy: Boolean,
    onClose: () -> Unit,
    onSave: () -> Unit,
) {
    ModalDrawerSheet(
        modifier = Modifier.fillMaxHeight().widthIn(min = 320.dp, max = 360.dp),
        drawerContainerColor = MaterialTheme.colorScheme.surface,
    ) {
        LazyColumn(
            contentPadding = PaddingValues(start = 18.dp, top = 2.dp, end = 18.dp, bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            item {
                Row(
                    modifier = Modifier.fillMaxWidth().height(46.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(localizedText(R.string.ui_edit_profile), style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    IconButton(onClick = onClose) { Icon(Icons.Default.Close, localizedText(R.string.ui_close_editor)) }
                }
            }
            item { OutlinedTextField(headline, onHeadlineChange, label = { Text(localizedText(R.string.ui_headline)) }, modifier = Modifier.fillMaxWidth()) }
            item { OutlinedTextField(biography, onBiographyChange, label = { Text(localizedText(R.string.ui_biography)) }, minLines = 3, modifier = Modifier.fillMaxWidth()) }
            item { OutlinedTextField(phone, onPhoneChange, label = { Text(localizedText(R.string.ui_phone)) }, modifier = Modifier.fillMaxWidth()) }
            item { OutlinedTextField(website, onWebsiteChange, label = { Text(localizedText(R.string.ui_website)) }, modifier = Modifier.fillMaxWidth()) }
            items(links.indices.toList()) { index ->
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                        OutlinedTextField(
                            value = links[index].label,
                            onValueChange = { value ->
                                onLinksChange(links.toMutableList().also { it[index] = it[index].copy(label = value) })
                            },
                            label = { Text(localizedText(R.string.ui_social_network)) },
                            modifier = Modifier.weight(.4f),
                        )
                        IconButton(onClick = { onLinksChange(links.filterIndexed { itemIndex, _ -> itemIndex != index }) }) {
                            Icon(Icons.Default.Delete, localizedText(R.string.ui_remove_social_link))
                        }
                    }
                    OutlinedTextField(
                        value = links[index].url,
                        onValueChange = { value ->
                            onLinksChange(links.toMutableList().also { it[index] = it[index].copy(url = value) })
                        },
                        label = { Text(localizedText(R.string.ui_link)) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    OutlinedButton(onClick = { onLinksChange(links + EditableProfileLink()) }) { Text(localizedText(R.string.ui_add_social_link)) }
                    Button(onClick = onSave, enabled = !busy) { Text(localizedText(R.string.ui_save)) }
                }
            }
            item { HorizontalDivider(Modifier.padding(vertical = 8.dp)) }
            item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(localizedText(R.string.ui_resume), style = MaterialTheme.typography.titleMedium)
                    Text(
                        when (cv.optString("status")) {
                            "ready" -> localizedText(R.string.ui_updated_available_for_ai_questions)
                            "failed" -> localizedText(R.string.ui_processing_failed_you_can_retry)
                            "processing", "pending" -> localizedText(R.string.ui_updating_professional_information)
                            else -> localizedText(R.string.ui_you_have_not_uploaded_a_resume_yet)
                        },
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    cv.optString("filename").takeIf { it.isNotBlank() && it != "null" }?.let { filename ->
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Icon(Icons.Default.Description, contentDescription = null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(filename, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                    cv.optString("mime_type").takeIf { it.isNotBlank() && it != "null" }?.let { mimeType ->
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Icon(Icons.Default.InsertDriveFile, contentDescription = null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(mimeType.substringAfterLast('/'), style = MaterialTheme.typography.bodySmall)
                        }
                    }
                    cv.optString("updated_at").takeIf { it.isNotBlank() && it != "null" }?.let { updatedAt ->
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Icon(Icons.Default.Schedule, contentDescription = null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(localizedText(R.string.ui_updated_1_s, updatedAt.substringBefore('T')), style = MaterialTheme.typography.bodySmall)
                        }
                    }
                    cv.optString("analysis").takeIf { it.isNotBlank() && it != "null" }?.let { analysis ->
                        Text(localizedText(R.string.ui_analysis), style = MaterialTheme.typography.labelLarge)
                        Text(analysis, style = MaterialTheme.typography.bodyMedium)
                    }
                    cv.optString("error").takeIf { it.isNotBlank() && it != "null" }?.let { cvError ->
                        Text(cvError, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error)
                    }
                }
            }
        }
    }
}

private data class ProfileInfoItem(
    val label: String,
    val value: String,
    val icon: androidx.compose.ui.graphics.vector.ImageVector,
    val onClick: (() -> Unit)? = null,
)

@Composable
private fun ProfileInformation(
    profile: JSONObject,
    headline: String,
    phone: String,
    website: String,
    links: List<EditableProfileLink>,
    onOpenLink: (String) -> Unit,
) {
    val counts = profile.optJSONObject("counts") ?: JSONObject()
    val age = listOf(profile.optString("age_min"), profile.optString("age_max"))
        .filter { it.isNotBlank() && it != "null" }
        .distinct()
        .joinToString("–")
    val items = buildList {
        add(ProfileInfoItem(localizedText(R.string.ui_headline), headline, Icons.Default.Work))
        add(ProfileInfoItem(localizedText(R.string.ui_age), if (age.isBlank()) "" else localizedText(R.string.ui_1_s_years_old, age), Icons.Default.Badge))
        add(ProfileInfoItem(localizedText(R.string.ui_phone), phone, Icons.Default.Phone))
        add(ProfileInfoItem(localizedText(R.string.ui_birthday), profile.optString("birthday"), Icons.Default.Cake))
        add(ProfileInfoItem(localizedText(R.string.ui_gender), profile.optString("gender"), Icons.Default.Person))
        add(ProfileInfoItem(localizedText(R.string.ui_website), website, Icons.Default.Language) { onOpenLink(website) })
        links.forEach { link ->
            add(ProfileInfoItem(link.label.ifBlank { localizedText(R.string.ui_link) }, link.url, Icons.Default.Link) { onOpenLink(link.url) })
        }
        add(ProfileInfoItem(localizedText(R.string.ui_friends), counts.optString("friends"), Icons.Default.People))
        add(ProfileInfoItem(localizedText(R.string.ui_likes), counts.optString("likes"), Icons.Default.ThumbUp))
        add(ProfileInfoItem(localizedText(R.string.ui_photos), counts.optString("photos"), Icons.Default.PhotoLibrary))
        add(ProfileInfoItem("Videos", counts.optString("videos"), Icons.Default.VideoLibrary))
    }.filter { it.value.isNotBlank() && it.value != "null" }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        items.chunked(2).forEach { rowItems ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                rowItems.forEach { item ->
                    Row(
                        modifier = Modifier
                            .weight(1f)
                            .then(item.onClick?.let { onClick -> Modifier.clickable(onClick = onClick) } ?: Modifier)
                            .padding(vertical = 2.dp),
                        verticalAlignment = Alignment.Top,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Icon(
                            imageVector = item.icon,
                            contentDescription = item.label,
                            modifier = Modifier.size(19.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                item.label,
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                            Text(
                                item.value,
                                style = MaterialTheme.typography.bodySmall,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                    }
                }
                if (rowItems.size == 1) Spacer(Modifier.weight(1f))
            }
        }
    }
}

private fun profileMediaUrl(path: String): String {
    if (path.startsWith("http")) return path
    val base = BuildConfig.DEFAULT_REALITYOS_API_BASE_URL.trimEnd('/')
    return if (path.startsWith("/v1/")) {
        "${base.removeSuffix("/v1")}$path"
    } else {
        "$base/${path.trimStart('/')}"
    }
}

internal fun profileImageRequest(context: android.content.Context, path: String): coil.request.ImageRequest =
    coil.request.ImageRequest.Builder(context)
        .data(profileMediaUrl(path))
        .addHeader("Authorization", "Bearer ${SocialSession.token}")
        .build()

@Composable
private fun ProfileWebView(url: String, onBack: () -> Unit) {
    Column(Modifier.fillMaxSize()) {
        Surface(color = MaterialTheme.colorScheme.surface) {
            Row(Modifier.fillMaxWidth().padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, localizedText(R.string.ui_back)) }
                Text(localizedText(R.string.ui_browser), style = MaterialTheme.typography.titleMedium)
            }
        }
        AndroidView(
            factory = { context ->
                WebView(context).apply {
                    webViewClient = WebViewClient()
                    settings.javaScriptEnabled = true
                    settings.allowFileAccess = false
                    settings.allowContentAccess = false
                    loadUrl(url)
                }
            },
            update = { if (it.url != url) it.loadUrl(url) },
            modifier = Modifier.fillMaxSize(),
        )
    }
}
