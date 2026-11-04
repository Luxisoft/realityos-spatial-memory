package com.luxisoft.realityos

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

internal data class PublicationClassification(val categoryId: String = "", val tagIds: Set<String> = emptySet()) {
    val complete: Boolean get() = categoryId.isNotBlank() && tagIds.isNotEmpty()
    fun json(): JSONObject = JSONObject().put("category_id", categoryId).put("tag_ids", JSONArray(tagIds.toList()))
}

internal fun publicationClassification(post: JSONObject): PublicationClassification = PublicationClassification(
    post.optJSONObject("category")?.optString("id").orEmpty(),
    storageRows(post.optJSONArray("tags") ?: JSONArray()).map { it.getString("id") }.toSet()
)

@Composable
internal fun CatalogSelect(label: String, options: List<JSONObject>, selected: Set<String>, multiple: Boolean = true, enabled: Boolean = true, onSelect: (Set<String>) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Box(Modifier.fillMaxWidth()) {
        OutlinedButton(onClick = { expanded = true }, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
            Text(label + ": " + options.filter { it.optString("id") in selected }.joinToString { it.optString("name") }.ifBlank { localizedText(R.string.catalog_select) }, Modifier.weight(1f), maxLines = 2, overflow = TextOverflow.Ellipsis)
            Icon(Icons.Default.ArrowDropDown, null)
        }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }, modifier = Modifier.heightIn(max = 320.dp)) {
            options.forEach { option ->
                val id = option.getString("id")
                DropdownMenuItem(text = { Text(option.getString("name")) }, leadingIcon = {
                    if (multiple) Checkbox(checked = id in selected, onCheckedChange = null)
                    else RadioButton(selected = id in selected, onClick = null)
                }, onClick = {
                    onSelect(if (multiple) { if (id in selected) selected - id else selected + id } else setOf(id))
                    if (!multiple) expanded = false
                })
            }
            if (options.isEmpty()) DropdownMenuItem(text = { Text(localizedText(R.string.catalog_empty)) }, onClick = {}, enabled = false)
        }
    }
}

@Composable
internal fun ClassificationFields(workspaceId: String, value: PublicationClassification, enabled: Boolean = true, onValid: (Boolean) -> Unit = {}, onChange: (PublicationClassification) -> Unit) {
    var catalog by remember(workspaceId) { mutableStateOf<JSONObject?>(null) }
    var loading by remember(workspaceId) { mutableStateOf(true) }
    var error by remember(workspaceId) { mutableStateOf("") }
    var retry by remember { mutableIntStateOf(0) }
    LaunchedEffect(workspaceId, retry) {
        loading = true
        error = ""
        try {
            catalog = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("groups/$workspaceId/publication-catalog")) }
        } catch (cancelled: CancellationException) { throw cancelled }
        catch (failure: Exception) { error = failure.message.orEmpty() }
        finally { loading = false }
    }
    val categories = storageRows(catalog?.optJSONArray("categories") ?: JSONArray()).filter { it.optBoolean("active") }
    val tags = storageRows(catalog?.optJSONArray("tags") ?: JSONArray()).filter { it.optBoolean("active") }
    val valid = !loading && error.isBlank() && value.complete && categories.any { it.optString("id") == value.categoryId } && value.tagIds.all { key -> tags.any { it.optString("id") == key } }
    LaunchedEffect(valid) { onValid(valid) }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        CatalogSelect(localizedText(R.string.catalog_category), categories, setOf(value.categoryId), multiple = false, enabled = enabled && !loading) { onChange(value.copy(categoryId = it.firstOrNull().orEmpty())) }
        CatalogSelect(localizedText(R.string.catalog_tags), tags, value.tagIds, enabled = enabled && !loading) { if (it.size <= 20) onChange(value.copy(tagIds = it)) }
        if (!loading && error.isBlank() && (categories.isEmpty() || tags.isEmpty())) Text(localizedText(R.string.catalog_owner_needed), style = MaterialTheme.typography.bodySmall)
        if (error.isNotBlank()) {
            Text(error, color = MaterialTheme.colorScheme.error)
            TextButton(onClick = { retry++ }) { Text(localizedText(R.string.ui_retry)) }
        }
    }
}

@Composable
internal fun ClassificationDialog(workspaceId: String, initial: PublicationClassification = PublicationClassification(), previewUrl: String? = null, onSave: suspend (PublicationClassification) -> Unit, onClose: () -> Unit) {
    var value by remember(workspaceId) { mutableStateOf(initial) }
    var valid by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    AlertDialog(onDismissRequest = { if (!busy) onClose() }, title = { Text(localizedText(R.string.catalog_classify)) }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            previewUrl?.let { DatabaseImage(profileImageRequest(context, it), null, Modifier.fillMaxWidth().height(160.dp), contentScale = ContentScale.Fit) }
            ClassificationFields(workspaceId, value, enabled = !busy, onValid = { valid = it }) { value = it }
            if (error.isNotBlank()) Text(error, color = MaterialTheme.colorScheme.error)
            if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        }
    }, confirmButton = {
        TextButton(enabled = valid && !busy, onClick = {
            scope.launch {
                busy = true
                try { onSave(value); onClose() }
                catch (cancelled: CancellationException) { throw cancelled }
                catch (failure: Exception) { error = failure.message.orEmpty() }
                finally { busy = false }
            }
        }) { Text(localizedText(R.string.ui_accept)) }
    }, dismissButton = { TextButton(onClick = onClose, enabled = !busy) { Text(localizedText(R.string.ui_cancel)) } })
}

internal fun publicationClassificationText(post: JSONObject): String = buildList {
    post.optJSONObject("category")?.optText("name")?.let { add(it) }
    addAll(storageRows(post.optJSONArray("tags") ?: JSONArray()).map { "#" + it.optString("name") })
}.joinToString(" · ")

@Composable
internal fun PublicationThumbnail(post: JSONObject, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val context = LocalContext.current
    Box(modifier.clickable(onClick = onClick)) {
        DatabaseImage(profileImageRequest(context, post.optString("thumbnail_url")), post.optString("caption"), Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
        if (post.optString("mime_type").startsWith("video/")) {
            Surface(Modifier.align(Alignment.Center).size(36.dp).testTag("publication-video"), shape = MaterialTheme.shapes.extraLarge, color = Color.Black.copy(alpha = .55f)) {
                Icon(Icons.Default.PlayArrow, localizedText(R.string.profile_play_video), tint = Color.White, modifier = Modifier.padding(6.dp))
            }
        }
        val category = post.optJSONObject("category")?.optText("name")
        val tags = storageRows(post.optJSONArray("tags") ?: JSONArray())
        if (category != null || tags.isNotEmpty()) {
            Surface(Modifier.align(Alignment.BottomStart).padding(4.dp).fillMaxWidth().testTag("publication-classification"), shape = MaterialTheme.shapes.extraSmall, color = MaterialTheme.colorScheme.surface.copy(alpha = .92f)) {
                Column(Modifier.padding(horizontal = 5.dp, vertical = 3.dp)) {
                    category?.let { Text(it, style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis) }
                    if (tags.isNotEmpty()) Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(tags.take(2).joinToString(" · ") { "#" + it.optString("name") }, Modifier.weight(1f), style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        if (tags.size > 2) Text(" +${tags.size - 2}", style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
        }
    }
}

@Composable
internal fun CatalogDraftFields(categories: List<String>, tags: List<String>, onCategories: (List<String>) -> Unit, onTags: (List<String>) -> Unit) {
    CatalogDraftList(localizedText(R.string.catalog_categories), categories, onCategories)
    CatalogDraftList(localizedText(R.string.catalog_tags), tags, onTags)
}

@Composable
private fun CatalogDraftList(label: String, values: List<String>, onChange: (List<String>) -> Unit) {
    var draft by remember { mutableStateOf("") }
    Text(label, style = MaterialTheme.typography.titleSmall)
    values.forEach { value ->
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(value, Modifier.weight(1f))
            IconButton(onClick = { onChange(values - value) }) { Icon(Icons.Default.Close, localizedText(R.string.ui_delete)) }
        }
    }
    Row(verticalAlignment = Alignment.CenterVertically) {
        OutlinedTextField(draft, { draft = it.take(80) }, Modifier.weight(1f), label = { Text(label) }, singleLine = true)
        IconButton(enabled = draft.isNotBlank() && values.none { it.equals(draft.trim(), true) }, onClick = { onChange(values + draft.trim()); draft = "" }) { Icon(Icons.Default.Add, localizedText(R.string.catalog_add)) }
    }
}

@Composable
internal fun GroupCatalogEditor(workspaceId: String, onChanged: () -> Unit) {
    var catalog by remember(workspaceId) { mutableStateOf<JSONObject?>(null) }
    var revision by remember { mutableIntStateOf(0) }
    var editing by remember { mutableStateOf<JSONObject?>(null) }
    var kind by remember { mutableStateOf("category") }
    var name by remember { mutableStateOf("") }
    var show by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    LaunchedEffect(workspaceId, revision) {
        try { catalog = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("groups/$workspaceId/publication-catalog")) } }
        catch (cancelled: CancellationException) { throw cancelled }
        catch (failure: Exception) { error = failure.message.orEmpty() }
    }
    if (error.isNotBlank()) {
        Text(error, color = MaterialTheme.colorScheme.error)
        TextButton(onClick = { error = ""; revision++ }) { Text(localizedText(R.string.ui_retry)) }
    }
    if (catalog?.optBoolean("can_manage") != true) return
    Text(localizedText(R.string.catalog_title), style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 16.dp))
    fun save(active: Boolean) {
        scope.launch {
            busy = true
            try {
                withContext(Dispatchers.IO) {
                    val path = "groups/$workspaceId/publication-catalog/" + (editing?.getString("id") ?: kind)
                    SocialSession.requestJson(path, if (editing == null) "POST" else "PATCH", JSONObject().put("name", name).put("active", active))
                }
                show = false; revision++; onChanged()
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (failure: Exception) { error = failure.message.orEmpty() }
            finally { busy = false }
        }
    }
    listOf("categories" to "category", "tags" to "tag").forEach { (key, type) ->
        Text(localizedText(if (type == "category") R.string.catalog_categories else R.string.catalog_tags), style = MaterialTheme.typography.titleSmall)
        storageRows(catalog?.optJSONArray(key) ?: JSONArray()).forEach { term ->
            TextButton(onClick = { editing = term; kind = type; name = term.getString("name"); show = true }) {
                Text(term.getString("name") + if (term.optBoolean("active")) "" else " · " + localizedText(R.string.catalog_archived))
            }
        }
        TextButton(onClick = { editing = null; kind = type; name = ""; show = true }) { Icon(Icons.Default.Add, null); Text(localizedText(R.string.catalog_add)) }
    }
    if (show) AlertDialog(onDismissRequest = { if (!busy) show = false }, title = { Text(localizedText(R.string.catalog_title)) }, text = {
        Column {
            OutlinedTextField(name, { name = it.take(80) }, label = { Text(localizedText(R.string.ui_name)) }, enabled = !busy)
            if (editing != null) TextButton(onClick = { save(editing?.optBoolean("active") != true) }, enabled = !busy && name.isNotBlank()) { Text(localizedText(if (editing?.optBoolean("active") == true) R.string.catalog_archive else R.string.catalog_restore)) }
            if (error.isNotBlank()) Text(error, color = MaterialTheme.colorScheme.error)
        }
    }, confirmButton = { TextButton(onClick = { save(editing?.optBoolean("active") ?: true) }, enabled = !busy && name.isNotBlank()) { Text(localizedText(R.string.ui_accept)) } }, dismissButton = { TextButton(onClick = { show = false }, enabled = !busy) { Text(localizedText(R.string.ui_cancel)) } })
}
