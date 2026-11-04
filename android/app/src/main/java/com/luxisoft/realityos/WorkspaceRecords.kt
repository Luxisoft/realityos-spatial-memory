package com.luxisoft.realityos

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.luxisoft.realityos.data.JsonApi
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

@Composable
internal fun WorkspaceRecords(
    workspaceId: String,
    canWrite: Boolean,
    onBack: () -> Unit,
    initialRecordId: String? = null,
    request: suspend (String, JSONObject?) -> String = { path, payload ->
        if (payload == null) SocialSession.request(path) else SocialSession.request(path, payload)
    }
) {
    key(workspaceId) { WorkspaceRecordsContent(workspaceId, canWrite, onBack, request, initialRecordId) }
}

@Composable
private fun WorkspaceRecordsContent(workspaceId: String, canWrite: Boolean, onBack: () -> Unit, request: suspend (String, JSONObject?) -> String, initialRecordId: String?) {
    val repository = remember(workspaceId, request) {
        WorkspaceRecordsRepository(workspaceId, JsonApi { path, _, payload -> withContext(Dispatchers.IO) { request(path, payload) } })
    }
    var query by remember { mutableStateOf("") }
    var rows by remember { mutableStateOf<List<WorkspaceRecord>>(emptyList()) }
    var selected by remember { mutableStateOf<RecordDetails?>(null) }
    var attachment by remember { mutableStateOf<JSONObject?>(null) }
    var note by remember { mutableStateOf("") }
    var biometricBasis by remember { mutableStateOf("") }
    var message by remember { mutableStateOf("") }
    var listBusy by remember { mutableStateOf(false) }
    var detailBusy by remember { mutableStateOf(false) }
    val busy = listBusy || detailBusy
    var operation by remember { mutableIntStateOf(0) }
    var detailJob by remember { mutableStateOf<Job?>(null) }
    var pendingId by remember { mutableStateOf<String?>(null) }
    var refresh by remember { mutableIntStateOf(0) }
    var offset by remember { mutableIntStateOf(0) }
    var hasMore by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val openedAttachment = attachment
    if (openedAttachment != null) {
        MediaViewerScreen(
            title = selected?.record?.title?.display().orEmpty(),
            mediaUrl = profileMediaUrl(openedAttachment.getString("url")),
            thumbnailUrl = "",
            mimeType = openedAttachment.optString("mime_type"),
            authToken = SocialSession.token,
            noteText = selected?.fields()?.firstOrNull { it.first == "note" }?.second.orEmpty(),
            noteSource = "text",
            metaLines = listOf(selected?.record?.occurredAt.orEmpty()),
            onClose = { attachment = null }
        )
        return
    }
    fun open(id: String) {
        val current = ++operation
        detailJob?.cancel()
        pendingId = id
        note = ""
        message = ""
        detailBusy = true
        detailJob = scope.launch {
            try {
                val response = repository.detail(id)
                if (operation == current) selected = response
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                if (operation == current) message = localizedText(R.string.account_failed)
            } finally {
                if (operation == current) {
                    detailBusy = false
                    pendingId = null
                }
            }
        }
    }
    LaunchedEffect(workspaceId, initialRecordId) { initialRecordId?.let { open(it) } }
    LaunchedEffect(workspaceId, refresh, offset) {
        listBusy = true
        try {
            val page = repository.list(query, offset)
            rows = if (offset == 0) page else (rows + page).distinctBy { it.id }
            hasMore = page.size == 50
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            message = localizedText(R.string.account_failed)
        } finally {
            listBusy = false
        }
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        TextButton(onClick = {
            val showingDetail = selected != null || pendingId != null
            operation++
            detailJob?.cancel()
            pendingId = null
            detailBusy = false
            selected = null
            note = ""
            message = ""
            if (!showingDetail) onBack()
        }) { Text(stringResource(R.string.account_back)) }
        Text(stringResource(R.string.records_title), style = MaterialTheme.typography.headlineSmall)
        if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        NoticeEffect(message, { message = "" })
        val details = selected
        if (details == null) {
            OutlinedTextField(query, { query = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text(stringResource(R.string.records_search)) })
            Button(onClick = {
                offset = 0
                refresh++
            }, enabled = !busy) { Text(stringResource(R.string.records_search)) }
            if (!busy && rows.isEmpty()) Text(stringResource(R.string.records_empty))
            rows.forEach { row ->
                OutlinedButton(onClick = { open(row.id) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.fillMaxWidth()) {
                        Text(row.title.display())
                        Text(row.externalId + " · " + recordFieldLabel(row.kind), style = MaterialTheme.typography.bodySmall)
                        if (row.kind == "person" && row.biometricAuthorized) Text(stringResource(R.string.records_face_authorized), style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
            if (hasMore) OutlinedButton(onClick = { offset += 50 }, enabled = !busy) { Text(stringResource(R.string.records_more)) }
        } else {
            val item = details.legacyDocument()
            Text(details.record.title.display(), style = MaterialTheme.typography.titleLarge)
            Text(item.getString("external_id") + " · v" + item.getInt("version"))
            Text(item.getString("occurred_at"), style = MaterialTheme.typography.bodySmall)
            if (item.optString("kind") == "person") {
                if (item.optBoolean("biometric_authorized")) {
                    Text(stringResource(R.string.records_face_authorized), style = MaterialTheme.typography.labelMedium)
                    Text(stringResource(R.string.records_face_candidate), style = MaterialTheme.typography.bodySmall)
                }
            }
            details.fields().forEach { (field, value) -> Text("${recordFieldLabel(field)}: $value") }
            Text(stringResource(R.string.records_related), style = MaterialTheme.typography.titleMedium)
            details.related.forEach { row ->
                TextButton(onClick = { open(row.id) }, enabled = !busy) { Text(row.title.display()) }
            }
            Text(stringResource(R.string.records_timeline), style = MaterialTheme.typography.titleMedium)
            details.notes.forEach { entry ->
                Text(entry.occurredAt, style = MaterialTheme.typography.labelSmall)
                Text(entry.text)
            }
            if (canWrite) {
                OutlinedTextField(note, { note = it }, Modifier.fillMaxWidth(), enabled = !busy, label = { Text(stringResource(R.string.records_note)) })
                Button(enabled = !busy && note.isNotBlank(), onClick = {
                    val current = ++operation
                    val submittedNote = note
                    detailJob?.cancel()
                    detailBusy = true
                    detailJob = scope.launch {
                        try {
                            val response = repository.addNote(details.record.id, submittedNote)
                            if (operation == current) {
                                note = ""
                                selected = response
                            }
                        } catch (cancelled: CancellationException) {
                            throw cancelled
                        } catch (_: Exception) {
                            if (operation == current) message = localizedText(R.string.account_failed)
                        } finally {
                            if (operation == current) detailBusy = false
                        }
                    }
                }) { Text(stringResource(R.string.records_save)) }
            }
            val media = item.optJSONArray("media") ?: JSONArray()
            if (item.optString("kind") == "person" && canWrite && !item.optBoolean("biometric_authorized")) {
                OutlinedTextField(biometricBasis, { biometricBasis = it }, Modifier.fillMaxWidth(), enabled = !busy, label = { Text(stringResource(R.string.records_face_basis)) })
            }
            (0 until media.length()).forEach { i ->
                val file = media.getJSONObject(i)
                if (file.optString("mime_type").startsWith("video/")) {
                    OutlinedButton(onClick = { attachment = file }) { Text(stringResource(R.string.records_video)) }
                } else {
                    DatabaseImage(model = profileImageRequest(androidx.compose.ui.platform.LocalContext.current, file.getString("url")), contentDescription = item.storedText("title"), modifier = Modifier.fillMaxWidth().height(240.dp).clickable { attachment = file })
                    if (item.optString("kind") == "person" && canWrite) {
                        val needsBasis = !item.optBoolean("biometric_authorized")
                        OutlinedButton(enabled = !busy && (!needsBasis || biometricBasis.isNotBlank()), onClick = {
                            val current = ++operation
                            val basis = biometricBasis
                            detailJob?.cancel()
                            detailBusy = true
                            detailJob = scope.launch {
                                try {
                                    val payload = JSONObject().put("record_id", item.getString("id")).put("record_media_id", file.getString("id"))
                                    if (basis.isNotBlank()) payload.put("biometric_basis", basis)
                                    withContext(Dispatchers.IO) { request("faces/record-enroll", payload) }
                                    val response = repository.detail(item.getString("id"))
                                    if (operation == current) {
                                        biometricBasis = ""
                                        selected = response
                                    }
                                } catch (cancelled: CancellationException) {
                                    throw cancelled
                                } catch (_: Exception) {
                                    if (operation == current) message = localizedText(R.string.account_failed)
                                } finally {
                                    if (operation == current) detailBusy = false
                                }
                            }
                        }) { Text(stringResource(R.string.records_face_enroll)) }
                    }
                }
            }
        }
    }
}
