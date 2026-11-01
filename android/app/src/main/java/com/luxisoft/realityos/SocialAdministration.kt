package com.luxisoft.realityos

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.PersonRemove
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

private data class PendingAdminAction(
    val method: String,
    val path: String,
    val message: String,
    val deletesGroup: Boolean = false
)

/** Right-side administration drawer. Every operation is independently authorized by the server. */
@Composable
internal fun SocialAdministration(
    workspaceId: String?,
    onDismiss: () -> Unit,
    onGroupDeleted: () -> Unit = {}
) {
    var loading by remember(workspaceId) { mutableStateOf(true) }
    var members by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var reports by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var pin by remember { mutableStateOf<String?>(null) }
    var pinAvailable by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    var revision by remember { mutableIntStateOf(0) }
    var pending by remember { mutableStateOf<PendingAdminAction?>(null) }
    var viewingProfile by remember { mutableStateOf<String?>(null) }
    var panelVisible by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    fun close() {
        scope.launch {
            panelVisible = false
            delay(250)
            onDismiss()
        }
    }
    LaunchedEffect(Unit) { panelVisible = true }
    LaunchedEffect(workspaceId, revision) {
        loading = true
        error = ""
        try {
            val loaded = withContext(Dispatchers.IO) {
                val memberArray = if (workspaceId != null) {
                    try {
                        JSONArray(SocialSession.request("groups/$workspaceId/members"))
                    } catch (_: Exception) {
                        JSONArray()
                    }
                } else {
                    JSONArray()
                }
                val groupPin = if (workspaceId != null) {
                    try {
                        JSONObject(SocialSession.request("groups/$workspaceId/pin")).getString("join_pin")
                    } catch (_: Exception) {
                        null
                    }
                } else {
                    null
                }
                val reportArray = JSONArray(SocialSession.request(if (workspaceId == null) "moderation/reports" else "groups/$workspaceId/reports"))
                Triple(
                    (0 until memberArray.length()).map { memberArray.getJSONObject(it) },
                    groupPin,
                    (0 until reportArray.length()).map { reportArray.getJSONObject(it) }
                )
            }
            members = loaded.first
            pin = loaded.second
            pinAvailable = workspaceId != null && loaded.second != null
            reports = loaded.third
        } catch (e: Exception) {
            error = e.message.orEmpty()
        } finally {
            loading = false
        }
    }
    val myRow = members.firstOrNull { it.optBoolean("self") }
    val myRole = myRow?.optString("role").orEmpty()
    val iAmAdmin = myRole == "admin"
    val iCanInvite = GroupAdminPolicy.canInvite(myRole, myRow?.optBoolean("can_invite") == true)
    fun runAdmin(action: PendingAdminAction) {
        scope.launch {
            try {
                withContext(Dispatchers.IO) {
                    SocialSession.requestJson(action.path, action.method, JSONObject())
                }
                pending = null
                if (action.deletesGroup) onGroupDeleted() else revision++
            } catch (e: Exception) {
                error = e.message.orEmpty()
                pending = null
            }
        }
    }
    Box(Modifier.fillMaxSize()) {
        Box(
            Modifier.fillMaxSize()
                .background(Color.Black.copy(alpha = 0.45f))
                .clickable(role = Role.Button, onClickLabel = localizedText(R.string.ui_close_administration), onClick = ::close)
        )
        AnimatedVisibility(
            visible = panelVisible,
            enter = slideInHorizontally(initialOffsetX = { it }),
            exit = slideOutHorizontally(targetOffsetX = { it }),
            modifier = Modifier.align(Alignment.CenterEnd)
        ) {
            Surface(
                Modifier.fillMaxHeight().widthIn(max = 400.dp).fillMaxWidth(0.94f),
                tonalElevation = 4.dp
            ) {
                val profileId = viewingProfile
                if (profileId != null) {
                    ProfileScreen(userId = profileId, onBack = { viewingProfile = null })
                } else {
                    Column(
                        Modifier.fillMaxSize().padding(16.dp)
                            .verticalScroll(rememberScrollState())
                    ) {
                        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                if (workspaceId == null) localizedText(R.string.ui_reports) else localizedText(R.string.ui_manage_group),
                                style = MaterialTheme.typography.titleLarge,
                                modifier = Modifier.weight(1f)
                            )
                            IconButton(onClick = ::close) {
                                Icon(Icons.Filled.Close, contentDescription = localizedText(R.string.ui_close))
                            }
                        }
                        if (error.isNotBlank()) {
                            Text(error, color = MaterialTheme.colorScheme.error)
                        }
                        if (loading) {
                            SkeletonList(Modifier.padding(top = 16.dp), rows = 6)
                        } else {
                            if (pinAvailable) {
                                Spacer(Modifier.height(8.dp))
                                Text(localizedText(R.string.ui_join_pin), style = MaterialTheme.typography.titleMedium)
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text(
                                        pin.orEmpty(),
                                        style = MaterialTheme.typography.headlineMedium,
                                        modifier = Modifier.weight(1f)
                                    )
                                    IconButton(onClick = {
                                        scope.launch {
                                            try {
                                                val rotated = withContext(Dispatchers.IO) {
                                                    JSONObject(
                                                        SocialSession.request(
                                                            "groups/$workspaceId/pin/rotate",
                                                            JSONObject()
                                                        )
                                                    ).getString("join_pin")
                                                }
                                                pin = rotated
                                            } catch (e: Exception) {
                                                error = e.message.orEmpty()
                                            }
                                        }
                                    }) {
                                        Icon(Icons.Filled.Refresh, contentDescription = localizedText(R.string.ui_generate_new_pin))
                                    }
                                }
                                Text(
                                    localizedText(R.string.ui_generating_a_new_one_invalidates_the_previous_one),
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                            if (workspaceId != null) {
                                Spacer(Modifier.height(12.dp))
                                Text(localizedText(R.string.ui_members), style = MaterialTheme.typography.titleMedium)
                                if (members.isEmpty() && error.isBlank()) Text(localizedText(R.string.ui_no_access_to_the_member_list))
                                members.forEach { member ->
                                    val targetRole = member.optString("role")
                                    val targetSelf = member.optBoolean("self")
                                    val badges = buildList {
                                        if (member.optBoolean("creator")) add(localizedText(R.string.ui_creator))
                                        if (targetRole == "admin") add("Admin")
                                        if (member.optBoolean("can_invite")) add(localizedText(R.string.ui_can_invite))
                                        if (targetSelf) add(localizedText(R.string.ui_you))
                                    }
                                    Row(
                                        Modifier.fillMaxWidth()
                                            .clickable(
                                                role = Role.Button,
                                                onClickLabel = localizedText(R.string.ui_view_profile),
                                                onClick = { viewingProfile = member.getString("id") }
                                            )
                                            .padding(vertical = 8.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Column(Modifier.weight(1f)) {
                                            Text(member.optString("name"), style = MaterialTheme.typography.titleSmall)
                                            if (badges.isNotEmpty()) {
                                                Text(
                                                    badges.joinToString(" · "),
                                                    style = MaterialTheme.typography.bodySmall,
                                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                                )
                                            }
                                        }
                                        if (iAmAdmin && !targetSelf && targetRole != "admin") {
                                            Switch(
                                                checked = member.optBoolean("can_invite"),
                                                onCheckedChange = { allowed ->
                                                    scope.launch {
                                                        try {
                                                            withContext(Dispatchers.IO) {
                                                                SocialSession.request(
                                                                    "groups/$workspaceId/members/${member.getString("id")}/invite-permission",
                                                                    JSONObject().put("allowed", allowed)
                                                                )
                                                            }
                                                            revision++
                                                        } catch (e: Exception) {
                                                            error = e.message.orEmpty()
                                                        }
                                                    }
                                                }
                                            )
                                        }
                                        if (iCanInvite && GroupAdminPolicy.canRemoveMember(myRole, iCanInvite, targetRole)) {
                                            IconButton(onClick = {
                                                pending = PendingAdminAction(
                                                    "POST",
                                                    "groups/$workspaceId/members/${member.getString("id")}/remove",
                                                    localizedText(R.string.ui_remove_this_person_from_the_group)
                                                )
                                            }) {
                                                Icon(Icons.Filled.PersonRemove, contentDescription = localizedText(R.string.ui_remove_from_group))
                                            }
                                        }
                                    }
                                    HorizontalDivider()
                                }
                                if (GroupAdminPolicy.showDeleteGroup(myRow?.optBoolean("creator") == true)) {
                                    Spacer(Modifier.height(12.dp))
                                    Button(
                                        onClick = {
                                            pending = PendingAdminAction(
                                                "DELETE",
                                                "groups/$workspaceId",
                                                localizedText(R.string.ui_delete_this_group_publications_become_personal_to_their_authors),
                                                deletesGroup = true
                                            )
                                        },
                                        colors = ButtonDefaults.buttonColors(
                                            containerColor = MaterialTheme.colorScheme.error,
                                            contentColor = MaterialTheme.colorScheme.onError
                                        )
                                    ) {
                                        Icon(Icons.Filled.Delete, contentDescription = null)
                                        Spacer(Modifier.width(8.dp))
                                        Text(localizedText(R.string.ui_delete_group))
                                    }
                                }
                            }
                            Spacer(Modifier.height(12.dp))
                            Text(localizedText(R.string.ui_content_reports), style = MaterialTheme.typography.titleMedium)
                            if (reports.isEmpty() && error.isBlank()) Text(localizedText(R.string.ui_no_pending_reports))
                            reports.forEach { report ->
                                Text(report.getString("reason"))
                                TextButton(onClick = {
                                    val postId = report.getString("post_id")
                                    pending = PendingAdminAction(
                                        "POST",
                                        if (workspaceId == null) "moderation/$postId/hide" else "groups/$workspaceId/hide/$postId",
                                        localizedText(R.string.ui_hide_this_publication)
                                    )
                                }) { Text(localizedText(R.string.ui_hide_content)) }
                            }
                            Spacer(Modifier.height(24.dp))
                        }
                    }
                }
            }
        }
    }
    pending?.let { action ->
        var submitting by remember { mutableStateOf(false) }
        if (submitting) LaunchedEffect(action) { runAdmin(action) }
        AlertDialog(
            onDismissRequest = { if (!submitting) pending = null },
            title = { Text(action.message) },
            confirmButton = {
                TextButton(enabled = !submitting, onClick = { submitting = true }) { Text(localizedText(R.string.ui_confirm)) }
            },
            dismissButton = {
                TextButton(enabled = !submitting, onClick = { pending = null }) { Text(localizedText(R.string.ui_cancel)) }
            }
        )
    }
}
