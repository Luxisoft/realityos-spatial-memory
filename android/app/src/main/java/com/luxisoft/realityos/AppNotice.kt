package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalAccessibilityManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.res.stringResource
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import java.util.UUID

internal enum class NoticeKind { INFO, SUCCESS, WARNING, ERROR }
internal data class AppNotice(val text: String, val kind: NoticeKind, val id: String = UUID.randomUUID().toString())
internal object AppNotices {
    val hosts = MutableStateFlow<Map<String, Int>>(emptyMap())
    val pending = MutableStateFlow<List<AppNotice>>(emptyList())
    fun show(text: String, kind: NoticeKind = NoticeKind.INFO) {
        if (text.isBlank()) return
        pending.update { queue -> if (queue.any { it.text == text && it.kind == kind }) queue else (queue + AppNotice(text, kind)).takeLast(5) }
    }
    fun dismiss(id: String) { pending.update { it.filterNot { notice -> notice.id == id } } }
}

@Composable
internal fun NoticeEffect(message: String, clear: () -> Unit, kind: NoticeKind = NoticeKind.ERROR) {
    LaunchedEffect(message) {
        if (message.isNotBlank()) {
            AppNotices.show(message, kind)
            clear()
        }
    }
}

private val LocalNoticeDepth = staticCompositionLocalOf { 0 }

@Composable
internal fun NoticeLayer(content: @Composable () -> Unit) {
    CompositionLocalProvider(LocalNoticeDepth provides (LocalNoticeDepth.current + 1)) {
        Box(Modifier.fillMaxSize()) {
            content()
            AppNoticeHost(Modifier.align(Alignment.BottomCenter))
        }
    }
}

@Composable
internal fun AppNoticeHost(modifier: Modifier = Modifier) {
    val hostId = remember { UUID.randomUUID().toString() }
    val depth = LocalNoticeDepth.current
    DisposableEffect(hostId, depth) {
        AppNotices.hosts.update { it + (hostId to depth) }
        onDispose {
            AppNotices.hosts.update { it - hostId }
            if (AppNotices.hosts.value.isEmpty()) AppNotices.pending.value = emptyList()
        }
    }
    val hosts by AppNotices.hosts.collectAsState()
    val notices by AppNotices.pending.collectAsState()
    if (hosts.entries.lastOrNull { it.value == hosts.values.maxOrNull() }?.key != hostId) return
    val notice = notices.firstOrNull() ?: return
    val accessibility = LocalAccessibilityManager.current
    val duration = if (notice.kind == NoticeKind.ERROR || notice.kind == NoticeKind.WARNING) 8000L else 4000L
    LaunchedEffect(notice.id) {
        delay(accessibility?.calculateRecommendedTimeoutMillis(duration, containsIcons = true, containsText = true, containsControls = true) ?: duration)
        AppNotices.dismiss(notice.id)
    }
    val color = when (notice.kind) {
        NoticeKind.ERROR -> MaterialTheme.colorScheme.error
        NoticeKind.WARNING -> MaterialTheme.colorScheme.secondary
        else -> MaterialTheme.colorScheme.primary
    }
    val icon = when (notice.kind) {
        NoticeKind.ERROR -> Icons.Default.ErrorOutline
        NoticeKind.WARNING -> Icons.Default.WarningAmber
        NoticeKind.SUCCESS -> Icons.Default.CheckCircleOutline
        else -> Icons.Default.Info
    }
    val title = stringResource(when (notice.kind) {
        NoticeKind.ERROR -> R.string.notice_error
        NoticeKind.WARNING -> R.string.notice_warning
        NoticeKind.SUCCESS -> R.string.notice_success
        else -> R.string.notice_information
    })
    Surface(modifier.fillMaxWidth().imePadding().navigationBarsPadding().padding(12.dp)
        .testTag("app-notice").semantics { liveRegion = LiveRegionMode.Polite },
        shape = RoundedCornerShape(12.dp), color = MaterialTheme.colorScheme.surface,
        border = androidx.compose.foundation.BorderStroke(1.dp, color), shadowElevation = 6.dp) {
        Row(Modifier.padding(start = 14.dp, top = 8.dp, bottom = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(icon, null, tint = color)
            Column(Modifier.weight(1f).padding(horizontal = 12.dp)) {
                Text(title, style = MaterialTheme.typography.titleSmall, color = color)
                Text(notice.text, style = MaterialTheme.typography.bodyMedium)
            }
            IconButton(onClick = { AppNotices.dismiss(notice.id) }, modifier = Modifier.testTag("notice-dismiss")) {
                Icon(Icons.Default.Close, stringResource(R.string.ui_dismiss_notice))
            }
        }
    }
}
