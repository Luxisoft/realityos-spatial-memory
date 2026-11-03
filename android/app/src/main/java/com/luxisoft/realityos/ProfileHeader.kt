package com.luxisoft.realityos

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.adamglin.PhosphorIcons
import com.adamglin.phosphoricons.Regular
import com.adamglin.phosphoricons.regular.Eyeglasses
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

/** One profile request shared by the host chrome and its publication screen. */
internal class ProfileState(val userId: String? = null) {
    var profile by mutableStateOf<JSONObject?>(null)
        private set
    var loading by mutableStateOf(true)
        private set
    var error by mutableStateOf("")
        private set

    fun apply(value: JSONObject) {
        profile = value
        if (userId == null) SocialSession.profilePictureUrl = value.optText("picture_url")
    }

    suspend fun load() {
        loading = true
        error = ""
        try {
            val path = userId?.let { "profiles/$it" } ?: "me/profile"
            apply(withContext(Dispatchers.IO) { JSONObject(SocialSession.request(path)) })
        } catch (failure: CancellationException) {
            throw failure
        } catch (failure: Exception) {
            error = failure.message.orEmpty()
        } finally {
            loading = false
        }
    }
}

@Composable
internal fun rememberProfileState(userId: String? = null): ProfileState {
    val state = remember(userId, SocialSession.workspaceId) { ProfileState(userId) }
    LaunchedEffect(state) { state.load() }
    return state
}

internal fun profileLinks(profile: JSONObject): List<EditableProfileLink> {
    val values = profile.optJSONArray("social_links") ?: JSONArray()
    return (0 until values.length()).map { index ->
        values.getJSONObject(index).let { EditableProfileLink(it.optString("label"), it.optString("url")) }
    }
}

@Composable
internal fun ProfileHeader(
    state: ProfileState,
    onMenu: (() -> Unit)? = null,
    onBack: (() -> Unit)? = null,
    onGlasses: (() -> Unit)? = null,
    onEditDrawerChange: (Boolean) -> Unit = {}
) {
    val context = LocalContext.current
    val clipboard = LocalClipboardManager.current
    val scope = rememberCoroutineScope()
    var expanded by rememberSaveable(state.userId) { mutableStateOf(false) }
    var editing by rememberSaveable(state.userId) { mutableStateOf(false) }
    var webUrl by rememberSaveable(state.userId) { mutableStateOf<String?>(null) }
    val current = state.profile
    val facebookProfile = current?.optString("profile_source") == "facebook"
    LaunchedEffect(editing) { onEditDrawerChange(editing) }
    DisposableEffect(Unit) { onDispose { onEditDrawerChange(false) } }
    fun openLink(url: String, facebook: Boolean = false) {
        if (facebook) {
            try {
                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).setPackage("com.facebook.katana"))
                return
            } catch (_: ActivityNotFoundException) {
                // Keep the existing in-app browser fallback.
            }
        }
        webUrl = url
    }
    Surface(tonalElevation = 1.dp, modifier = Modifier.testTag("global-profile-header")) {
        Column(Modifier.fillMaxWidth()) {
            Row(
                Modifier.fillMaxWidth().heightIn(min = 64.dp).padding(horizontal = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                val navigation = onBack ?: onMenu
                if (navigation != null) {
                    IconButton(onClick = navigation, modifier = Modifier.testTag("host-menu-button")) {
                        Icon(if (onBack != null) Icons.Default.ArrowBack else Icons.Default.Menu, localizedText(if (onBack != null) R.string.ui_back else R.string.content_open_menu))
                    }
                }
                Box(Modifier.size(52.dp)) {
                    val picture = current?.optText("picture_url")
                    if (picture != null) {
                        DatabaseImage(
                            profileImageRequest(context, picture),
                            current.optString("display_name"),
                            Modifier.size(48.dp).clip(CircleShape),
                            contentScale = ContentScale.Crop
                        )
                    } else {
                        Icon(Icons.Default.AccountCircle, null, Modifier.size(48.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    if (state.userId == null && current != null) {
                        IconButton(onClick = { editing = true }, modifier = Modifier.align(Alignment.BottomEnd).size(32.dp).testTag("profile-edit")) {
                            Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primary) {
                                Icon(Icons.Default.Edit, localizedText(R.string.ui_edit_profile), Modifier.padding(3.dp).size(16.dp))
                            }
                        }
                    }
                }
                Column(Modifier.weight(1f)) {
                    if (current == null && state.loading) {
                        SkeletonLines(rows = 2)
                    } else {
                        Text(current?.optString("display_name").orEmpty(), Modifier.testTag("profile-name"), style = MaterialTheme.typography.titleSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        current?.optText("email")?.let { email ->
                            Text(
                                email,
                                Modifier.clickable {
                                    clipboard.setText(AnnotatedString(email))
                                    AppNotices.show(localizedText(R.string.ui_email_copied), NoticeKind.SUCCESS)
                                }.testTag("profile-email"),
                                style = MaterialTheme.typography.bodySmall,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                }
                IconButton(onClick = { expanded = !expanded }, enabled = current != null, modifier = Modifier.size(48.dp).testTag("profile-expand")) {
                    Icon(if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore, localizedText(if (expanded) R.string.ui_hide_information else R.string.ui_show_information))
                }
                Column {
                    current?.optText("facebook_link")?.takeIf { facebookProfile }?.let { facebook ->
                        IconButton(onClick = { openLink(facebook, true) }, modifier = Modifier.testTag("profile-facebook")) {
                            Icon(Icons.Default.Facebook, localizedText(R.string.ui_open_facebook))
                        }
                    }
                    if (onGlasses != null) {
                        IconButton(onClick = onGlasses, modifier = Modifier.testTag("profile-glasses")) {
                            Icon(PhosphorIcons.Regular.Eyeglasses, localizedText(R.string.ui_glasses))
                        }
                    }
                }
            }
            NoticeEffect(state.error, {})
            AnimatedVisibility(expanded && current != null) {
                Column(
                    Modifier.fillMaxWidth().heightIn(max = (LocalConfiguration.current.screenHeightDp * .4f).dp)
                        .verticalScroll(rememberScrollState()).padding(16.dp).testTag("profile-details"),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    if (current != null) {
                        ProfileInformation(current, current.optString("headline"), current.optString("phone"), current.optString("website"), profileLinks(current), { openLink(it) })
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            Icon(Icons.Default.Description, null)
                            Text(current.optText("biography") ?: "-", style = MaterialTheme.typography.bodyMedium)
                        }
                        val friends = if (facebookProfile) current.optJSONArray("friends") ?: JSONArray() else JSONArray()
                        for (index in 0 until minOf(friends.length(), 6)) {
                            val friend = friends.getJSONObject(index)
                            TextButton(onClick = { friend.optText("profile_link")?.let { openLink(it, true) } }) {
                                Text(friend.optString("name"))
                            }
                        }
                    }
                }
            }
        }
    }
    if (editing && current != null) ProfileEditor(state, onClose = { editing = false })
    webUrl?.let { url ->
        Dialog(onDismissRequest = { webUrl = null }, properties = DialogProperties(usePlatformDefaultWidth = false)) {
            Surface(Modifier.fillMaxSize()) { ProfileWebView(url) { webUrl = null } }
        }
    }
}

@Composable
private fun ProfileEditor(state: ProfileState, onClose: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val current = state.profile ?: return
    var headline by rememberSaveable { mutableStateOf(current.optString("headline")) }
    var biography by rememberSaveable { mutableStateOf(current.optString("biography")) }
    var phone by rememberSaveable { mutableStateOf(current.optString("phone")) }
    var website by rememberSaveable { mutableStateOf(current.optString("website")) }
    var links by remember { mutableStateOf(profileLinks(current)) }
    var personal by rememberSaveable(stateSaver = PersonalProfileDraft.Saver) { mutableStateOf(PersonalProfileDraft.from(current)) }
    var personalErrors by remember { mutableStateOf(emptyMap<String, Int>()) }
    val personalEditable = current.optBoolean("personal_details_editable")
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    val pickCv = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            scope.launch {
                busy = true
                error = ""
                try {
                    val value = withContext(Dispatchers.IO) {
                        val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                            ?: error(localizedText(R.string.ui_could_not_read_the_resume))
                        val mime = context.contentResolver.getType(uri) ?: "application/pdf"
                        JSONObject(SocialSession.requestMultipart("me/profile/cv", emptyMap(), bytes, uri.lastPathSegment?.substringAfterLast('/') ?: "cv", mime))
                    }
                    state.apply(value)
                } catch (failure: CancellationException) {
                    throw failure
                } catch (failure: Exception) {
                    error = failure.message.orEmpty()
                } finally {
                    busy = false
                }
            }
        }
    }
    Dialog(onDismissRequest = { if (!busy) onClose() }, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.CenterEnd) {
            Column(Modifier.widthIn(max = 360.dp)) {
                NoticeEffect(error, { error = "" })
                ProfileEditDrawer(
                    headline, { headline = it }, biography, { biography = it }, phone, { phone = it },
                    website, { website = it }, links, { links = it }, current.optJSONObject("cv") ?: JSONObject(), busy,
                    onClose = { if (!busy) onClose() },
                    onSave = {
                        personalErrors = if (personalEditable) personal.errors() else emptyMap()
                        if (personalErrors.isNotEmpty()) return@ProfileEditDrawer
                        scope.launch {
                            busy = true
                            error = ""
                            try {
                                val payload = JSONObject().put("headline", headline).put("biography", biography)
                                    .put("phone", phone).put("website", website).put(
                                        "social_links",
                                        JSONArray().apply {
                                            links.filter { it.label.isNotBlank() && it.url.isNotBlank() }.forEach { put(JSONObject().put("label", it.label).put("url", it.url)) }
                                        }
                                    )
                                if (personalEditable) personal.addTo(payload)
                                state.apply(withContext(Dispatchers.IO) { JSONObject(SocialSession.requestJson("me/profile", "PATCH", payload)) })
                                onClose()
                            } catch (failure: CancellationException) {
                                throw failure
                            } catch (failure: Exception) {
                                error = failure.message.orEmpty()
                            } finally {
                                busy = false
                            }
                        }
                    },
                    onUploadCv = { pickCv.launch(arrayOf("application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")) },
                    personal = personal,
                    onPersonalChange = {
                        personal = it
                        personalErrors = emptyMap()
                    },
                    personalEditable = personalEditable,
                    facebook = current.optString("profile_source") == "facebook",
                    personalErrors = personalErrors
                )
            }
        }
    }
}
