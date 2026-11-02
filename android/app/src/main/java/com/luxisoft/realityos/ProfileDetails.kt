package com.luxisoft.realityos

import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONObject

internal data class EditableProfileLink(val label: String = "", val url: String = "")

@Composable
internal fun ProfileEditDrawer(
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
    onUploadCv: () -> Unit
) {
    ModalDrawerSheet(
        modifier = Modifier.fillMaxHeight().widthIn(min = 320.dp, max = 360.dp),
        drawerContainerColor = MaterialTheme.colorScheme.surface
    ) {
        LazyColumn(
            modifier = Modifier.testTag("profile-edit-fields"),
            contentPadding = PaddingValues(start = 18.dp, top = 2.dp, end = 18.dp, bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            item {
                Row(
                    modifier = Modifier.fillMaxWidth().height(46.dp),
                    verticalAlignment = Alignment.CenterVertically
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
                            modifier = Modifier.weight(.4f)
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
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedButton(onClick = { onLinksChange(links + EditableProfileLink()) }) { Text(localizedText(R.string.ui_add_social_link)) }
                    Button(onClick = onSave, enabled = !busy) { Text(localizedText(R.string.ui_save)) }
                }
            }
            item { HorizontalDivider(Modifier.padding(vertical = 8.dp)) }
            item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(localizedText(R.string.ui_resume), style = MaterialTheme.typography.titleMedium)
                    OutlinedButton(onClick = onUploadCv, enabled = !busy, modifier = Modifier.testTag("profile-cv-upload")) {
                        Text(localizedText(if (cv.optBoolean("present")) R.string.ui_update_resume else R.string.ui_upload_resume))
                    }
                    Text(
                        when (cv.optString("status")) {
                            "ready" -> localizedText(R.string.ui_updated_available_for_ai_questions)
                            "failed" -> localizedText(R.string.ui_processing_failed_you_can_retry)
                            "processing", "pending" -> localizedText(R.string.ui_updating_professional_information)
                            else -> localizedText(R.string.ui_you_have_not_uploaded_a_resume_yet)
                        },
                        color = MaterialTheme.colorScheme.onSurfaceVariant
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
    val onClick: (() -> Unit)? = null
)

@Composable
internal fun ProfileInformation(
    profile: JSONObject,
    headline: String,
    phone: String,
    website: String,
    links: List<EditableProfileLink>,
    onOpenLink: (String) -> Unit
) {
    val counts = profile.optJSONObject("counts") ?: JSONObject()
    val age = listOf(profile.optString("age_min"), profile.optString("age_max"))
        .filter { it.isNotBlank() && it != "null" }
        .distinct()
        .joinToString("–")
    val items = buildList {
        add(ProfileInfoItem(localizedText(R.string.ui_location), profile.optString("location"), Icons.Default.LocationOn))
        add(ProfileInfoItem(localizedText(R.string.ui_hometown), profile.optString("hometown"), Icons.Default.Home))
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
                horizontalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                rowItems.forEach { item ->
                    Row(
                        modifier = Modifier
                            .weight(1f)
                            .then(item.onClick?.let { onClick -> Modifier.clickable(onClick = onClick) } ?: Modifier)
                            .padding(vertical = 2.dp),
                        verticalAlignment = Alignment.Top,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = item.icon,
                            contentDescription = item.label,
                            modifier = Modifier.size(19.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                item.label,
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            Text(
                                item.value,
                                style = MaterialTheme.typography.bodySmall,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                }
                if (rowItems.size == 1) Spacer(Modifier.weight(1f))
            }
        }
    }
}

internal fun profileMediaUrl(path: String): String {
    if (path.startsWith("http")) return path
    val base = BuildConfig.DEFAULT_REALITYOS_API_BASE_URL.trimEnd('/')
    return if (path.startsWith("/v1/")) {
        "${base.removeSuffix("/v1")}$path"
    } else {
        "$base/${path.trimStart('/')}"
    }
}

internal fun profileImageRequest(context: android.content.Context, path: String): coil.request.ImageRequest = coil.request.ImageRequest.Builder(context)
    .data(profileMediaUrl(path))
    .addHeader("Authorization", "Bearer ${SocialSession.token}")
    .build()

@Composable
internal fun ProfileWebView(url: String, onBack: () -> Unit) {
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
            modifier = Modifier.fillMaxSize()
        )
    }
}

/** Explicitly distinguish the retained Work demo scenes from captured evidence. */
@Composable
internal fun PublicationSourceBadge(source: String, modifier: Modifier = Modifier) {
    if (source.startsWith("simulator")) {
        Surface(modifier = modifier.testTag("publication-simulated"), color = MaterialTheme.colorScheme.surface.copy(alpha = .9f)) {
            Text(localizedText(R.string.profile_simulated_media), Modifier.padding(horizontal = 5.dp, vertical = 2.dp), style = MaterialTheme.typography.labelSmall)
        }
    }
}
