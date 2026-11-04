package com.luxisoft.realityos

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

@Composable
internal fun GroupPublicationPicker(workspaceId: String, onClose: () -> Unit, onImported: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var rows by remember { mutableStateOf(emptyList<JSONObject>()) }
    var selected by remember { mutableStateOf(emptySet<String>()) }
    var classifications by remember { mutableStateOf(emptyMap<String, PublicationClassification>()) }
    var classifying by remember { mutableStateOf<String?>(null) }
    var applyAll by remember { mutableStateOf(false) }
    var batchValue by remember { mutableStateOf(PublicationClassification()) }
    var loading by remember { mutableStateOf(true) }
    var failed by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var cursor by remember { mutableStateOf<String?>(null) }
    var owner by remember { mutableStateOf("") }
    fun load() {
        scope.launch {
            loading = true
            failed = false
            try {
                val page = withContext(Dispatchers.IO) {
                    if (owner.isBlank()) owner = JSONObject(SocialSession.request("me/profile")).getString("user_id")
                    JSONObject(SocialSession.request("gallery/page?owner_ids=$owner&limit=30" + (cursor?.let { "&cursor=${android.net.Uri.encode(it)}" } ?: "")))
                }
                rows = (rows + storageRows(page.getJSONArray("items"))).distinctBy { it.optString("original_id").ifBlank { it.getString("id") } }
                cursor = page.optText("next_cursor")
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: Exception) {
                failed = true
                AppNotices.show(localizedFailure(error), NoticeKind.ERROR)
            } finally {
                loading = false
            }
        }
    }
    LaunchedEffect(workspaceId) { load() }
    Dialog(onDismissRequest = { if (!busy) onClose() }, properties = DialogProperties(usePlatformDefaultWidth = false, decorFitsSystemWindows = false)) {
        NoticeLayer {
            Surface(Modifier.fillMaxSize()) {
                Column(Modifier.fillMaxSize().safeDrawingPadding().padding(16.dp)) {
                    Text(localizedText(R.string.import_existing_publications), style = MaterialTheme.typography.titleLarge)
                    LazyColumn(Modifier.weight(1f)) {
                        items(rows, key = { it.getString("id") }) { post ->
                            val id = post.getString("id")
                            val inGroup = post.optString("workspace_id") == workspaceId
                            Column {
                                Row(Modifier.fillMaxWidth().clickable(enabled = !busy && !inGroup && (id in selected || selected.size < 100)) { selected = if (id in selected) selected - id else selected + id }.padding(vertical = 8.dp)) {
                                    Checkbox(checked = inGroup || id in selected, enabled = !busy && !inGroup && (id in selected || selected.size < 100), onCheckedChange = { checked -> selected = if (checked) selected + id else selected - id })
                                    Text(post.storedText("caption").ifBlank { localizedText(R.string.evidence_publication) }, Modifier.weight(1f).padding(8.dp))
                                    DatabaseImage(profileImageRequest(context, post.getString("thumbnail_url")), null, Modifier.size(64.dp))
                                }
                                if (id in selected) TextButton(onClick = { classifying = id }) { Text(localizedText(R.string.catalog_classify) + if (classifications[id]?.complete == true) " ✓" else "") }
                            }
                        }
                        if (loading) {
                            item { CircularProgressIndicator() }
                        } else if (failed) {
                            item { TextButton(onClick = { load() }) { Text(localizedText(R.string.ui_retry)) } }
                        } else if (cursor != null) {
                            item { TextButton(onClick = { load() }) { Text(localizedText(R.string.storage_more)) } }
                        } else if (rows.isEmpty()) {
                            item { Text(localizedText(R.string.ui_no_publications_in_this_workspace_yet)) }
                        }
                    }
                    TextButton(enabled = selected.isNotEmpty() && !busy, onClick = { applyAll = true }) { Text(localizedText(R.string.catalog_apply_all)) }
                    Button(enabled = selected.isNotEmpty() && selected.all { classifications[it]?.complete == true } && !busy, onClick = {
                        scope.launch {
                            busy = true
                            try {
                                withContext(Dispatchers.IO) { SocialSession.request("groups/$workspaceId/publications/import", JSONObject().put("publication_ids", JSONArray(selected.toList())).put("classifications", JSONObject().apply { selected.forEach { key -> put(key, classifications.getValue(key).json()) } })) }
                                AppNotices.show(localizedText(R.string.storage_done), NoticeKind.SUCCESS)
                                onImported()
                                onClose()
                            } catch (cancelled: CancellationException) {
                                throw cancelled
                            } catch (error: Exception) {
                                AppNotices.show(localizedFailure(error), NoticeKind.ERROR)
                            } finally {
                                busy = false
                            }
                        }
                    }) { Text(localizedText(R.string.storage_import) + " (${selected.size})") }
                    TextButton(onClick = onClose, enabled = !busy) { Text(localizedText(R.string.ui_close)) }
                }
            }
        }
    }
    if (classifying != null || applyAll) {
        val key = classifying
        ClassificationDialog(workspaceId, initial = if (applyAll) batchValue else classifications[key] ?: PublicationClassification(), onSave = { value ->
            if (applyAll) {
                batchValue = value
                classifications = classifications + selected.associateWith { value }
            } else if (key != null) {
                classifications = classifications + (key to value)
            }
        }, onClose = {
            classifying = null
            applyAll = false
        })
    }
}
