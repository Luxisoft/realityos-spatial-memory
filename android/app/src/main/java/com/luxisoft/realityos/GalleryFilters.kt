package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.isActive

@Composable
internal fun GalleryFilterButton(
    bar: GalleryTopBarState,
    fetchOptions: (suspend (String?) -> PublicationCatalog)? = null
) {
    val repository = remember(SocialSession.identity) { GalleryRepository() }
    val identity = SocialSession.identity
    var open by remember(bar, identity) { mutableStateOf(false) }
    var draft by remember(bar, bar.selectedId, identity) { mutableStateOf(bar.filters) }
    var options by remember(bar.selectedId, identity) { mutableStateOf<PublicationCatalog?>(null) }
    var error by remember(bar.selectedId, identity) { mutableStateOf("") }
    var loading by remember(bar.selectedId, identity) { mutableStateOf(false) }
    var retry by remember(bar.selectedId, identity) { mutableIntStateOf(0) }
    LaunchedEffect(bar.filters, bar.selectedId, identity) { draft = bar.filters }
    fun updateFilters(value: GalleryFilterSelection) {
        draft = value
        if (value.valid && value != bar.filters) bar.onFilters(value)
    }
    LaunchedEffect(open, bar.selectedId, identity, retry) {
        if (!open) return@LaunchedEffect
        loading = true
        error = ""
        options = null
        try {
            val catalog = fetchOptions?.invoke(bar.selectedId) ?: repository.filterOptions(bar.selectedId)
            coroutineContext.ensureActive()
            options = catalog
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (failure: Exception) {
            coroutineContext.ensureActive()
            error = localizedFailure(failure)
        } finally {
            if (coroutineContext.isActive) loading = false
        }
    }
    val config = LocalConfiguration.current
    Box {
        IconButton(onClick = {
            draft = bar.filters
            open = true
        }, modifier = Modifier.testTag("gallery-filter")) {
            Icon(Icons.Default.FilterList, localizedText(R.string.gallery_filters), tint = if (bar.filters.active) MaterialTheme.colorScheme.primary else LocalContentColor.current)
        }
        key(bar.selectedId, identity) {
            DropdownMenu(expanded = open, onDismissRequest = { open = false }, modifier = Modifier.widthIn(max = (config.screenWidthDp - 24).dp).heightIn(max = (config.screenHeightDp * .8f).dp)) {
                Column(Modifier.widthIn(min = 240.dp, max = 360.dp).padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        Text(localizedText(R.string.gallery_filters), style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f).testTag("gallery-filter-title"))
                        TextButton(onClick = { updateFilters(GalleryFilterSelection()) }, modifier = Modifier.testTag("gallery-filter-clear")) {
                            Text(localizedText(R.string.gallery_clear))
                        }
                    }
                    if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
                    CatalogSelect(localizedText(R.string.catalog_categories), options?.categories.orEmpty(), draft.categories, enabled = !loading && error.isBlank(), showWorkspace = bar.selectedId == null) { updateFilters(draft.copy(categories = it)) }
                    CatalogSelect(localizedText(R.string.catalog_tags), options?.tags.orEmpty(), draft.tags, enabled = !loading && error.isBlank(), showWorkspace = bar.selectedId == null) { updateFilters(draft.copy(tags = it)) }
                    CatalogSelect(localizedText(R.string.gallery_authors), options?.owners.orEmpty(), draft.owners, enabled = !loading && error.isBlank(), showWorkspace = bar.selectedId == null) { updateFilters(draft.copy(owners = it)) }
                    GalleryDateField(localizedText(R.string.gallery_from), draft.from) { updateFilters(draft.copy(from = it)) }
                    GalleryDateField(localizedText(R.string.gallery_through), draft.through) { updateFilters(draft.copy(through = it)) }
                    OutlinedTextField(draft.text, { updateFilters(draft.copy(text = it.take(500))) }, label = { Text(localizedText(R.string.gallery_description)) }, modifier = Modifier.fillMaxWidth())
                    if (!draft.valid) Text(localizedText(R.string.gallery_dates_invalid), color = MaterialTheme.colorScheme.error)
                    if (error.isNotBlank()) {
                        Text(error, color = MaterialTheme.colorScheme.error)
                        TextButton(onClick = { retry++ }) { Text(localizedText(R.string.ui_retry)) }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun GalleryDateField(label: String, value: LocalDate?, onChange: (LocalDate?) -> Unit) {
    var open by remember { mutableStateOf(false) }
    OutlinedButton(onClick = { open = true }, modifier = Modifier.fillMaxWidth()) { Text(label + ": " + (value?.let { evidenceDate(it.toString(), LocalizedText.languageTag) } ?: localizedText(R.string.gallery_any_date))) }
    if (open) {
        val picker = rememberDatePickerState(initialSelectedDateMillis = value?.atStartOfDay(ZoneOffset.UTC)?.toInstant()?.toEpochMilli())
        DatePickerDialog(onDismissRequest = { open = false }, confirmButton = {
            TextButton(onClick = {
                onChange(picker.selectedDateMillis?.let { Instant.ofEpochMilli(it).atZone(ZoneOffset.UTC).toLocalDate() })
                open = false
            }) { Text(localizedText(R.string.ui_accept)) }
        }, dismissButton = {
            TextButton(onClick = {
                onChange(null)
                open = false
            }) { Text(localizedText(R.string.gallery_clear)) }
        }) { DatePicker(picker) }
    }
}
