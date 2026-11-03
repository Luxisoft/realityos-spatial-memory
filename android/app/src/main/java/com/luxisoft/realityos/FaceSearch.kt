package com.luxisoft.realityos

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

private fun faceEvidenceUrl(thumbnailPath: String): String {
    val clean = thumbnailPath.trim()
    if (clean.startsWith("http")) return clean
    val origin = BuildConfig.DEFAULT_REALITYOS_API_BASE_URL.trimEnd('/').removeSuffix("/v1")
    return origin + (if (clean.startsWith("/")) clean else "/$clean")
}

/** Consent-gated 1:N face search over workspace members. Probe bytes stay ephemeral. */
@Composable
@SuppressLint("LocalContextGetResourceValueCall")
internal fun FaceSearch(onBack: () -> Unit, onOpenProfile: (String) -> Unit = {}, initialProbe: Uri? = null, initialWorkspaceId: String = "") {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var workspaces by remember { mutableStateOf(listOf<JSONObject>()) }
    var workspaceId by remember(initialWorkspaceId) { mutableStateOf(initialWorkspaceId.ifBlank { SocialSession.workspaceId.orEmpty() }) }
    var probeUri by remember(initialProbe) { mutableStateOf(initialProbe) }
    var probeMime by remember { mutableStateOf("image/jpeg") }
    var matches by remember { mutableStateOf(listOf<JSONObject>()) }
    var recordMatches by remember { mutableStateOf(listOf<JSONObject>()) }
    var searched by remember { mutableStateOf(false) }
    var simulated by remember { mutableStateOf(false) }
    var stage by remember { mutableStateOf<Int?>(null) }
    var probeFrames by remember { mutableStateOf(0) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("") }
    var enrollments by remember { mutableStateOf(0) }
    var fbPicture by remember { mutableStateOf<String?>(null) }
    var fbImportedPhotos by remember { mutableStateOf(0) }
    var fbImportedVideos by remember { mutableStateOf(0) }
    var captureUri by remember { mutableStateOf<Uri?>(null) }

    suspend fun refreshEnrollments() {
        enrollments = withContext(Dispatchers.IO) {
            JSONArray(SocialSession.request("faces/enrollments")).length()
        }
    }

    val pickProbe = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        probeUri = uri
        probeMime = uri?.let { context.contentResolver.getType(it) } ?: "image/jpeg"
        searched = false; matches = emptyList(); recordMatches = emptyList(); message = ""; stage = null; probeFrames = 0
    }
    val takeProbe = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (success) {
            probeUri = captureUri
            probeMime = "image/jpeg"
            searched = false
            matches = emptyList()
            recordMatches = emptyList()
            message = ""
            stage = null
            probeFrames = 0
        }
    }
    fun launchCamera() {
        val file = File(File(context.cacheDir, "captures").apply { mkdirs() }, "face-search.jpg")
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
        captureUri = uri
        takeProbe.launch(uri)
    }
    val askCamera = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) launchCamera() else message = context.getString(R.string.face_capture_no_camera)
    }
    val pickEnroll = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            busy = true
            try {
                val bytes = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error(context.getString(R.string.face_unreadable))
                val result = withContext(Dispatchers.IO) {
                    JSONObject(SocialSession.requestMultipart("faces/profile-photo", emptyMap(), prepareRecognitionPhoto(bytes), "profile.jpg", "image/jpeg"))
                }
                message = localizedQuantityText(R.plurals.face_enrolled, result.getInt("faces_enrolled"), result.getInt("faces_enrolled"))
                refreshEnrollments()
            } catch (error: Exception) { message = error.message.orEmpty() }
            finally { busy = false }
        }
    }

    LaunchedEffect(Unit) {
        try {
            val result = withContext(Dispatchers.IO) { JSONArray(SocialSession.request("workspaces")) }
            workspaces = (0 until result.length()).map { result.getJSONObject(it) }
            if (workspaceId.isBlank()) workspaceId = SocialSession.workspaceId.orEmpty()
            refreshEnrollments()
            val profile = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("me/facebook-profile")) }
            fbPicture = profile.optString("picture_url").takeIf { it.isNotBlank() }
            fbImportedPhotos = profile.optInt("imported_photos")
            fbImportedVideos = profile.optInt("imported_videos")
        } catch (error: Exception) { message = error.message.orEmpty() }
    }

    fun search() {
        val uri = probeUri
        if (uri == null || workspaceId.isBlank()) {
            message = context.getString(R.string.face_need_probe); return
        }
        scope.launch {
            busy = true
            try {
                val bytes = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error(context.getString(R.string.face_probe_unreadable))
                val mime = probeMime.ifBlank { "image/jpeg" }
                val filename = if (mime.startsWith("video/")) "probe.mp4" else "probe.jpg"
                val result = withContext(Dispatchers.IO) {
                    JSONObject(SocialSession.requestMultipart("faces/search", mapOf("workspace_id" to workspaceId), bytes, filename, mime))
                }
                val found = result.optJSONArray("matches") ?: JSONArray()
                matches = (0 until found.length()).map { found.getJSONObject(it) }
                val foundRecords = result.optJSONArray("matches_records") ?: JSONArray()
                recordMatches = (0 until foundRecords.length()).map { foundRecords.getJSONObject(it) }
                simulated = result.optBoolean("simulated")
                stage = if (result.isNull("stage")) null else result.getInt("stage")
                probeFrames = result.optInt("probe_frames", 0)
                searched = true
                message = ""
            } catch (error: Exception) { message = error.message.orEmpty() }
            finally { busy = false }
        }
    }

    LaunchedEffect(initialProbe, workspaceId) {
        if (initialProbe != null && workspaceId.isNotBlank() && !searched && !busy) search()
    }

    Column(Modifier.fillMaxSize().safeDrawingPadding()) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, stringResource(R.string.face_back)) }
            Column(Modifier.weight(1f)) {
                Text(stringResource(R.string.face_title), style = MaterialTheme.typography.titleMedium)
                Text(stringResource(R.string.face_subtitle), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.tertiary)
            }
        }
        if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            if (fbPicture != null) coil.compose.AsyncImage(model = fbPicture, contentDescription = stringResource(R.string.face_account),
                contentScale = ContentScale.Crop, modifier = Modifier.size(48.dp).clip(CircleShape))
            else Icon(Icons.Default.AccountCircle, null, modifier = Modifier.size(48.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(stringResource(R.string.face_my_photos), style = MaterialTheme.typography.titleSmall)
                Text(stringResource(R.string.face_import_status, fbImportedPhotos, fbImportedVideos),
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
        Text(stringResource(R.string.biometric_private_references), Modifier.padding(16.dp), style = MaterialTheme.typography.bodySmall)
        run {

        Column(Modifier.padding(horizontal = 16.dp)) {
            Text(stringResource(R.string.face_workspace), style = MaterialTheme.typography.labelMedium)
            Row {
                workspaces.take(4).forEach { workspace ->
                    val id = workspace.getString("id")
                    val name = workspace.getString("name").let { if (it.startsWith("home:")) context.getString(R.string.face_home) else it }
                    TextButton(onClick = { workspaceId = id; searched = false }) { Text((if (workspaceId == id) "✓ " else "") + name) }
                }
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (probeUri != null) coil.compose.AsyncImage(model = probeUri, contentDescription = null,
                    contentScale = ContentScale.Crop, modifier = Modifier.size(72.dp))
                else Icon(Icons.Default.PersonSearch, null, modifier = Modifier.size(72.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.width(12.dp))
                Column {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { pickProbe.launch("image/*") }, enabled = !busy) { Text(stringResource(R.string.face_pick)) }
                        OutlinedButton(onClick = { pickProbe.launch("video/*") }, enabled = !busy) { Text(stringResource(R.string.face_pick_video)) }
                        OutlinedButton(onClick = {
                            if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) launchCamera()
                            else askCamera.launch(Manifest.permission.CAMERA)
                        }, enabled = !busy) { Icon(Icons.Default.CameraAlt, null) }
                    }
                    Spacer(Modifier.height(8.dp))
                    Button(onClick = { search() }, enabled = !busy && probeUri != null) { Text(stringResource(R.string.face_search)) }
                }
            }
            NoticeEffect(message, { message = "" })
            if (simulated) Text(stringResource(R.string.face_simulated), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.tertiary)
            if (searched && stage != null) Text(stringResource(R.string.face_stage, stage!!), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.tertiary)
            if (searched && probeFrames > 1) Text(stringResource(R.string.face_frames, probeFrames), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.tertiary)
            if (searched && matches.isEmpty() && recordMatches.isEmpty()) Text(stringResource(R.string.face_no_match), modifier = Modifier.padding(vertical = 8.dp))
        }
        LazyColumn(Modifier.weight(1f)) {
            items(matches) { match ->
                ListItem(
                    modifier = Modifier.clickable { match.optString("user_id").takeIf { it.isNotBlank() }?.let(onOpenProfile) },
                    leadingContent = {
                        coil.compose.AsyncImage(
                            model = coil.request.ImageRequest.Builder(context)
                                .data(faceEvidenceUrl(match.optString("picture_url")))
                                .authorizeMedia(faceEvidenceUrl(match.optString("picture_url"))).build(),
                            contentDescription = match.optString("display_name"),
                            contentScale = ContentScale.Crop, modifier = Modifier.size(56.dp))
                    },
                    headlineContent = { Text(match.getString("display_name")) },
                    supportingContent = {
                        val badge = if (match.optString("match_type") == "possible_acquaintance") stringResource(R.string.face_badge_knows)
                        else stringResource(R.string.face_badge_direct)
                        Text("${(match.getDouble("similarity") * 100).toInt()}% · $badge")
                    },
                )
                HorizontalDivider()
            }
            items(recordMatches) { match ->
                val evidence = match.getJSONObject("evidence")
                ListItem(
                    leadingContent = {
                        coil.compose.AsyncImage(
                            model = coil.request.ImageRequest.Builder(context)
                                .data(faceEvidenceUrl(evidence.getString("thumbnail_url")))
                                .authorizeMedia(faceEvidenceUrl(evidence.getString("thumbnail_url"))).build(),
                            contentDescription = match.optString("title"),
                            contentScale = ContentScale.Crop, modifier = Modifier.size(56.dp))
                    },
                    headlineContent = { Text(match.optString("title")) },
                    supportingContent = {
                        Text("${(match.optDouble("similarity", 0.0) * 100).toInt()}% · ${match.optString("external_id")}")
                    },
                )
                HorizontalDivider()
            }
        }
        }
        HorizontalDivider()
        Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(stringResource(R.string.face_enroll_title), style = MaterialTheme.typography.titleSmall)
                Text(stringResource(R.string.face_enroll_count, enrollments), style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Button(onClick = { pickEnroll.launch("image/*") }, enabled = !busy) { Text(stringResource(R.string.face_enroll)) }
        }
    }
}
