package com.luxisoft.realityos

import android.net.Uri
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

@Composable
internal fun StorageConnectionsScreen(onClose: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var connections by remember { mutableStateOf(emptyList<JSONObject>()) }
    var selected by remember { mutableStateOf<JSONObject?>(null) }
    var editing by remember { mutableStateOf(false) }
    var formValue by remember { mutableStateOf<JSONObject?>(null) }
    var folder by remember { mutableStateOf("") }
    var page by remember { mutableStateOf(JSONObject()) }
    var picked by remember { mutableStateOf(setOf<String>()) }
    var workspaces by remember { mutableStateOf(emptyList<JSONObject>()) }
    var workspace by remember { mutableStateOf("") }
    var runs by remember { mutableStateOf(emptyList<JSONObject>()) }
    var rules by remember { mutableStateOf(emptyList<JSONObject>()) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("") }
    var confirmation by remember { mutableStateOf<String?>(null) }
    var preview by remember { mutableStateOf<JSONObject?>(null) }
    var result by remember { mutableStateOf<JSONObject?>(null) }
    var evidence by remember { mutableStateOf<StorageEvidenceSelection?>(null) }
    var openProfile by remember { mutableStateOf<String?>(null) }
    var resultWorkspace by remember { mutableStateOf("") }
    var openRecord by remember { mutableStateOf<String?>(null) }
    var consentAsk by remember { mutableStateOf(false) }
    var faceManagement by remember { mutableStateOf(false) }
    val uploader = rememberPublicationUploader(onPublished = {}, onBusy = {})
    PublicationUploadDialog(uploader)
    fun base(): String = "$STORAGE_BASE/${selected!!.getString("id")}"
    fun operation(block: suspend () -> Unit) {
        scope.launch {
            busy = true
            message = ""
            try {
                block()
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: Exception) {
                message = localizedText(R.string.storage_error) + " " + error.message.orEmpty()
            } finally {
                busy = false
            }
        }
    }
    suspend fun request(path: String, body: JSONObject? = null, method: String? = null): String = withContext(Dispatchers.IO) {
        SocialSession.requestJson(path, method ?: if (body == null) "GET" else "POST", body)
    }
    suspend fun browse(prefix: String, cursor: String? = null) {
        val response = JSONObject(request("${base()}/objects?prefix=${Uri.encode(prefix)}" + (cursor?.let { "&cursor=${Uri.encode(it)}" } ?: "")))
        folder = response.optString("prefix")
        page = response
        picked = emptySet()
    }
    suspend fun refreshRuns() {
        runs = storageRows(JSONArray(request("${base()}/imports")))
        rules = storageRows(JSONArray(request("${base()}/syncs")))
    }
    LaunchedEffect(Unit) {
        operation {
            connections = storageRows(JSONArray(request(STORAGE_BASE)))
            workspaces = storageRows(JSONArray(request("workspaces")))
        }
    }
    LaunchedEffect(selected?.optString("id")) {
        while (selected != null) {
            if (!busy) {
                try {
                    refreshRuns()
                } catch (cancelled: CancellationException) {
                    throw cancelled
                } catch (_: Exception) { }
            }
            delay(5000)
        }
    }
    fun back() {
        when {
            editing -> editing = false
            preview != null -> preview = null
            result != null -> result = null
            selected != null -> {
                selected = null
                runs = emptyList()
                rules = emptyList()
                picked = emptySet()
                page = JSONObject()
            }
            else -> onClose()
        }
    }
    BackHandler(enabled = !busy) { back() }
    openProfile?.let {
        ProfileScreen(userId = it, onBack = { openProfile = null })
        return
    }
    openRecord?.let {
        WorkspaceRecords(workspaceId = resultWorkspace, canWrite = false, initialRecordId = it, onBack = { openRecord = null })
        return
    }
    if (faceManagement) {
        FaceSearch(onBack = { faceManagement = false })
        return
    }
    evidence?.let { selection ->
        StorageEvidenceViewer(selection) { evidence = null }
        return
    }
    preview?.let { item ->
        val url = "${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/${base()}/content?key=${Uri.encode(item.getString("key"))}"
        MediaViewerScreen(title = item.getString("key"), mediaUrl = url, thumbnailUrl = "$url&preview=true", mimeType = item.getString("mime_type"), authToken = SocialSession.token, noteText = "", noteSource = "text", metaLines = emptyList(), onClose = { preview = null })
        return
    }
    if (editing) {
        Column(Modifier.fillMaxSize()) {
            if (message.isNotBlank()) Text(message, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(12.dp))
            StorageConnectionForm(formValue, busy, onSave = { body ->
                operation {
                    request(if (formValue == null) STORAGE_BASE else "$STORAGE_BASE/${formValue!!.getString("id")}", body, if (formValue == null) "POST" else "PUT")
                    connections = storageRows(JSONArray(request(STORAGE_BASE)))
                    selected = selected?.let { previous -> connections.find { it.getString("id") == previous.getString("id") } }
                    editing = false
                }
            }, onClose = { editing = false })
        }
        return
    }
    fun search(person: Boolean) {
        val key = picked.single()
        val item = storageRows(page.optJSONArray("items") ?: JSONArray()).first { it.getString("key") == key }
        val target = workspace.ifBlank { SocialSession.workspaceId.orEmpty() }
        val token = SocialSession.token ?: return
        operation {
            if (person && !JSONObject(request("faces/consent")).optBoolean("consented")) {
                consentAsk = true
                return@operation
            }
            val bytes = withContext(Dispatchers.IO) { storageDownload("${base()}/content?key=${Uri.encode(key)}", token) }
            check(SocialSession.token == token) { localizedText(R.string.storage_session_changed) }
            val language = RealityExperienceStore(context).selectedLanguage().languageTag
            val response = withContext(Dispatchers.IO) {
                SocialSession.requestMultipart(if (person) "faces/search" else "queries/image", mapOf("workspace_id" to target, "language" to language), bytes, key.substringAfterLast('/'), item.getString("mime_type"), if (person) "probe" else "image")
            }
            check(SocialSession.token == token) { localizedText(R.string.storage_session_changed) }
            resultWorkspace = target
            result = JSONObject(response)
        }
    }
    LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            Text(localizedText(R.string.storage_title), style = MaterialTheme.typography.titleLarge)
            TextButton(onClick = { back() }, enabled = !busy) { Text(localizedText(R.string.storage_back)) }
            if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
            if (message.isNotBlank()) Text(message, color = MaterialTheme.colorScheme.error)
        }
        if (selected == null) {
            item {
                Button(onClick = {
                    formValue = null
                    editing = true
                }) { Text(localizedText(R.string.storage_add)) }
            }
            items(connections, key = { it.getString("id") }) { connection ->
                OutlinedButton(onClick = {
                    selected = connection
                    operation {
                        browse(connection.optString("prefix"))
                        refreshRuns()
                    }
                }) { Text(connection.getString("name") + " · " + connection.getString("bucket")) }
            }
            if (connections.isEmpty()) item { Text(localizedText(R.string.storage_empty)) }
        } else {
            item {
                Text(selected!!.getString("name"), style = MaterialTheme.typography.titleMedium)
                Row {
                    TextButton(onClick = {
                        operation {
                            request("${base()}/test", JSONObject())
                            message = localizedText(R.string.storage_connected)
                        }
                    }, enabled = !busy) { Text(localizedText(R.string.storage_test)) }
                    TextButton(onClick = {
                        formValue = selected
                        editing = true
                    }, enabled = !busy) { Text(localizedText(R.string.storage_edit)) }
                    TextButton(onClick = { confirmation = "disconnect" }, enabled = !busy) { Text(localizedText(R.string.storage_disconnect)) }
                }
                Text(localizedText(R.string.storage_destination))
                var destinations by remember { mutableStateOf(false) }
                Box {
                    OutlinedButton(onClick = { destinations = true }, enabled = !busy) { Text(workspaces.find { it.getString("id") == workspace }?.optString("name") ?: localizedText(R.string.storage_private)) }
                    DropdownMenu(destinations, { destinations = false }) {
                        DropdownMenuItem(text = { Text(localizedText(R.string.storage_private)) }, onClick = {
                            workspace = ""
                            destinations = false
                        })
                        workspaces.filter { !it.optString("name").startsWith("home:") }.forEach { group ->
                            DropdownMenuItem(text = { Text(group.getString("name")) }, onClick = {
                                workspace = group.getString("id")
                                destinations = false
                            })
                        }
                    }
                }
                Text(folder.ifBlank { "/" })
                TextButton(onClick = { operation { browse(selected!!.optString("prefix")) } }, enabled = !busy) { Text(localizedText(R.string.storage_root)) }
            }
            items((0 until (page.optJSONArray("folders")?.length() ?: 0)).map { page.getJSONArray("folders").getString(it) }) { name ->
                TextButton(onClick = { operation { browse(name) } }, enabled = !busy) { Text("📁 " + name) }
            }
            items(storageRows(page.optJSONArray("items") ?: JSONArray()), key = { it.getString("key") }) { item ->
                val key = item.getString("key")
                val mime = item.optString("mime_type")
                Row(Modifier.fillMaxWidth()) {
                    Checkbox(checked = key in picked, enabled = !busy && (storageSupportsMedia(mime) || storageSupportsCv(mime)), onCheckedChange = { checked -> picked = if (checked) picked + key else picked - key })
                    Column(Modifier.weight(1f)) {
                        Text(key.substringAfterLast('/'))
                        Text("${item.optLong("size")} B · ${item.optString("modified_at")}", style = MaterialTheme.typography.bodySmall)
                        if (storageSupportsMedia(mime)) {
                            TextButton(onClick = { preview = item }) { Text(localizedText(R.string.storage_preview)) }
                        } else if (!storageSupportsCv(mime)) {
                            Text(localizedText(R.string.storage_unsupported))
                        }
                    }
                }
            }
            page.optText("next_cursor")?.let { cursor -> item { TextButton(onClick = { operation { browse(folder, cursor) } }, enabled = !busy) { Text(localizedText(R.string.storage_more)) } } }
            item {
                val chosen = storageRows(page.optJSONArray("items") ?: JSONArray()).filter { it.getString("key") in picked }
                Button(onClick = { confirmation = "import" }, enabled = !busy && chosen.isNotEmpty() && chosen.all { storageSupportsMedia(it.optString("mime_type")) }) { Text(localizedText(R.string.storage_import) + " (${picked.size})") }
                if (chosen.size == 1) {
                    val mime = chosen.single().optString("mime_type")
                    if (mime.startsWith("image/")) TextButton(onClick = { search(false) }, enabled = !busy) { Text(localizedText(R.string.storage_search_object)) }
                    if (storageSupportsMedia(mime)) TextButton(onClick = { search(true) }, enabled = !busy) { Text(localizedText(R.string.storage_search_person)) }
                    if (storageSupportsCv(mime)) TextButton(onClick = { confirmation = "cv" }, enabled = !busy) { Text(localizedText(R.string.storage_cv)) }
                }
                TextButton(onClick = { faceManagement = true }, enabled = !busy) { Text(localizedText(R.string.storage_face_settings)) }
                Text(localizedText(R.string.storage_sync_help))
                listOf(0, 15, 60, 1440).forEach { minutes ->
                    TextButton(onClick = { confirmation = "sync:$minutes" }, enabled = !busy) { Text(if (minutes == 0) localizedText(R.string.storage_manual_sync) else localizedText(R.string.storage_sync_every, minutes)) }
                }
            }
            result?.let { response ->
                item {
                    Text(response.optText("message") ?: localizedText(R.string.storage_search_results))
                    val thumbs = storageRows(response.optJSONArray("gallery_matches") ?: JSONArray()).mapNotNull { decodeGalleryThumb(it) } + storageRows(response.optJSONArray("matches") ?: JSONArray()).mapNotNull { decodeFaceThumb(it) } + storageRows(response.optJSONArray("matches_records") ?: JSONArray()).mapNotNull { decodeRecordFaceThumb(it) }
                    response.optText("highlighted_media_url")?.let { url ->
                        DatabaseImage(profileImageRequest(context, authorizedMediaUrl(url)), response.optString("message"), Modifier.fillMaxWidth().height(220.dp))
                    }
                    if (thumbs.isEmpty() && response.optText("highlighted_media_url") == null) Text(localizedText(R.string.storage_no_results))
                    StorageResultButtons(thumbs, onProfile = { openProfile = it }, onRecord = { openRecord = it }, onEvidence = { evidence = it })
                }
            }
            items(rules, key = { it.getString("id") }) { rule ->
                Column {
                    Text(rule.optString("prefix") + " · " + if (rule.optBoolean("enabled")) localizedText(R.string.storage_sync_every, rule.optInt("interval_minutes")) else localizedText(R.string.storage_sync_paused))
                    rule.optText("error")?.let { Text(it) }
                    Row {
                        TextButton(onClick = {
                            operation {
                                request("${base()}/syncs/${rule.getString("id")}/run", JSONObject())
                                refreshRuns()
                            }
                        }, enabled = !busy) { Text(localizedText(R.string.storage_update)) }
                        if (rule.optBoolean("enabled")) {
                            TextButton(onClick = {
                                operation {
                                    request("${base()}/syncs/${rule.getString("id")}", method = "DELETE")
                                    refreshRuns()
                                }
                            }, enabled = !busy) { Text(localizedText(R.string.storage_pause)) }
                        }
                    }
                }
            }
            item { Text(localizedText(R.string.storage_imports), style = MaterialTheme.typography.titleMedium) }
            items(runs, key = { it.getString("id") }) { run ->
                Column {
                    storageRows(run.getJSONArray("items")).forEach { item ->
                        Text(item.getString("key").substringAfterLast('/') + " · " + storageStatusLabel(item.getString("status")))
                        if (item.optString("status") in setOf("duplicate", "failed") && !item.isNull("upload_id")) {
                            TextButton(onClick = {
                                uploader.id = item.getString("upload_id")
                                uploader.resumePolling()
                            }) { Text(localizedText(R.string.storage_review)) }
                        }
                    }
                    if (storageRows(run.getJSONArray("items")).any { it.optString("status") == "failed" }) {
                        TextButton(onClick = {
                            operation {
                                request("${base()}/imports/${run.getString("id")}/retry", JSONObject())
                                refreshRuns()
                            }
                        }, enabled = !busy) { Text(localizedText(R.string.storage_retry)) }
                    }
                }
            }
        }
    }
    if (consentAsk) {
        AlertDialog(onDismissRequest = { consentAsk = false }, title = { Text(localizedText(R.string.face_consent_title)) }, text = { Text(localizedText(R.string.face_consent_body)) }, confirmButton = {
            TextButton(onClick = {
                operation {
                    request("faces/consent", JSONObject().put("confirm", true))
                    consentAsk = false
                }
            }) { Text(localizedText(R.string.face_consent_accept)) }
        }, dismissButton = { TextButton(onClick = { consentAsk = false }) { Text(localizedText(R.string.face_consent_later)) } })
    }
    confirmation?.let { action ->
        AlertDialog(onDismissRequest = { confirmation = null }, title = { Text(localizedText(R.string.storage_confirm)) }, text = {
            Text(
                localizedText(
                    if (action == "disconnect") {
                        R.string.storage_disconnect_help
                    } else if (action == "cv") {
                        R.string.storage_cv_help
                    } else {
                        R.string.storage_import_help
                    }
                ) + "\n" + (workspaces.find { it.getString("id") == workspace }?.optString("name") ?: localizedText(R.string.storage_private))
            )
        }, confirmButton = {
            Button(onClick = {
                confirmation = null
                operation {
                    val destination = JSONObject().put("audience", if (workspace.isBlank()) "home" else "work")
                    if (workspace.isNotBlank()) destination.put("workspace_id", workspace)
                    when {
                        action == "disconnect" -> {
                            request(base(), method = "DELETE")
                            selected = null
                            connections = storageRows(JSONArray(request(STORAGE_BASE)))
                        }
                        action == "cv" -> {
                            request("${base()}/cv", JSONObject().put("key", picked.single()))
                            message = localizedText(R.string.storage_done)
                        }
                        action.startsWith("sync:") -> {
                            request("${base()}/syncs", destination.put("prefix", folder).put("enabled", action != "sync:0").put("interval_minutes", action.substringAfter(':').toInt().takeIf { it > 0 } ?: 60))
                            refreshRuns()
                        }
                        else -> {
                            request("${base()}/imports", destination.put("request_key", UUID.randomUUID().toString()).put("keys", JSONArray(picked.toList())))
                            picked = emptySet()
                            refreshRuns()
                        }
                    }
                }
            }) { Text(localizedText(R.string.storage_confirm)) }
        }, dismissButton = { TextButton(onClick = { confirmation = null }) { Text(localizedText(R.string.storage_back)) } })
    }
}

internal data class StorageEvidenceSelection(val items: List<GalleryThumb>, val index: Int)

@Composable
internal fun StorageEvidenceViewer(selection: StorageEvidenceSelection, onClose: () -> Unit) {
    SearchEvidenceCarousel(selection.items, selection.index, onClose)
}

@Composable
internal fun StorageResultButtons(thumbs: List<GalleryThumb>, onProfile: (String) -> Unit, onRecord: (String) -> Unit, onEvidence: (StorageEvidenceSelection) -> Unit) {
    thumbs.forEachIndexed { index, thumb ->
        TextButton(onClick = {
            when {
                thumb.profileUserId.isNotBlank() -> onProfile(thumb.profileUserId)
                thumb.recordId.isNotBlank() -> onRecord(thumb.recordId)
                else -> onEvidence(StorageEvidenceSelection(thumbs, index))
            }
        }) { Text(thumb.caption + (thumb.confidence?.let { " · ${(it * 100).toInt()}%" } ?: "")) }
    }
}
