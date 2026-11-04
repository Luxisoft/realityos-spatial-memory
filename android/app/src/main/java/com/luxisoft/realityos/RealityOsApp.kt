package com.luxisoft.realityos

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.Velocity
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.facebook.login.LoginManager
import com.luxisoft.realityos.host.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

internal enum class HostDestination {
    PROFILE,
    GALLERY,
    META_DISPLAY
}

internal enum class MetaSection { PREVIEW, GLASSES }

/**
 * Native host shell for compatible Meta Ray-Ban Display sessions. The phone is
 * deliberately a calm host surface: operational Register and Query controls
 * remain on the glasses, while connection and simulation live in the drawer.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RealityOsApp(
    viewModel: RealityViewModel,
    onRegisterWithMeta: () -> Unit,
    onConnectDisplay: () -> Unit,
    onDisconnectDisplay: () -> Unit
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val experienceStore = remember(context.applicationContext) {
        RealityExperienceStore(context.applicationContext)
    }
    var showWelcome by rememberSaveable {
        mutableStateOf(!experienceStore.hasCompletedWelcome())
    }
    var replayingWelcome by rememberSaveable { mutableStateOf(false) }

    LaunchedEffect(SocialSession.active) {
        viewModel?.stopSpeak()
        if (SocialSession.active) viewModel.refreshMetaConfiguration() else viewModel.clearMetaAccount()
    }

    RealityOsTheme {
        NoticeLayer {
            if (showWelcome) {
                RealityWelcome(
                    replay = replayingWelcome,
                    onFinish = {
                        if (!replayingWelcome) experienceStore.completeWelcome()
                        showWelcome = false
                        replayingWelcome = false
                    }
                )
            } else if (!SocialSession.active) {
                SocialGallery(viewModel, onWelcome = {
                    replayingWelcome = true
                    showWelcome = true
                })
            } else {
                AccountBiometricGate {
                    RealityHostShell(
                        state = state,
                        experienceStore = experienceStore,
                        viewModel = viewModel,
                        onRegisterWithMeta = onRegisterWithMeta,
                        onConnectDisplay = onConnectDisplay,
                        onDisconnectDisplay = onDisconnectDisplay,
                        onReplayWelcome = {
                            replayingWelcome = true
                            showWelcome = true
                        }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RealityHostShell(
    state: RealityUiState,
    experienceStore: RealityExperienceStore,
    viewModel: RealityViewModel,
    onRegisterWithMeta: () -> Unit,
    onConnectDisplay: () -> Unit,
    onDisconnectDisplay: () -> Unit,
    onReplayWelcome: () -> Unit
) {
    val drawerState = rememberDrawerState(initialValue = androidx.compose.material3.DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    var selectedName by rememberSaveable { mutableStateOf(HostDestination.PROFILE.name) }
    val selected = remember(selectedName) { HostDestination.entries.firstOrNull { it.name == selectedName } ?: HostDestination.PROFILE }
    // The host gallery is always work: starting here avoids flashing another feed first.
    var audience by rememberSaveable { mutableStateOf("work") }
    var metaSectionName by rememberSaveable { mutableStateOf(MetaSection.PREVIEW.name) }
    val metaSection = remember(metaSectionName) { MetaSection.valueOf(metaSectionName) }
    var previewControlsOpen by rememberSaveable { mutableStateOf(false) }
    var bottomBarVisible by rememberSaveable { mutableStateOf(true) }
    var mediaViewerOpen by rememberSaveable { mutableStateOf(false) }
    var profileEditOpen by rememberSaveable { mutableStateOf(false) }
    var groupAdminOpen by rememberSaveable { mutableStateOf(false) }
    var showSearchSheet by rememberSaveable { mutableStateOf(false) }
    var showConnections by rememberSaveable { mutableStateOf(false) }
    val chatMessages = remember { mutableStateListOf<ChatMessage>() }
    LaunchedEffect(SocialSession.active) {
        // History belongs to one profile: drop it on login/logout switches.
        chatMessages.clear()
        if (SocialSession.active) {
            runCatching { experienceStore.syncAccountLanguage() }
        }
    }
    val galleryBar = remember { GalleryTopBarState() }
    val profileState = rememberProfileState()
    LaunchedEffect(selected) { mediaViewerOpen = false }
    val swipePages = remember { HostSwipeNavigation.pages }
    val pagerState = rememberPagerState(initialPage = HostSwipeNavigation.pageFor(selected).coerceAtLeast(0)) { swipePages.size }
    LaunchedEffect(selected) {
        val target = HostSwipeNavigation.pageFor(selected)
        if (target >= 0 && pagerState.currentPage != target) pagerState.animateScrollToPage(target)
    }
    LaunchedEffect(pagerState) {
        snapshotFlow { pagerState.settledPage }.collect { page ->
            val destination = HostSwipeNavigation.destinationFor(page)
            if (destination != null && selected in swipePages && selectedName != destination.name) {
                // Mirror the bottom-bar side effect: the host gallery is always work.
                if (destination == HostDestination.GALLERY) audience = "work"
                selectedName = destination.name
            }
        }
    }
    val phoneCaptureActive = state.wearable.inputRoute == InputRoute.PHONE && state.wearable.cameraActive
    val keepNavigationVisible by rememberUpdatedState(phoneCaptureActive)
    val bottomBarRevealJob = remember { mutableStateOf<Job?>(null) }
    val bottomBarScrollConnection = remember(scope) {
        object : NestedScrollConnection {
            override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset {
                if (keepNavigationVisible) {
                    bottomBarRevealJob.value?.cancel()
                    bottomBarVisible = true
                    return Offset.Zero
                }
                when {
                    available.y < -1f -> {
                        bottomBarVisible = false
                        bottomBarRevealJob.value?.cancel()
                        bottomBarRevealJob.value = scope.launch {
                            delay(450)
                            bottomBarVisible = true
                        }
                    }
                    available.y > 1f -> {
                        bottomBarRevealJob.value?.cancel()
                        bottomBarVisible = true
                    }
                }
                return Offset.Zero
            }

            override suspend fun onPostFling(consumed: Velocity, available: Velocity): Velocity {
                bottomBarRevealJob.value?.cancel()
                bottomBarVisible = true
                return Velocity.Zero
            }
        }
    }
    var confirmCaptureExit by remember { mutableStateOf(false) }
    BackHandler(enabled = phoneCaptureActive) {
        if (state.recording) confirmCaptureExit = true else viewModel.cancelPhoneCapture()
    }
    if (confirmCaptureExit) {
        androidx.compose.material3.AlertDialog(
            onDismissRequest = { confirmCaptureExit = false },
            title = { Text(localizedText(R.string.ui_exit_recording)) },
            text = { Text(localizedText(R.string.ui_you_can_save_or_discard_the_video_before_leaving)) },
            confirmButton = {
                TextButton(onClick = {
                    confirmCaptureExit = false
                    viewModel.togglePreviewVideo()
                }) { Text(localizedText(R.string.ui_save_and_exit)) }
            },
            dismissButton = {
                TextButton(onClick = {
                    confirmCaptureExit = false
                    viewModel.cancelPhoneCapture()
                }) { Text(localizedText(R.string.ui_discard_and_exit)) }
            }
        )
    }

    LaunchedEffect(phoneCaptureActive) {
        if (phoneCaptureActive) {
            bottomBarVisible = true
            if (selected == HostDestination.META_DISPLAY) metaSectionName = MetaSection.PREVIEW.name
        }
    }
    LaunchedEffect(selected, metaSection, showSearchSheet) {
        if (selected != HostDestination.META_DISPLAY || metaSection != MetaSection.PREVIEW || showSearchSheet) {
            viewModel.onPhonePreviewHidden()
        }
    }
    LaunchedEffect(selected) {
        bottomBarRevealJob.value?.cancel()
        bottomBarVisible = true
    }

    BackHandler(enabled = previewControlsOpen) {
        previewControlsOpen = false
    }
    BackHandler(enabled = drawerState.isOpen && !previewControlsOpen) {
        scope.launch { drawerState.close() }
    }
    LaunchedEffect(state.message, state.virtualProfileError) {
        val message = state.virtualProfileError ?: state.message
        if (message.isNotBlank()) AppNotices.show(message, if (state.virtualProfileError != null) NoticeKind.ERROR else NoticeKind.INFO)
    }

    ModalNavigationDrawer(
        drawerState = drawerState,
        gesturesEnabled = drawerState.isOpen || (!previewControlsOpen && !mediaViewerOpen && selected == HostDestination.PROFILE),
        drawerContent = {
            RealityDrawer(
                experienceStore = experienceStore,
                onConnections = {
                    scope.launch {
                        drawerState.close()
                        showConnections = true
                    }
                },
                onAbout = {
                    scope.launch { drawerState.close() }
                    onReplayWelcome()
                },
                onLogout = {
                    viewModel.cancelPhoneCapture()
                    val identity = SocialSession.identity
                    scope.launch {
                        withContext(Dispatchers.IO) {
                            runCatching { SocialSession.request("auth/logout", org.json.JSONObject(), identity) }
                        }
                        if (SocialSession.isCurrent(identity)) {
                            SocialSession.clearIfCurrent(identity)
                            LoginManager.getInstance().logOut()
                        }
                        drawerState.close()
                    }
                }
            )
        }
    ) {
        Box(Modifier.fillMaxSize()) {
            Scaffold(
                containerColor = MaterialTheme.colorScheme.background,
                contentWindowInsets = WindowInsets.safeDrawing,
                topBar = {
                    if (!mediaViewerOpen) {
                        Column(Modifier.statusBarsPadding()) {
                            ProfileHeader(
                                state = profileState,
                                onMenu = { scope.launch { drawerState.open() } },
                                onGlasses = {
                                    showSearchSheet = false
                                    selectedName = HostDestination.META_DISPLAY.name
                                },
                                onEditDrawerChange = { profileEditOpen = it }
                            )
                            if (!showSearchSheet && (selected == HostDestination.GALLERY || selected == HostDestination.META_DISPLAY)) {
                                HostTopBar(
                                    selected = selected,
                                    audience = audience,
                                    metaSection = metaSection,
                                    galleryBar = galleryBar,
                                    onSelectMeta = { metaSectionName = it.name },
                                    onOpenMetaControls = { previewControlsOpen = true }
                                )
                            }
                        }
                    }
                },
                bottomBar = {
                    AnimatedVisibility(
                        visible = !mediaViewerOpen && !showSearchSheet && !showConnections && (phoneCaptureActive || bottomBarVisible),
                        enter = slideInVertically { fullHeight -> fullHeight },
                        exit = slideOutVertically { fullHeight -> fullHeight }
                    ) {
                        SocialBottomBar(
                            selected = selected,
                            profilePictureUrl = SocialSession.profilePictureUrl,
                            onProfile = { selectedName = HostDestination.PROFILE.name },
                            onWork = {
                                audience = "work"
                                selectedName = HostDestination.GALLERY.name
                            },
                            onSearch = { showSearchSheet = true }
                        )
                    }
                },
                snackbarHost = {}
            ) { contentPadding ->
                Box(
                    Modifier
                        .fillMaxSize()
                        .padding(contentPadding)
                        .consumeWindowInsets(contentPadding)
                        .nestedScroll(bottomBarScrollConnection)
                        .drawerEdgeOpen(
                            enabled = !previewControlsOpen && !mediaViewerOpen && !drawerState.isOpen && selected == HostDestination.PROFILE,
                            onOpen = { scope.launch { drawerState.open() } }
                        )
                ) {
                    if (selected in swipePages) {
                        HorizontalPager(
                            state = pagerState,
                            modifier = Modifier.fillMaxSize(),
                            beyondViewportPageCount = 2,
                            userScrollEnabled = !mediaViewerOpen && !drawerState.isOpen && !profileEditOpen && !(groupAdminOpen && selected == HostDestination.GALLERY)
                        ) { page ->
                            Box(
                                Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)
                            ) {
                                when (swipePages[page]) {
                                    HostDestination.PROFILE -> ProfileScreen(viewModel = viewModel, onViewerChange = { mediaViewerOpen = it }, sharedProfile = profileState, active = selected == HostDestination.PROFILE, captureUploadStatus = state.meta.uploadStatus)
                                    HostDestination.GALLERY -> SocialGallery(viewModel, audience = audience, onWelcome = onReplayWelcome, onViewerChange = { mediaViewerOpen = it }, galleryBar = galleryBar, onAdminDrawerChange = { groupAdminOpen = it })
                                    else -> {}
                                }
                            }
                        }
                    } else {
                        AnimatedContent(
                            targetState = selected,
                            transitionSpec = { fadeIn(tween(220)) togetherWith fadeOut(tween(120)) },
                            label = "host-destination",
                            modifier = Modifier.fillMaxSize()
                        ) { destination ->
                            when (destination) {
                                HostDestination.PROFILE -> ProfileScreen(viewModel = viewModel, onViewerChange = { mediaViewerOpen = it }, sharedProfile = profileState, active = selected == HostDestination.PROFILE, captureUploadStatus = state.meta.uploadStatus)
                                HostDestination.GALLERY -> SocialGallery(viewModel, audience = audience, onWelcome = onReplayWelcome, onViewerChange = { mediaViewerOpen = it }, galleryBar = galleryBar, onAdminDrawerChange = { groupAdminOpen = it })
                                HostDestination.META_DISPLAY -> when (metaSection) {
                                    MetaSection.PREVIEW -> PreviewDestination(state = state, viewModel = viewModel)
                                    MetaSection.GLASSES -> GlassesDestination(
                                        state = state,
                                        viewModel = viewModel,
                                        onRegisterWithMeta = onRegisterWithMeta,
                                        onConnectDisplay = onConnectDisplay,
                                        onDisconnectDisplay = onDisconnectDisplay
                                    )
                                }
                            }
                        }
                    }
                }
            }
            if (showSearchSheet) {
                RootPanel(onClose = { showSearchSheet = false }) {
                    UnifiedSearch(chatMessages, viewModel)
                }
            }
            if (showConnections) {
                RootPanel(onClose = { showConnections = false }) {
                    StorageConnectionsScreen { showConnections = false }
                }
            }
            PreviewControlsOverlay(visible = previewControlsOpen, onDismiss = { previewControlsOpen = false }) {
                PreviewControlPanel(
                    state = state,
                    viewModel = viewModel,
                    onOpenGlasses = {
                        previewControlsOpen = false
                        selectedName = HostDestination.META_DISPLAY.name
                        metaSectionName = MetaSection.GLASSES.name
                    },
                    modifier = Modifier.fillMaxWidth()
                )
            }
            DisplayProfileOverlay(viewModel)
        }
    }
}
