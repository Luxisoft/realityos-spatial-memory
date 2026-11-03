package com.luxisoft.realityos

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.*
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView

internal data class ViewerComment(val id: String, val text: String)

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
@Composable
internal fun DefaultViewerVideo(mediaUrl: String, authToken: String?, startPositionMs: Long = 0) {
    val context = LocalContext.current
    val token = authToken.orEmpty()
    var speeded by remember { mutableStateOf(false) }
    var buffering by remember(mediaUrl) { mutableStateOf(true) }
    var firstFrame by remember(mediaUrl) { mutableStateOf(false) }
    var videoError by remember(mediaUrl) { mutableStateOf(false) }
    var attempt by remember(mediaUrl) { mutableIntStateOf(0) }
    val player = remember(mediaUrl, token, attempt) {
        val dataSource = androidx.media3.datasource.DefaultHttpDataSource.Factory()
            .setDefaultRequestProperties(mediaAuthorization(mediaUrl, token))
        val source = androidx.media3.exoplayer.source.ProgressiveMediaSource.Factory(dataSource)
            .createMediaSource(androidx.media3.common.MediaItem.fromUri(mediaUrl))
        androidx.media3.exoplayer.ExoPlayer.Builder(context).build().apply {
            setMediaSource(source)
            repeatMode = androidx.media3.common.Player.REPEAT_MODE_ONE
            playWhenReady = true
        }
    }
    DisposableEffect(player) {
        val listener = object : androidx.media3.common.Player.Listener {
            override fun onPlaybackStateChanged(state: Int) {
                buffering = state == androidx.media3.common.Player.STATE_BUFFERING || (!firstFrame && state != androidx.media3.common.Player.STATE_ENDED)
            }
            override fun onRenderedFirstFrame() {
                firstFrame = true
                buffering = false
            }
            override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                buffering = false
                videoError = true
            }
        }
        buffering = true
        firstFrame = false
        videoError = false
        player.addListener(listener)
        player.prepare()
        player.seekTo(startPositionMs)
        onDispose {
            player.removeListener(listener)
            player.release()
        }
    }
    Box(Modifier.fillMaxSize()) {
        AndroidView(
            factory = { viewContext ->
                androidx.media3.ui.PlayerView(viewContext).apply {
                    this.player = player
                    useController = true
                    resizeMode = androidx.media3.ui.AspectRatioFrameLayout.RESIZE_MODE_FIT
                    setOnTouchListener { _, event ->
                        when (event.actionMasked) {
                            android.view.MotionEvent.ACTION_DOWN -> {
                                player.setPlaybackSpeed(2f)
                                speeded = true
                            }
                            android.view.MotionEvent.ACTION_UP, android.view.MotionEvent.ACTION_CANCEL -> {
                                player.setPlaybackSpeed(1f)
                                speeded = false
                            }
                        }
                        false
                    }
                }
            },
            update = { it.player = player },
            modifier = Modifier.fillMaxSize()
        )
        if (buffering && !videoError) Box(Modifier.matchParentSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        if (videoError) {
            Column(Modifier.align(Alignment.Center), horizontalAlignment = Alignment.CenterHorizontally) {
                Text(stringResource(R.string.media_load_failed), color = Color.White)
                Button(onClick = { attempt++ }) { Text(stringResource(R.string.ui_retry)) }
            }
        }
        if (speeded && !buffering) {
            Surface(
                shape = RoundedCornerShape(50),
                color = Color.Black.copy(alpha = 0.6f),
                modifier = Modifier.align(Alignment.TopCenter).padding(top = 72.dp)
            ) {
                Text("2×", color = Color.White, style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp))
            }
        }
    }
}

/**
 * Fullscreen image/video viewer. Info and the publication note live in a
 * frosted-glass information panel. Chat reserves space for an initially open
 * panel; other viewers keep their compact overlay until opened.
 */
@Composable
internal fun MediaViewerScreen(
    title: String,
    mediaUrl: String,
    thumbnailUrl: String,
    mimeType: String,
    authToken: String?,
    noteText: String,
    noteSource: String,
    metaLines: List<String>,
    comments: List<ViewerComment> = emptyList(),
    commentsLoading: Boolean = false,
    onCommentClick: (String) -> Unit = {},
    topActions: @Composable RowScope.() -> Unit = {},
    beforeNotes: @Composable () -> Unit = {},
    informationInitiallyExpanded: Boolean = true,
    reserveInformationSpace: Boolean = true,
    informationHeader: (@Composable RowScope.() -> Unit)? = null,
    informationBody: (@Composable () -> Unit)? = null,
    onZoomChange: (Boolean) -> Unit = {},
    videoContent: @Composable (String) -> Unit = { DefaultViewerVideo(it, authToken) },
    onClose: () -> Unit
) {
    val context = LocalContext.current
    var expanded by remember(mediaUrl) { mutableStateOf(informationInitiallyExpanded) }
    var informationHeight by remember { mutableIntStateOf(0) }
    val density = LocalDensity.current
    BackHandler { onClose() }
    val isVideo = mimeType.startsWith("video/")
    val backdrop = thumbnailUrl.ifBlank { mediaUrl }
    LaunchedEffect(mediaUrl) { onZoomChange(false) }
    var transform by remember(mediaUrl) { mutableStateOf(MediaZoomTransform()) }
    var imageSize by remember(mediaUrl) { mutableStateOf(IntSize.Zero) }
    var viewport by remember { mutableStateOf(IntSize.Zero) }

    var imageAttempt by remember(mediaUrl) { mutableIntStateOf(0) }
    val fullImageRequest = remember(context, mediaUrl, authToken, imageAttempt) {
        coil.request.ImageRequest.Builder(context).data(mediaUrl).setParameter("retry", imageAttempt)
            .authorizeMedia(mediaUrl, authToken).build()
    }
    val backdropRequest = remember(context, backdrop, authToken) {
        coil.request.ImageRequest.Builder(context).data(backdrop)
            .authorizeMedia(backdrop, authToken).build()
    }

    BoxWithConstraints(
        Modifier.fillMaxSize().background(Color.Black)
            .clickable(indication = null, interactionSource = remember { MutableInteractionSource() }) { }
    ) {
        val informationMaxHeight = maxHeight * 0.45f
        Box(Modifier.fillMaxSize().padding(bottom = if (reserveInformationSpace) with(density) { informationHeight.toDp() } else 0.dp)) {
            if (isVideo) {
                videoContent(mediaUrl)
            } else {
                Box(
                    Modifier.fillMaxSize().clipToBounds()
                        .onSizeChanged {
                            viewport = it
                            transform = MediaZoomTransform()
                            onZoomChange(false)
                        }
                        .pointerInput(mediaUrl, imageSize, viewport) {
                            awaitEachGesture {
                                awaitFirstDown(requireUnconsumed = false)
                                do {
                                    val event = awaitPointerEvent()
                                    val continuingPointers = event.changes.count { it.pressed && it.previousPressed }
                                    if (continuingPointers > 0 && (event.changes.count { it.pressed } > 1 || transform.scale > 1f)) {
                                        val centroid = event.calculateCentroid(useCurrent = false)
                                        val movement = event.calculatePan()
                                        val next = MediaZoomPolicy.transform(
                                            current = transform,
                                            viewportWidth = viewport.width,
                                            viewportHeight = viewport.height,
                                            imageWidth = imageSize.width,
                                            imageHeight = imageSize.height,
                                            centroidX = centroid.x,
                                            centroidY = centroid.y,
                                            movementX = movement.x,
                                            movementY = movement.y,
                                            scaleChange = event.calculateZoom()
                                        )
                                        val wasZoomed = transform.scale > 1f
                                        transform = next
                                        if (wasZoomed != (next.scale > 1f)) onZoomChange(next.scale > 1f)
                                        event.changes.forEach { it.consume() }
                                    }
                                } while (event.changes.any { it.pressed })
                            }
                        }
                ) {
                    coil.compose.SubcomposeAsyncImage(
                        model = fullImageRequest,
                        contentDescription = title,
                        contentScale = ContentScale.Inside,
                        modifier = Modifier.fillMaxSize().graphicsLayer {
                            scaleX = transform.scale
                            scaleY = transform.scale
                            translationX = transform.panX
                            translationY = transform.panY
                        },
                        onSuccess = {
                            imageSize = IntSize(it.result.drawable.intrinsicWidth, it.result.drawable.intrinsicHeight)
                        },
                        loading = {
                            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                CircularProgressIndicator()
                            }
                        },
                        error = {
                            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Icon(Icons.Filled.BrokenImage, contentDescription = stringResource(R.string.evidence_image_error), tint = Color.White.copy(alpha = 0.6f), modifier = Modifier.size(64.dp))
                                    Button(onClick = { imageAttempt++ }) { Text(stringResource(R.string.ui_retry)) }
                                }
                            }
                        }
                    )
                }
            }
        }
        Row(
            Modifier.align(Alignment.TopCenter).fillMaxWidth()
                .background(Color.Black.copy(alpha = 0.45f))
                .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Top + WindowInsetsSides.Horizontal))
                .padding(horizontal = 4.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onClose) { Icon(Icons.Filled.Close, contentDescription = stringResource(R.string.evidence_close), tint = Color.White) }
            Spacer(Modifier.weight(1f))
            topActions()
        }
        Box(
            Modifier.align(Alignment.BottomCenter).fillMaxWidth()
                .heightIn(max = informationMaxHeight).onSizeChanged { informationHeight = it.height }
                .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Bottom + WindowInsetsSides.Horizontal))
                .clip(RoundedCornerShape(topStart = 20.dp, topEnd = 20.dp))
                .then(if (informationHeader == null) Modifier.clickable { expanded = !expanded } else Modifier)
        ) {
            DatabaseImage(
                model = backdropRequest,
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier.matchParentSize().blur(28.dp)
            )
            Box(Modifier.matchParentSize().background(Color.Black.copy(alpha = 0.62f)))
            Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp, vertical = 12.dp)) {
                beforeNotes()
                Row(
                    modifier = Modifier.fillMaxWidth().then(if (informationHeader != null) Modifier.clickable { expanded = !expanded } else Modifier),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        if (expanded) Icons.Filled.KeyboardArrowDown else Icons.Filled.KeyboardArrowUp,
                        contentDescription = stringResource(if (expanded) R.string.evidence_hide_information else R.string.evidence_show_information),
                        tint = Color.White
                    )
                    if (informationHeader != null) {
                        informationHeader()
                    } else {
                        Text(
                            title.ifBlank { stringResource(R.string.evidence_publication) },
                            style = MaterialTheme.typography.titleSmall,
                            color = Color.White,
                            maxLines = if (expanded) Int.MAX_VALUE else 1,
                            overflow = TextOverflow.Ellipsis,
                            modifier = Modifier.weight(1f)
                        )
                        if (noteText.isNotBlank()) {
                            Icon(
                                if (noteSource == "voice") Icons.Filled.Mic else Icons.Filled.ShortText,
                                contentDescription = stringResource(if (noteSource == "voice") R.string.evidence_voice_note else R.string.evidence_note),
                                tint = Color(0xFF62A9F8)
                            )
                        }
                    }
                }
                AnimatedVisibility(visible = expanded, enter = expandVertically(), exit = shrinkVertically()) {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                        if (informationBody != null) {
                            informationBody()
                        } else {
                            if (noteText.isNotBlank()) {
                                Text(
                                    noteText,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = Color.White
                                )
                            }
                            metaLines.filter { it.isNotBlank() }.forEach { line ->
                                Text(line, style = MaterialTheme.typography.labelMedium, color = Color.White.copy(alpha = 0.75f))
                            }
                        }
                        if (commentsLoading) SkeletonLines()
                        comments.forEach { comment ->
                            Text(
                                comment.text,
                                style = MaterialTheme.typography.bodySmall,
                                color = Color.White.copy(alpha = 0.9f),
                                modifier = Modifier.clickable { onCommentClick(comment.id) }
                            )
                        }
                    }
                }
            }
        }
    }
}
