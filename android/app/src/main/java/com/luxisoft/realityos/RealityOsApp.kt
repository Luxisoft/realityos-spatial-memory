package com.luxisoft.realityos

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.outlined.BugReport
import androidx.compose.material.icons.outlined.Cable
import androidx.compose.material.icons.outlined.Language
import androidx.compose.material.icons.outlined.Memory
import androidx.compose.material.icons.outlined.SettingsInputComponent
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.NavigationDrawerItemDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import kotlinx.coroutines.launch

private enum class HostDestination {
    PREVIEW,
    CONNECTION,
    GLASSES,
    DEVELOPER,
    LANGUAGE,
    ABOUT,
}

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
    onDisconnectDisplay: () -> Unit,
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

    RealityOsTheme {
        if (showWelcome) {
            RealityWelcome(
                replay = replayingWelcome,
                onFinish = {
                    if (!replayingWelcome) experienceStore.completeWelcome()
                    showWelcome = false
                    replayingWelcome = false
                },
            )
        } else {
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
                },
            )
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
    onReplayWelcome: () -> Unit,
) {
    val drawerState = rememberDrawerState(initialValue = androidx.compose.material3.DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }
    var selectedName by rememberSaveable { mutableStateOf(HostDestination.PREVIEW.name) }
    val selected = remember(selectedName) { HostDestination.valueOf(selectedName) }

    BackHandler(enabled = drawerState.isOpen) {
        scope.launch { drawerState.close() }
    }
    LaunchedEffect(state.message, state.virtualProfileError) {
        val message = state.virtualProfileError ?: state.message
        if (message.isNotBlank()) snackbarHostState.showSnackbar(message)
    }

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            RealityDrawer(
                state = state,
                selected = selected,
                onSelect = { destination ->
                    selectedName = destination.name
                    scope.launch { drawerState.close() }
                },
            )
        },
    ) {
        Scaffold(
            containerColor = MaterialTheme.colorScheme.background,
            contentWindowInsets = WindowInsets.safeDrawing,
            topBar = {
                RealityTopBar(
                    state = state,
                    onOpenDrawer = { scope.launch { drawerState.open() } },
                )
            },
            snackbarHost = { SnackbarHost(snackbarHostState) },
        ) { contentPadding ->
            AnimatedContent(
                targetState = selected,
                transitionSpec = {
                    fadeIn(animationSpec = tween(220)) togetherWith fadeOut(animationSpec = tween(120))
                },
                label = "host-destination",
                modifier = Modifier
                    .fillMaxSize()
                    .padding(contentPadding),
            ) { destination ->
                when (destination) {
                    HostDestination.PREVIEW -> PreviewDestination(
                        state = state,
                        viewModel = viewModel,
                        onOpenGlasses = { selectedName = HostDestination.GLASSES.name },
                    )
                    HostDestination.CONNECTION -> ConnectionDestination(viewModel, state)
                    HostDestination.GLASSES -> GlassesDestination(
                        state = state,
                        onRegisterWithMeta = onRegisterWithMeta,
                        onConnectDisplay = onConnectDisplay,
                        onDisconnectDisplay = onDisconnectDisplay,
                    )
                    HostDestination.DEVELOPER -> {
                        if (BuildConfig.DEBUG) {
                            DeveloperLabControls(viewModel = viewModel)
                        } else {
                            PreviewDestination(
                                state = state,
                                viewModel = viewModel,
                                onOpenGlasses = { selectedName = HostDestination.GLASSES.name },
                            )
                        }
                    }
                    HostDestination.LANGUAGE -> LanguageDestination(experienceStore)
                    HostDestination.ABOUT -> AboutDestination(onReplayWelcome)
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RealityTopBar(state: RealityUiState, onOpenDrawer: () -> Unit) {
    val connected = state.wearable.sessionActive
    val live = state.provisioning?.processingMode?.equals("live", ignoreCase = true) == true
    TopAppBar(
        navigationIcon = {
            IconButton(onClick = onOpenDrawer) {
                Icon(Icons.Filled.Menu, contentDescription = stringResource(R.string.content_open_menu))
            }
        },
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                ImageMark(size = 34.dp)
                Spacer(Modifier.width(10.dp))
                Column(verticalArrangement = Arrangement.spacedBy(1.dp)) {
                    Text("RealityOS", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text(
                        if (live) "${stringResource(R.string.brand_spatial_memory)} · ${stringResource(R.string.status_live)}"
                        else stringResource(R.string.brand_spatial_memory),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.primary,
                        maxLines = 1,
                    )
                }
            }
        },
        actions = { ConnectionPill(connected = connected) },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = MaterialTheme.colorScheme.background,
            titleContentColor = MaterialTheme.colorScheme.onBackground,
        ),
    )
}

@Composable
private fun ConnectionPill(connected: Boolean) {
    val signal by animateColorAsState(
        targetValue = if (connected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline,
        label = "connection-color",
    )
    Surface(
        color = signal.copy(alpha = if (connected) 0.16f else 0.10f),
        contentColor = if (connected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
        shape = CircleShape,
        modifier = Modifier.padding(end = 12.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Box(Modifier.size(7.dp).clip(CircleShape).background(signal))
            Text(
                if (connected) stringResource(R.string.status_connected) else stringResource(R.string.status_ready),
                style = MaterialTheme.typography.labelMedium,
                maxLines = 1,
            )
        }
    }
}

@Composable
private fun RealityDrawer(
    state: RealityUiState,
    selected: HostDestination,
    onSelect: (HostDestination) -> Unit,
) {
    ModalDrawerSheet(
        modifier = Modifier.widthIn(max = 344.dp),
        drawerContainerColor = MaterialTheme.colorScheme.surface,
        drawerContentColor = MaterialTheme.colorScheme.onSurface,
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 14.dp),
        ) {
            Row(
                modifier = Modifier.padding(start = 10.dp, top = 30.dp, bottom = 22.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                ImageMark(size = 46.dp)
                Spacer(Modifier.width(12.dp))
                Column {
                    Text("RealityOS", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text(
                        stringResource(R.string.drawer_tagline),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            DrawerConnectionSummary(state)
            Spacer(Modifier.height(16.dp))
            DrawerItem(HostDestination.PREVIEW, selected, R.string.nav_preview, Icons.Outlined.Visibility, onSelect)
            DrawerItem(HostDestination.CONNECTION, selected, R.string.nav_connection, Icons.Outlined.Cable, onSelect)
            DrawerItem(HostDestination.GLASSES, selected, R.string.nav_glasses, Icons.Outlined.SettingsInputComponent, onSelect)
            if (BuildConfig.DEBUG) {
                DrawerItem(HostDestination.DEVELOPER, selected, R.string.nav_developer_lab, Icons.Outlined.BugReport, onSelect)
            }
            HorizontalDivider(
                modifier = Modifier.padding(vertical = 12.dp),
                color = MaterialTheme.colorScheme.outlineVariant,
            )
            DrawerItem(HostDestination.LANGUAGE, selected, R.string.nav_language, Icons.Outlined.Language, onSelect)
            DrawerItem(HostDestination.ABOUT, selected, R.string.nav_about, Icons.Outlined.Memory, onSelect)
            Spacer(Modifier.weight(1f))
            Text(
                stringResource(R.string.drawer_footer),
                modifier = Modifier.padding(10.dp, 14.dp),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun DrawerConnectionSummary(state: RealityUiState) {
    val isLive = state.provisioning?.processingMode?.equals("live", ignoreCase = true) == true
    Surface(
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = MaterialTheme.shapes.medium,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(if (isLive) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.secondary),
            )
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    stringResource(R.string.drawer_connection_summary),
                    style = MaterialTheme.typography.labelLarge,
                )
                Text(
                    if (isLive) stringResource(R.string.status_live) else stringResource(R.string.status_setup),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun DrawerItem(
    destination: HostDestination,
    selected: HostDestination,
    label: Int,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    onSelect: (HostDestination) -> Unit,
) {
    NavigationDrawerItem(
        label = { Text(stringResource(label)) },
        selected = destination == selected,
        onClick = { onSelect(destination) },
        icon = { Icon(icon, contentDescription = null) },
        modifier = Modifier.padding(NavigationDrawerItemDefaults.ItemPadding),
    )
}

@Composable
private fun PreviewDestination(
    state: RealityUiState,
    viewModel: RealityViewModel,
    onOpenGlasses: () -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        contentAlignment = Alignment.Center,
    ) {
        if (BuildConfig.DEBUG) {
            DeveloperPreviewStage(
                viewModel = viewModel,
                enabled = !state.wearable.sessionActive,
                modifier = Modifier.fillMaxWidth(),
            )
        } else {
            LiveDisplayStage(
                state = state,
                onOpenGlasses = onOpenGlasses,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}

@Composable
private fun LiveDisplayStage(
    state: RealityUiState,
    onOpenGlasses: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier.widthIn(max = 520.dp),
        shape = MaterialTheme.shapes.extraLarge,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1f)
                    .clip(RoundedCornerShape(28.dp))
                    .background(Color.Black),
                contentAlignment = Alignment.Center,
            ) {
                MemoryField(active = state.wearable.sessionActive)
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.padding(28.dp),
                ) {
                    Text(
                        if (state.wearable.sessionActive) {
                            stringResource(R.string.preview_live_title)
                        } else {
                            stringResource(R.string.preview_waiting_title)
                        },
                        style = MaterialTheme.typography.headlineSmall,
                        textAlign = TextAlign.Center,
                    )
                    Spacer(Modifier.height(10.dp))
                    Text(
                        if (state.wearable.sessionActive) {
                            stringResource(R.string.preview_live_body)
                        } else {
                            stringResource(R.string.preview_waiting_body)
                        },
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center,
                    )
                }
            }
            if (!state.wearable.sessionActive) {
                Button(onClick = onOpenGlasses, modifier = Modifier.fillMaxWidth()) {
                    Text(stringResource(R.string.preview_open_glasses))
                }
            }
        }
    }
}

@Composable
private fun MemoryField(active: Boolean) {
    val trace = if (active) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline
    Canvas(modifier = Modifier.fillMaxSize()) {
        val width = size.width
        val height = size.height
        val path = Path().apply {
            moveTo(width * 0.06f, height * 0.68f)
            cubicTo(width * 0.26f, height * 0.40f, width * 0.40f, height * 0.81f, width * 0.60f, height * 0.50f)
            cubicTo(width * 0.77f, height * 0.22f, width * 0.88f, height * 0.43f, width * 0.96f, height * 0.28f)
        }
        drawPath(path, trace.copy(alpha = 0.38f), style = Stroke(width = 4.dp.toPx()))
        listOf(0.11f to 0.62f, 0.34f to 0.52f, 0.58f to 0.50f, 0.84f to 0.35f).forEachIndexed { index, point ->
            val radius = if (index == 2 && active) 14.dp.toPx() else 8.dp.toPx()
            drawCircle(trace.copy(alpha = if (index == 2) 0.9f else 0.48f), radius, androidx.compose.ui.geometry.Offset(width * point.first, height * point.second))
        }
    }
}

@Composable
private fun ConnectionDestination(viewModel: RealityViewModel, state: RealityUiState) {
    var showCustom by rememberSaveable { mutableStateOf(false) }
    var revealKey by rememberSaveable { mutableStateOf(false) }
    val draft = state.provisioningDraft
    LazyColumn(
        modifier = Modifier.fillMaxSize().imePadding(),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            SectionHeading(
                title = stringResource(R.string.connection_title),
                body = stringResource(R.string.connection_subtitle),
            )
        }
        item {
            Card(shape = MaterialTheme.shapes.large) {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(stringResource(R.string.connection_automatic), style = MaterialTheme.typography.titleLarge)
                    Text(
                        stringResource(R.string.connection_automatic_body),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    if (state.virtualProfileLoading) {
                        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                        Text(
                            stringResource(R.string.connection_loading),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    state.provisioning?.let { provisioned ->
                        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                        StatusRow(stringResource(R.string.connection_default_server), provisioned.apiBaseUrl)
                        StatusRow(
                            stringResource(R.string.connection_workspace),
                            provisioned.workspaceName ?: provisioned.workspaceId,
                        )
                        StatusRow(stringResource(R.string.connection_device), provisioned.deviceId)
                        provisioned.expiresAt?.let { expiry ->
                            StatusRow(
                                stringResource(R.string.connection_credential),
                                stringResource(R.string.connection_expiry, formatExpiry(expiry)),
                            )
                        }
                    }
                    Button(
                        onClick = { viewModel.loadVirtualDeviceProfile(saveAutomatically = true) },
                        enabled = !state.virtualProfileLoading,
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text(stringResource(R.string.connection_refresh)) }
                }
            }
        }
        item {
            OutlinedButton(onClick = { showCustom = !showCustom }, modifier = Modifier.fillMaxWidth()) {
                Text(stringResource(if (showCustom) R.string.connection_hide_custom else R.string.connection_custom))
            }
        }
        if (showCustom) {
            item {
                Card(
                    shape = MaterialTheme.shapes.large,
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                ) {
                    Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                        Text(stringResource(R.string.connection_custom), style = MaterialTheme.typography.titleLarge)
                        Text(
                            stringResource(R.string.connection_custom_body),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        OutlinedTextField(
                            value = draft.apiBaseUrl,
                            onValueChange = { viewModel.updateProvisioningDraft(apiBaseUrl = it) },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text(stringResource(R.string.connection_server_url)) },
                            supportingText = { Text(stringResource(R.string.connection_server_hint)) },
                            singleLine = true,
                        )
                        OutlinedTextField(
                            value = draft.workspaceId,
                            onValueChange = { viewModel.updateProvisioningDraft(workspaceId = it) },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text(stringResource(R.string.connection_workspace_id)) },
                            supportingText = { Text(stringResource(R.string.connection_workspace_hint)) },
                            singleLine = true,
                        )
                        OutlinedTextField(
                            value = draft.deviceId,
                            onValueChange = { viewModel.updateProvisioningDraft(deviceId = it) },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text(stringResource(R.string.connection_device_id)) },
                            supportingText = { Text(stringResource(R.string.connection_device_hint)) },
                            singleLine = true,
                        )
                        OutlinedTextField(
                            value = draft.deviceKey,
                            onValueChange = { viewModel.updateProvisioningDraft(deviceKey = it) },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text(stringResource(R.string.connection_device_key)) },
                            supportingText = { Text(stringResource(R.string.connection_key_hint)) },
                            visualTransformation = if (revealKey) VisualTransformation.None else PasswordVisualTransformation(),
                            singleLine = true,
                        )
                        TextButton(onClick = { revealKey = !revealKey }) {
                            Text(stringResource(if (revealKey) R.string.connection_hide_key else R.string.connection_show_key))
                        }
                        Button(onClick = viewModel::saveProvisioning, modifier = Modifier.fillMaxWidth()) {
                            Text(stringResource(R.string.connection_save_custom))
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun GlassesDestination(
    state: RealityUiState,
    onRegisterWithMeta: () -> Unit,
    onConnectDisplay: () -> Unit,
    onDisconnectDisplay: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionHeading(
            title = stringResource(R.string.glasses_title),
            body = stringResource(R.string.glasses_body),
        )
        Card(shape = MaterialTheme.shapes.large) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Text("DAT", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                StatusRow(
                    stringResource(R.string.glasses_registration),
                    state.wearable.registration.lowercase().replace('_', ' '),
                )
                StatusRow(
                    stringResource(R.string.glasses_device),
                    stringResource(if (state.wearable.deviceAvailable) R.string.glasses_available else R.string.glasses_not_detected),
                )
                StatusRow(
                    stringResource(R.string.glasses_display),
                    stringResource(if (state.wearable.sessionActive) R.string.glasses_active else R.string.glasses_not_connected),
                )
                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                OutlinedButton(onClick = onRegisterWithMeta, modifier = Modifier.fillMaxWidth()) {
                    Text(stringResource(R.string.glasses_register))
                }
                if (state.wearable.sessionActive) {
                    OutlinedButton(onClick = onDisconnectDisplay, modifier = Modifier.fillMaxWidth()) {
                        Text(stringResource(R.string.glasses_disconnect))
                    }
                } else {
                    Button(onClick = onConnectDisplay, modifier = Modifier.fillMaxWidth()) {
                        Text(stringResource(R.string.glasses_connect))
                    }
                }
            }
        }
        Surface(
            color = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
            shape = MaterialTheme.shapes.medium,
        ) {
            Text(
                stringResource(R.string.glasses_capture_note),
                modifier = Modifier.padding(16.dp),
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}

@Composable
private fun LanguageDestination(experienceStore: RealityExperienceStore) {
    val selected = experienceStore.selectedLanguage()
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionHeading(
            title = stringResource(R.string.language_title),
            body = stringResource(R.string.language_body),
        )
        LanguageOption(
            label = stringResource(R.string.language_english),
            selected = selected == RealityLanguage.ENGLISH,
            onClick = { experienceStore.setLanguage(RealityLanguage.ENGLISH) },
        )
        LanguageOption(
            label = stringResource(R.string.language_spanish),
            selected = selected == RealityLanguage.SPANISH,
            onClick = { experienceStore.setLanguage(RealityLanguage.SPANISH) },
        )
    }
}

@Composable
private fun LanguageOption(label: String, selected: Boolean, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = if (selected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface,
            contentColor = if (selected) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface,
        ),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(
            modifier = Modifier.padding(20.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(label, modifier = Modifier.weight(1f), style = MaterialTheme.typography.titleLarge)
            if (selected) {
                Text(
                    stringResource(R.string.language_selected),
                    style = MaterialTheme.typography.labelMedium,
                )
            }
        }
    }
}

@Composable
internal fun SectionHeading(title: String, body: String) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(title, style = MaterialTheme.typography.headlineSmall)
        Text(
            body,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun StatusRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(14.dp),
        verticalAlignment = Alignment.Top,
    ) {
        Text(
            label,
            modifier = Modifier.weight(0.40f),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            style = MaterialTheme.typography.bodySmall,
        )
        Text(
            value,
            modifier = Modifier.weight(0.60f),
            textAlign = TextAlign.End,
            style = MaterialTheme.typography.labelLarge,
        )
    }
}

@Composable
private fun ImageMark(size: androidx.compose.ui.unit.Dp) {
    androidx.compose.foundation.Image(
        painter = painterResource(R.drawable.luxisoft_brand_mark),
        contentDescription = stringResource(R.string.content_luxisoft_mark),
        modifier = Modifier
            .size(size)
            .clip(RoundedCornerShape(size * 0.28f)),
    )
}

private fun formatExpiry(value: Instant): String = value
    .atZone(ZoneId.systemDefault())
    .format(DateTimeFormatter.ofPattern("MMM d, HH:mm"))
