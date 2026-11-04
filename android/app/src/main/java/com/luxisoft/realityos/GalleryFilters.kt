package com.luxisoft.realityos

import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.ZoneOffset
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

internal data class GalleryFilterSelection(
    val categories: Set<String> = emptySet(),
    val tags: Set<String> = emptySet(),
    val owners: Set<String> = emptySet(),
    val from: LocalDate? = null,
    val through: LocalDate? = null,
    val text: String = ""
) {
    val active: Boolean get() = categories.isNotEmpty() || tags.isNotEmpty() || owners.isNotEmpty() || from != null || through != null || text.isNotBlank()
    val valid: Boolean get() = from == null || through == null || !through.isBefore(from)
    fun query(zone: ZoneId = ZoneId.systemDefault()): String = buildList {
        categories.sorted().forEach { add("category_ids=" + Uri.encode(it)) }
        tags.sorted().forEach { add("tag_ids=" + Uri.encode(it)) }
        owners.sorted().forEach { add("owner_ids=" + Uri.encode(it)) }
        from?.let { add("published_from=" + Uri.encode(it.atStartOfDay(zone).toInstant().toString())) }
        through?.let { add("published_before=" + Uri.encode(it.plusDays(1).atStartOfDay(zone).toInstant().toString())) }
        if (text.isNotBlank()) add("description_q=" + Uri.encode(text.trim()))
    }.joinToString("&")
}

@Composable
internal fun GalleryFilterButton(
    bar: GalleryTopBarState,
    fetchOptions: suspend (String?) -> JSONObject = { workspaceId ->
        withContext(Dispatchers.IO) { JSONObject(SocialSession.request("gallery/filter-options" + (workspaceId?.let { "?workspace_id=${Uri.encode(it)}" } ?: ""))) }
    }
) {
    var open by remember { mutableStateOf(false) }
    var draft by remember { mutableStateOf(bar.filters) }
    var options by remember(bar.selectedId) { mutableStateOf<JSONObject?>(null) }
    var error by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var retry by remember { mutableIntStateOf(0) }
    LaunchedEffect(open, bar.selectedId, retry) {
        if (!open) return@LaunchedEffect
        loading = true
        error = ""
        options = null
        try {
            options = fetchOptions(bar.selectedId)
        } catch (cancelled: CancellationException) { throw cancelled }
        catch (failure: Exception) { error = failure.message.orEmpty() }
        finally { loading = false }
    }
    fun optionsFor(key: String): List<JSONObject> = storageRows(options?.optJSONArray(key) ?: JSONArray()).map { item ->
        if (bar.selectedId == null && item.optString("workspace_name").isNotBlank()) JSONObject(item.toString()).put("name", item.optString("name") + " · " + item.optString("workspace_name")) else item
    }
    val config = LocalConfiguration.current
    Box {
        IconButton(onClick = { draft = bar.filters; open = true }, modifier = Modifier.testTag("gallery-filter")) {
            Icon(Icons.Default.FilterList, localizedText(R.string.gallery_filters), tint = if (bar.filters.active) MaterialTheme.colorScheme.primary else LocalContentColor.current)
        }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }, modifier = Modifier.widthIn(max = (config.screenWidthDp - 24).dp).heightIn(max = (config.screenHeightDp * .8f).dp)) {
            Column(Modifier.widthIn(min = 240.dp, max = 360.dp).padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(localizedText(R.string.gallery_filters), style = MaterialTheme.typography.titleMedium)
                if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
                CatalogSelect(localizedText(R.string.catalog_categories), optionsFor("categories"), draft.categories, enabled = !loading) { draft = draft.copy(categories = it) }
                CatalogSelect(localizedText(R.string.catalog_tags), optionsFor("tags"), draft.tags, enabled = !loading) { draft = draft.copy(tags = it) }
                CatalogSelect(localizedText(R.string.gallery_authors), optionsFor("owners"), draft.owners, enabled = !loading) { draft = draft.copy(owners = it) }
                GalleryDateField(localizedText(R.string.gallery_from), draft.from) { draft = draft.copy(from = it) }
                GalleryDateField(localizedText(R.string.gallery_through), draft.through) { draft = draft.copy(through = it) }
                OutlinedTextField(draft.text, { draft = draft.copy(text = it.take(500)) }, label = { Text(localizedText(R.string.gallery_description)) }, modifier = Modifier.fillMaxWidth())
                if (!draft.valid) Text(localizedText(R.string.gallery_dates_invalid), color = MaterialTheme.colorScheme.error)
                if (error.isNotBlank()) {
                    Text(error, color = MaterialTheme.colorScheme.error)
                    TextButton(onClick = { retry++ }) { Text(localizedText(R.string.ui_retry)) }
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    TextButton(onClick = { bar.onFilters(GalleryFilterSelection()); open = false }) { Text(localizedText(R.string.gallery_clear)) }
                    Button(enabled = draft.valid && !loading && error.isBlank(), onClick = { bar.onFilters(draft); open = false }) { Text(localizedText(R.string.gallery_apply)) }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun GalleryDateField(label: String, value: LocalDate?, onChange: (LocalDate?) -> Unit) {
    var open by remember { mutableStateOf(false) }
    OutlinedButton(onClick = { open = true }, modifier = Modifier.fillMaxWidth()) { Text(label + ": " + (value?.toString() ?: localizedText(R.string.gallery_any_date))) }
    if (open) {
        val picker = rememberDatePickerState(initialSelectedDateMillis = value?.atStartOfDay(ZoneOffset.UTC)?.toInstant()?.toEpochMilli())
        DatePickerDialog(onDismissRequest = { open = false }, confirmButton = { TextButton(onClick = { onChange(picker.selectedDateMillis?.let { Instant.ofEpochMilli(it).atZone(ZoneOffset.UTC).toLocalDate() }); open = false }) { Text(localizedText(R.string.ui_accept)) } }, dismissButton = {
            TextButton(onClick = { onChange(null); open = false }) { Text(localizedText(R.string.gallery_clear)) }
        }) { DatePicker(picker) }
    }
}
