package com.luxisoft.realityos

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@Composable
internal fun SearchEvidenceCarousel(items: List<GalleryThumb>, initialIndex: Int, onClose: () -> Unit) {
    val language = RealityExperienceStore(LocalContext.current).selectedLanguage().languageTag
    var retry by remember { mutableIntStateOf(0) }
    val information = key(language, retry) { rememberEvidenceText(items, language, retry) }
    val pager = rememberPagerState(initialPage = initialIndex.coerceIn(0, items.lastIndex)) { items.size }
    val scope = rememberCoroutineScope()
    val zoomed = remember { mutableStateMapOf<Int, Boolean>() }
    var video by remember { mutableStateOf<GalleryThumb?>(null) }
    val playing = video
    if (playing != null) {
        BackHandler { video = null }
        Box(Modifier.fillMaxSize().background(Color.Black).safeDrawingPadding()) {
            DefaultViewerVideo(authorizedMediaUrl(playing.mediaUrl), SocialSession.token, videoStartMs(playing.frameTimestampMs ?: 0))
            IconButton(onClick = { video = null }, modifier = Modifier.align(Alignment.TopStart).statusBarsPadding()) {
                Icon(Icons.Filled.Close, stringResource(R.string.evidence_return_frame), tint = Color.White)
            }
        }
        return
    }
    HorizontalPager(
        state = pager,
        modifier = Modifier.fillMaxSize(),
        beyondViewportPageCount = 1,
        userScrollEnabled = zoomed[pager.currentPage] != true,
        key = { items[it].evidenceId.ifBlank { items[it].viewerUrl } }
    ) { page ->
        val item = items[page]
        MediaViewerScreen(
            title = information.values[item.evidenceId]?.let { it.title.ifBlank { it.labels.joinToString() } }?.ifBlank { null } ?: stringResource(R.string.evidence_title),
            mediaUrl = authorizedMediaUrl(item.viewerUrl), thumbnailUrl = authorizedMediaUrl(item.boxedUrl.ifBlank { item.thumbnailUrl }),
            mimeType = "image/jpeg", authToken = SocialSession.token, noteText = item.noteText, noteSource = item.noteSource,
            metaLines = emptyList(),
            informationInitiallyExpanded = true,
            reserveInformationSpace = true,
            informationHeader = { EvidenceHeader(item, language) },
            informationBody = {
                EvidenceInformationBody(item, information.values[item.evidenceId], information.loading, information.failed, information.pending, information.preparing) { retry++ }
            },
            topActions = { Text("${pager.currentPage + 1} / ${items.size}", color = Color.White, modifier = Modifier.padding(horizontal = 12.dp)) },
            onZoomChange = { zoomed[page] = it },
            beforeNotes = {
                val context = LocalContext.current
                LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
                    itemsIndexed(items) { index, thumb ->
                        DatabaseImage(
                            profileImageRequest(context, authorizedMediaUrl(thumb.boxedUrl.ifBlank { thumb.thumbnailUrl })),
                            stringResource(R.string.evidence_view_result, index + 1),
                            Modifier.size(56.dp).clip(RoundedCornerShape(8.dp))
                                .border(if (index == pager.currentPage) 2.dp else 0.dp, if (index == pager.currentPage) MaterialTheme.colorScheme.primary else Color.Transparent, RoundedCornerShape(8.dp))
                                .clickable { scope.launch { pager.animateScrollToPage(index) } },
                            contentScale = ContentScale.Crop
                        )
                    }
                }
                if (item.mimeType.startsWith("video/")) {
                    TextButton(onClick = { video = item }) {
                        Icon(Icons.Filled.PlayArrow, null)
                        Text(stringResource(R.string.evidence_play_video, evidenceTime(item.frameTimestampMs ?: 0)))
                    }
                }
            },
            onClose = onClose
        )
    }
}
