package com.luxisoft.realityos.host

import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.AdminPanelSettings
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.PersonAdd
import androidx.compose.material.icons.outlined.Language
import androidx.compose.material.icons.outlined.Memory
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.NavigationDrawerItemDefaults
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.composed
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.LocalViewConfiguration
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.adamglin.PhosphorIcons
import com.adamglin.phosphoricons.Fill
import com.adamglin.phosphoricons.Regular
import com.adamglin.phosphoricons.fill.Eye
import com.adamglin.phosphoricons.fill.Eyeglasses
import com.adamglin.phosphoricons.fill.ImagesSquare
import com.adamglin.phosphoricons.fill.SlidersHorizontal
import com.adamglin.phosphoricons.fill.UserCircle
import com.adamglin.phosphoricons.regular.Eye
import com.adamglin.phosphoricons.regular.Eyeglasses
import com.adamglin.phosphoricons.regular.ImagesSquare
import com.adamglin.phosphoricons.regular.SlidersHorizontal
import com.adamglin.phosphoricons.regular.UserCircle
import com.luxisoft.realityos.*
import com.luxisoft.realityos.localizedText
import kotlinx.coroutines.launch

/**
 * Opens the host drawer from an edge swipe on pages where the pager would
 * otherwise claim every horizontal drag. Only drags starting on the edge
 * and travelling toward the content are consumed; everything else reaches
 * the pager untouched.
 */
internal fun Modifier.drawerEdgeOpen(
    enabled: Boolean,
    edgeWidth: Dp = 32.dp,
    onOpen: () -> Unit
): Modifier = composed {
    val edgePx = with(LocalDensity.current) { edgeWidth.toPx() }
    val slop = LocalViewConfiguration.current.touchSlop
    val isRtl = LocalLayoutDirection.current == LayoutDirection.Rtl
    val currentOnOpen by rememberUpdatedState(onOpen)
    pointerInput(enabled, edgePx) {
        awaitEachGesture {
            val down = awaitFirstDown(requireUnconsumed = false)
            if (!enabled || !DrawerEdgePolicy.atEdge(down.position.x, size.width.toFloat(), edgePx, isRtl)) {
                do {
                    val event = awaitPointerEvent()
                } while (event.changes.any { it.pressed })
                return@awaitEachGesture
            }
            var opened = false
            do {
                val event = awaitPointerEvent()
                for (change in event.changes) {
                    if (!change.pressed) continue
                    if (!opened && DrawerEdgePolicy.shouldOpen(change.position.x - down.position.x, slop, isRtl)) {
                        opened = true
                        change.consume()
                        currentOnOpen()
                    } else if (opened) {
                        change.consume()
                    }
                }
            } while (event.changes.any { it.pressed })
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun HostTopBar(
    selected: HostDestination,
    audience: String,
    metaSection: MetaSection,
    galleryBar: GalleryTopBarState,
    onSelectMeta: (MetaSection) -> Unit,
    onOpenMetaControls: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth().height(48.dp).padding(horizontal = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = androidx.compose.foundation.layout.Arrangement.End
    ) {
        if (selected == HostDestination.GALLERY && audience == "work" && (galleryBar.loading || galleryBar.options.isNotEmpty())) {
            var workspaceMenu by remember { mutableStateOf(false) }
            Box {
                TextButton(
                    onClick = { workspaceMenu = true },
                    contentPadding = PaddingValues(horizontal = 8.dp)
                ) {
                    if (galleryBar.loading) {
                        SkeletonBlock(Modifier.width(100.dp).height(16.dp))
                    } else {
                        Text(
                            GalleryWorkspaceLabels.selectedName(galleryBar.options, galleryBar.selectedId, localizedText(R.string.ui_all_workspaces)),
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            modifier = Modifier.widthIn(max = 110.dp)
                        )
                    }
                    Icon(Icons.Filled.ArrowDropDown, contentDescription = localizedText(R.string.ui_select_workspace))
                }
                DropdownMenu(expanded = workspaceMenu, onDismissRequest = { workspaceMenu = false }) {
                    if (galleryBar.loading) {
                        SkeletonList(Modifier.width(220.dp).padding(16.dp), rows = 3)
                    } else {
                        DropdownMenuItem(
                            text = { Text(localizedText(R.string.ui_all_workspaces)) },
                            onClick = {
                                galleryBar.onSelect(null)
                                workspaceMenu = false
                            },
                            leadingIcon = if (galleryBar.selectedId == null) {
                                { Icon(Icons.Filled.Check, contentDescription = null) }
                            } else {
                                null
                            }
                        )
                        galleryBar.options.forEach { option ->
                            DropdownMenuItem(
                                text = { Text(option.name) },
                                onClick = {
                                    galleryBar.onSelect(option.id)
                                    workspaceMenu = false
                                },
                                leadingIcon = if (galleryBar.selectedId == option.id) {
                                    { Icon(Icons.Filled.Check, contentDescription = null) }
                                } else {
                                    null
                                }
                            )
                        }
                    }
                }
            }
            IconButton(onClick = galleryBar.onPublish, enabled = !galleryBar.loading && galleryBar.publishEnabled) {
                Icon(Icons.Filled.Add, contentDescription = localizedText(R.string.ui_publish))
            }
            if (galleryBar.showInvite) {
                IconButton(onClick = galleryBar.onInvite) {
                    Icon(Icons.Filled.PersonAdd, contentDescription = localizedText(R.string.ui_invite))
                }
            }
            if (galleryBar.showAdmin) {
                IconButton(onClick = galleryBar.onAdmin) {
                    Icon(Icons.Filled.AdminPanelSettings, contentDescription = localizedText(R.string.ui_manage))
                }
            }
        }
        if (selected == HostDestination.META_DISPLAY) {
            IconButton(onClick = { onSelectMeta(MetaSection.PREVIEW) }) {
                Icon(
                    imageVector = if (metaSection == MetaSection.PREVIEW) PhosphorIcons.Fill.Eye else PhosphorIcons.Regular.Eye,
                    contentDescription = localizedText(R.string.ui_preview),
                    tint = if (metaSection == MetaSection.PREVIEW) RealityIconSelected else RealityIconDefault
                )
            }
            IconButton(onClick = { onSelectMeta(MetaSection.GLASSES) }) {
                Icon(
                    imageVector = if (metaSection == MetaSection.GLASSES) PhosphorIcons.Fill.Eyeglasses else PhosphorIcons.Regular.Eyeglasses,
                    contentDescription = localizedText(R.string.ui_glasses),
                    tint = if (metaSection == MetaSection.GLASSES) RealityIconSelected else RealityIconDefault
                )
            }
            IconButton(
                onClick = onOpenMetaControls,
                modifier = Modifier.testTag("host-preview-controls-button")
            ) {
                Icon(
                    imageVector = PhosphorIcons.Regular.SlidersHorizontal,
                    contentDescription = localizedText(R.string.ui_controls),
                    tint = RealityIconDefault
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun SocialBottomBar(
    selected: HostDestination,
    profilePictureUrl: String?,
    onProfile: () -> Unit,
    onWork: () -> Unit,
    onSearch: () -> Unit
) {
    CompactBottomBar {
        ProfileBottomBarItem(
            selected = selected == HostDestination.PROFILE,
            onClick = onProfile,
            profilePictureUrl = profilePictureUrl
        )
        BottomBarItem(
            selected = selected == HostDestination.GALLERY,
            onClick = onWork,
            selectedIcon = PhosphorIcons.Fill.ImagesSquare,
            unselectedIcon = PhosphorIcons.Regular.ImagesSquare,
            contentDescription = localizedText(R.string.ui_work)
        )
        BottomBarItem(
            selected = false,
            onClick = onSearch,
            contentDescription = localizedText(R.string.ui_search),
            brandIcon = painterResource(R.drawable.ic_muse)
        )
    }
}

@Composable
internal fun RowScope.ProfileBottomBarItem(
    selected: Boolean,
    profilePictureUrl: String?,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .weight(1f)
            .fillMaxHeight()
            .selectable(selected = selected, onClick = onClick, role = Role.Tab),
        contentAlignment = Alignment.Center
    ) {
        if (profilePictureUrl != null) {
            val context = LocalContext.current
            coil.compose.SubcomposeAsyncImage(
                model = profileImageRequest(context, profilePictureUrl),
                contentDescription = localizedText(R.string.ui_profile),
                contentScale = ContentScale.Crop,
                loading = { SkeletonBlock(Modifier.fillMaxSize().clip(CircleShape)) },
                error = { ProfileAvatarFallback(selected) },
                modifier = Modifier
                    .size(30.dp)
                    .clip(CircleShape)
                    .then(
                        if (selected) {
                            Modifier.border(1.5.dp, RealityIconSelected, CircleShape)
                        } else {
                            Modifier
                        }
                    )
            )
        } else {
            ProfileAvatarFallback(selected)
        }
    }
}

@Composable
internal fun ProfileAvatarFallback(selected: Boolean) {
    Icon(
        imageVector = if (selected) PhosphorIcons.Fill.UserCircle else PhosphorIcons.Regular.UserCircle,
        contentDescription = localizedText(R.string.ui_profile),
        modifier = Modifier.size(30.dp),
        tint = if (selected) RealityIconSelected else RealityIconDefault
    )
}

@Composable
internal fun MetaDisplayBottomBar(
    selected: MetaSection,
    onSelect: (MetaSection) -> Unit,
    onControls: () -> Unit
) {
    CompactBottomBar {
        BottomBarItem(
            selected = selected == MetaSection.PREVIEW,
            onClick = { onSelect(MetaSection.PREVIEW) },
            selectedIcon = PhosphorIcons.Fill.Eye,
            unselectedIcon = PhosphorIcons.Regular.Eye,
            contentDescription = localizedText(R.string.ui_preview)
        )
        BottomBarItem(
            selected = selected == MetaSection.GLASSES,
            onClick = { onSelect(MetaSection.GLASSES) },
            selectedIcon = PhosphorIcons.Fill.Eyeglasses,
            unselectedIcon = PhosphorIcons.Regular.Eyeglasses,
            contentDescription = localizedText(R.string.ui_glasses)
        )
        BottomBarItem(
            selected = false,
            onClick = onControls,
            selectedIcon = PhosphorIcons.Fill.SlidersHorizontal,
            unselectedIcon = PhosphorIcons.Regular.SlidersHorizontal,
            contentDescription = localizedText(R.string.ui_controls),
            modifier = Modifier.testTag("host-preview-controls-button")
        )
    }
}

@Composable
internal fun CompactBottomBar(content: @Composable RowScope.() -> Unit) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        contentColor = MaterialTheme.colorScheme.onSurface,
        tonalElevation = 0.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .navigationBarsPadding()
                .height(54.dp)
                .padding(3.dp),
            content = content
        )
    }
}

@Composable
internal fun RowScope.BottomBarItem(
    selectedIcon: androidx.compose.ui.graphics.vector.ImageVector? = null,
    unselectedIcon: androidx.compose.ui.graphics.vector.ImageVector? = null,
    contentDescription: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    brandIcon: Painter? = null
) {
    Box(
        modifier = modifier
            .weight(1f)
            .fillMaxHeight()
            .selectable(selected = selected, onClick = onClick, role = Role.Tab),
        contentAlignment = Alignment.Center
    ) {
        if (brandIcon != null) {
            Icon(
                painter = brandIcon,
                contentDescription = contentDescription,
                modifier = Modifier.size(30.dp),
                tint = if (selected) RealityIconSelected else RealityIconDefault
            )
        } else {
            val vector = if (selected) selectedIcon else unselectedIcon
            if (vector != null) {
                Icon(
                    imageVector = vector,
                    contentDescription = contentDescription,
                    modifier = Modifier.size(30.dp),
                    tint = if (selected) RealityIconSelected else RealityIconDefault
                )
            }
        }
    }
}

@Composable
internal fun RealityDrawer(
    experienceStore: RealityExperienceStore,
    onAbout: () -> Unit,
    onLogout: () -> Unit
) {
    ModalDrawerSheet(
        modifier = Modifier.widthIn(max = 344.dp),
        drawerContainerColor = MaterialTheme.colorScheme.surface,
        drawerContentColor = MaterialTheme.colorScheme.onSurface
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 14.dp)
        ) {
            Row(
                modifier = Modifier.padding(start = 10.dp, top = 30.dp, bottom = 22.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                ImageMark(size = 46.dp)
                Spacer(Modifier.width(12.dp))
                Column {
                    Text("RealityOS", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text(
                        stringResource(R.string.drawer_tagline),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            HorizontalDivider(color = MaterialTheme.colorScheme.secondaryContainer)
            Spacer(Modifier.height(8.dp))
            DrawerLanguageSelector(experienceStore)
            NavigationDrawerItem(
                label = { Text(stringResource(R.string.nav_about)) },
                icon = { Icon(Icons.Outlined.Memory, null) },
                selected = false,
                onClick = onAbout,
                colors = flatDrawerItemColors(),
                modifier = Modifier.padding(NavigationDrawerItemDefaults.ItemPadding)
            )
            Spacer(Modifier.weight(1f))
            HorizontalDivider(color = MaterialTheme.colorScheme.secondaryContainer)
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(NavigationDrawerItemDefaults.ItemPadding)
                    .padding(bottom = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                NavigationDrawerItem(
                    label = { Text(localizedText(R.string.ui_sign_out), style = MaterialTheme.typography.bodySmall) },
                    icon = { Icon(Icons.Filled.Logout, contentDescription = null) },
                    selected = false,
                    onClick = onLogout,
                    colors = flatDrawerItemColors(),
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun DrawerLanguageSelector(
    experienceStore: RealityExperienceStore,
    saveLanguage: suspend (RealityLanguage) -> Unit = { experienceStore.saveAccountLanguage(it) }
) {
    val selected by experienceStore.language.collectAsState()
    val scope = rememberCoroutineScope()
    var saving by remember { mutableStateOf(false) }
    var saveError by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)) {
        Text(stringResource(R.string.nav_language), style = MaterialTheme.typography.labelMedium)
        androidx.compose.material3.SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth().testTag("drawer-language")) {
            RealityLanguage.entries.forEachIndexed { index, language ->
                SegmentedButton(
                    selected = selected == language,
                    enabled = !saving,
                    shape = androidx.compose.material3.SegmentedButtonDefaults.itemShape(index, RealityLanguage.entries.size),
                    onClick = {
                        if (!saving && selected != language) {
                            scope.launch {
                                saving = true
                                saveError = false
                                try {
                                    saveLanguage(language)
                                } catch (failure: kotlinx.coroutines.CancellationException) {
                                    throw failure
                                } catch (_: Exception) {
                                    saveError = true
                                } finally {
                                    saving = false
                                }
                            }
                        }
                    }
                ) { Text(language.languageTag.uppercase()) }
            }
        }
        if (saveError) Text(stringResource(R.string.language_save_failed), color = MaterialTheme.colorScheme.error, modifier = Modifier.testTag("language-save-error"))
    }
}

@Composable
internal fun flatDrawerItemColors() = NavigationDrawerItemDefaults.colors(
    selectedContainerColor = MaterialTheme.colorScheme.surface,
    unselectedContainerColor = MaterialTheme.colorScheme.surface,
    selectedIconColor = RealityIconSelected,
    selectedTextColor = MaterialTheme.colorScheme.primary,
    unselectedIconColor = RealityIconDefault,
    unselectedTextColor = MaterialTheme.colorScheme.onSurface
)
