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
import java.net.URLEncoder
import java.time.Instant
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
    request: suspend (String, JSONObject?) -> String = { path, payload ->
        if (payload == null) SocialSession.request(path) else SocialSession.request(path, payload)
    }
) {
    key(workspaceId) { WorkspaceRecordsContent(workspaceId, canWrite, onBack, request) }
}

@Composable
private fun WorkspaceRecordsContent(workspaceId: String, canWrite: Boolean, onBack: () -> Unit, request: suspend (String, JSONObject?) -> String) {
    var query by remember { mutableStateOf("") }
    var rows by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var selected by remember { mutableStateOf<JSONObject?>(null) }
    var attachment by remember { mutableStateOf<JSONObject?>(null) }
    var note by remember { mutableStateOf("") }
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
    val base = "workspaces/$workspaceId/records"
    val openedAttachment = attachment
    if (openedAttachment != null) {
        MediaViewerScreen(
            title = selected?.optString("title").orEmpty(),
            mediaUrl = profileMediaUrl(openedAttachment.getString("url")),
            thumbnailUrl = "",
            mimeType = openedAttachment.optString("mime_type"),
            authToken = SocialSession.token,
            noteText = selected?.optJSONObject("data")?.optString("note").orEmpty(),
            noteSource = "text",
            metaLines = listOf(selected?.optString("occurred_at").orEmpty()),
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
                val response = withContext(Dispatchers.IO) { JSONObject(request("$base/$id", null)) }
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
    LaunchedEffect(workspaceId, refresh, offset) {
        listBusy = true
        try {
            val array = withContext(Dispatchers.IO) { JSONArray(request("$base?q=${URLEncoder.encode(query, "UTF-8")}&offset=$offset", null)) }
            val page = (0 until array.length()).map { array.getJSONObject(it) }
            rows = if (offset == 0) page else (rows + page).distinctBy { it.getString("id") }
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
        if (message.isNotBlank()) Text(message)
        val item = selected
        if (item == null) {
            OutlinedTextField(query, { query = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text(stringResource(R.string.records_search)) })
            Button(onClick = {
                offset = 0
                refresh++
            }, enabled = !busy) { Text(stringResource(R.string.records_search)) }
            if (!busy && rows.isEmpty()) Text(stringResource(R.string.records_empty))
            rows.forEach { row ->
                OutlinedButton(onClick = { open(row.getString("id")) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.fillMaxWidth()) {
                        Text(row.getString("title"))
                        Text(row.getString("external_id") + " · " + row.getString("kind"), style = MaterialTheme.typography.bodySmall)
                        if (row.optBoolean("simulated")) Text(stringResource(R.string.records_simulated), style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
            if (hasMore) OutlinedButton(onClick = { offset += 50 }, enabled = !busy) { Text(stringResource(R.string.records_more)) }
        } else {
            Text(item.getString("title"), style = MaterialTheme.typography.titleLarge)
            Text(item.getString("external_id") + " · v" + item.getInt("version"))
            Text(item.getString("occurred_at"), style = MaterialTheme.typography.bodySmall)
            val data = item.optJSONObject("data") ?: JSONObject()
            data.keys().forEach { key -> Text("$key: ${data.opt(key)}") }
            Text(stringResource(R.string.records_related), style = MaterialTheme.typography.titleMedium)
            val related = item.optJSONArray("related") ?: JSONArray()
            (0 until related.length()).forEach { i ->
                val row = related.getJSONObject(i)
                TextButton(onClick = { open(row.getString("id")) }, enabled = !busy) { Text(row.getString("title")) }
            }
            if (item.optString("kind") == "person") key(item.getString("id")) { MedicationCheckForm(workspaceId, item) }
            Text(stringResource(R.string.records_timeline), style = MaterialTheme.typography.titleMedium)
            val notes = item.optJSONArray("notes") ?: JSONArray()
            (0 until notes.length()).forEach { i ->
                val n = notes.getJSONObject(i)
                Text(n.getString("occurred_at"), style = MaterialTheme.typography.labelSmall)
                Text(n.getString("text"))
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
                            withContext(Dispatchers.IO) { request("$base/${item.getString("id")}/notes", JSONObject().put("text", submittedNote).put("occurred_at", Instant.now().toString())) }
                            val response = withContext(Dispatchers.IO) { JSONObject(request("$base/${item.getString("id")}", null)) }
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
            (0 until media.length()).forEach { i ->
                val file = media.getJSONObject(i)
                if (file.optString("mime_type").startsWith("video/")) {
                    OutlinedButton(onClick = { attachment = file }) { Text(stringResource(R.string.records_video)) }
                } else {
                    DatabaseImage(model = profileImageRequest(androidx.compose.ui.platform.LocalContext.current, file.getString("url")), contentDescription = item.getString("title"), modifier = Modifier.fillMaxWidth().height(240.dp).clickable { attachment = file })
                }
            }
        }
    }
}
