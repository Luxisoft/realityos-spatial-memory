package com.luxisoft.realityos

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.Scaffold
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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.saveable.rememberSaveableStateHolder
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.luxisoft.realityos.host.*
import kotlinx.coroutines.launch

internal enum class HostDestination {
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
        viewModel.stopSpeak()
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
    var selectedName by rememberSaveable { mutableStateOf(HostDestination.GALLERY.name) }
    val selected = remember(selectedName) { HostDestination.entries.firstOrNull { it.name == selectedName } ?: HostDestination.GALLERY }
    var metaSectionName by rememberSaveable { mutableStateOf(MetaSection.PREVIEW.name) }
    val metaSection = remember(metaSectionName) { MetaSection.valueOf(metaSectionName) }
    var previewControlsOpen by rememberSaveable { mutableStateOf(false) }
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
    val savedScreens = rememberSaveableStateHolder()
    val galleryBar = remember { GalleryTopBarState() }
    val profileState = rememberProfileState()
    LaunchedEffect(selected) { mediaViewerOpen = false }
    val phoneCaptureActive = state.wearable.inputRoute == InputRoute.PHONE && state.wearable.cameraActive
    var confirmCaptureExit by remember { mutableStateOf(false) }
    var pendingNavigation by remember { mutableStateOf<(() -> Unit)?>(null) }
    fun navigate(action: () -> Unit) {
        if (phoneCaptureActive && state.recording) {
            pendingNavigation = action
            confirmCaptureExit = true
        } else {
            action()
        }
    }
    LaunchedEffect(state.meta.pendingMime) {
        if (state.meta.pendingMime != null && pendingNavigation != null) {
            pendingNavigation?.invoke()
            pendingNavigation = null
        }
    }
    BackHandler(enabled = selected == HostDestination.META_DISPLAY && !phoneCaptureActive && !previewControlsOpen && !showSearchSheet && !showConnections && !profileEditOpen) {
        selectedName = HostDestination.GALLERY.name
    }
    BackHandler(enabled = phoneCaptureActive) {
        if (state.recording) confirmCaptureExit = true else viewModel.cancelPhoneCapture()
    }
    if (confirmCaptureExit) {
        androidx.compose.material3.AlertDialog(
            onDismissRequest = {
                confirmCaptureExit = false
                pendingNavigation = null
            },
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
                    pendingNavigation?.invoke()
                    pendingNavigation = null
                }) { Text(localizedText(R.string.ui_discard_and_exit)) }
            }
        )
    }

    LaunchedEffect(phoneCaptureActive) {
        if (phoneCaptureActive) {
            if (selected == HostDestination.META_DISPLAY) metaSectionName = MetaSection.PREVIEW.name
        }
    }
    LaunchedEffect(selected, metaSection, showSearchSheet) {
        if (selected != HostDestination.META_DISPLAY || metaSection != MetaSection.PREVIEW || showSearchSheet) {
            viewModel.onPhonePreviewHidden()
        }
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
        gesturesEnabled = drawerState.isOpen,
        drawerContent = {
            RealityDrawer(
                experienceStore = experienceStore,
                onConnections = {
                    scope.launch {
                        drawerState.close()
                        navigate { showConnections = true }
                    }
                },
                onAbout = {
                    scope.launch { drawerState.close() }
                    navigate { onReplayWelcome() }
                },
                onLogout = {
                    viewModel.cancelPhoneCapture()
                    scope.launch {
                        drawerState.close()
                        SocialSession.signOut()
                    }
                }
            )
        }
    ) {
        Box(Modifier.fillMaxSize()) {
            Scaffold(
                containerColor = MaterialTheme.colorScheme.background,
                contentWindowInsets = WindowInsets.safeDrawing,
                bottomBar = {
                    if (!mediaViewerOpen && !showSearchSheet && !showConnections && !groupAdminOpen && !previewControlsOpen) {
                        ProfileHeader(
                            state = profileState,
                            bottom = true,
                            onMenu = { scope.launch { drawerState.open() } },
                            onAvatar = { navigate { selectedName = HostDestination.GALLERY.name } },
                            onGlasses = { selectedName = HostDestination.META_DISPLAY.name },
                            onSearch = { navigate { showSearchSheet = true } },
                            onEditDrawerChange = { profileEditOpen = it }
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
                        .drawerEdgeOpen(
                            enabled = !previewControlsOpen && !mediaViewerOpen && !profileEditOpen && !groupAdminOpen && !drawerState.isOpen && selected == HostDestination.GALLERY,
                            onOpen = { scope.launch { drawerState.open() } }
                        )
                ) {
                    savedScreens.SaveableStateProvider(selected.name) {
                        when (selected) {
                            HostDestination.GALLERY -> SocialGallery(
                                viewModel,
                                onWelcome = onReplayWelcome,
                                onViewerChange = { mediaViewerOpen = it },
                                galleryBar = galleryBar,
                                onAdminDrawerChange = { groupAdminOpen = it },
                                capturePublicationRevision = state.meta.publicationRevision
                            )
                            HostDestination.META_DISPLAY -> Column(Modifier.fillMaxSize()) {
                                MetaViewHeader(
                                    title = localizedText(
                                        if (metaSection == MetaSection.GLASSES) {
                                            R.string.ui_glasses
                                        } else if (BuildConfig.DEBUG) {
                                            R.string.preview_simulator_title
                                        } else {
                                            R.string.preview_live_title
                                        }
                                    ),
                                    metaSection = metaSection,
                                    onSelectMeta = { section -> navigate { metaSectionName = section.name } },
                                    onOpenMetaControls = { previewControlsOpen = true }
                                )
                                Box(Modifier.weight(1f)) {
                                    when (metaSection) {
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
