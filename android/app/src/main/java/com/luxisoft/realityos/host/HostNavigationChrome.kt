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
import androidx.compose.foundation.layout.heightIn
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
import androidx.compose.material.icons.filled.CloudUpload
import androidx.compose.material.icons.filled.FolderCopy
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.PersonAdd
import androidx.compose.material.icons.filled.Storage
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
import com.adamglin.phosphoricons.fill.UserCircle
import com.adamglin.phosphoricons.regular.Eye
import com.adamglin.phosphoricons.regular.Eyeglasses
import com.adamglin.phosphoricons.regular.ImagesSquare
import com.adamglin.phosphoricons.regular.SlidersHorizontal
import com.adamglin.phosphoricons.regular.UserCircle
import com.luxisoft.realityos.*
import com.luxisoft.realityos.GalleryFilterButton
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
internal fun GalleryActions(galleryBar: GalleryTopBarState) {
    Row(
        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).padding(horizontal = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = androidx.compose.foundation.layout.Arrangement.End
    ) {
        IconButton(onClick = galleryBar.onCreate, modifier = Modifier.testTag("work-create-group")) {
            Icon(Icons.Default.Add, localizedText(R.string.ui_create_group))
        }
        var workspaceMenu by remember { mutableStateOf(false) }
        Box(Modifier.weight(1f)) {
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
                        modifier = Modifier.weight(1f, fill = false).widthIn(max = 110.dp)
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
        GalleryFilterButton(galleryBar)
        IconButton(onClick = galleryBar.onPublish, enabled = !galleryBar.loading && galleryBar.publishEnabled, modifier = Modifier.testTag("work-publish")) {
            Icon(Icons.Default.CloudUpload, localizedText(R.string.ui_publish))
        }
        var more by remember { mutableStateOf(false) }
        Box {
            IconButton(onClick = { more = true }) { Icon(Icons.Default.MoreVert, localizedText(R.string.ui_manage)) }
            DropdownMenu(more, { more = false }) {
                DropdownMenuItem(text = { Text(localizedText(R.string.ui_history)) }, leadingIcon = {
                    Icon(Icons.Default.History, contentDescription = null)
                }, enabled = galleryBar.selectedId != null, modifier = Modifier.testTag("work-history"), onClick = {
                    more = false
                    galleryBar.onRecords()
                })
                DropdownMenuItem(text = { Text(localizedText(R.string.import_existing_publications)) }, leadingIcon = {
                    Icon(Icons.Default.FolderCopy, contentDescription = null)
                }, enabled = galleryBar.selectedId != null, onClick = {
                    more = false
                    galleryBar.onImport()
                })
                if (galleryBar.showInvite) {
                    DropdownMenuItem(text = { Text(localizedText(R.string.ui_invite_person)) }, leadingIcon = {
                        Icon(Icons.Default.PersonAdd, contentDescription = null)
                    }, modifier = Modifier.testTag("work-invite-person"), onClick = {
                        more = false
                        galleryBar.onInvite()
                    })
                }
                if (galleryBar.showAdmin) {
                    DropdownMenuItem(text = { Text(localizedText(R.string.ui_manage)) }, leadingIcon = {
                        Icon(Icons.Default.AdminPanelSettings, contentDescription = null)
                    }, onClick = {
                        more = false
                        galleryBar.onAdmin()
                    })
                }
            }
        }
    }
}

@Composable
internal fun MetaViewHeader(
    title: String,
    metaSection: MetaSection,
    onSelectMeta: (MetaSection) -> Unit,
    onOpenMetaControls: () -> Unit
) {
    Row(
        Modifier.fillMaxWidth().padding(start = 14.dp, end = 4.dp).testTag("meta-view-header"),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(title, Modifier.weight(1f).padding(vertical = 7.dp), style = MaterialTheme.typography.labelMedium)
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

@Composable
internal fun RealityDrawer(
    experienceStore: RealityExperienceStore,
    onAbout: () -> Unit,
    onConnections: () -> Unit = {},
    connectionsEnabled: Boolean = !com.luxisoft.realityos.BuildConfig.LOCAL_DEVELOPMENT,
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
            if (connectionsEnabled) {
                NavigationDrawerItem(
                    label = { Text(localizedText(R.string.storage_title)) },
                    icon = { Icon(Icons.Filled.Storage, null, Modifier.size(24.dp).testTag("drawer-connections-icon")) },
                    selected = false,
                    onClick = onConnections,
                    colors = flatDrawerItemColors(),
                    modifier = Modifier.fillMaxWidth().testTag("drawer-connections")
                )
            }
            NavigationDrawerItem(
                label = { Text(stringResource(R.string.nav_about)) },
                icon = { Icon(Icons.Outlined.Memory, null, Modifier.size(24.dp).testTag("drawer-about-icon")) },
                selected = false,
                onClick = onAbout,
                colors = flatDrawerItemColors(),
                modifier = Modifier.fillMaxWidth().testTag("drawer-about")
            )
            Spacer(Modifier.weight(1f))
            DrawerLanguageSelector(experienceStore)
            HorizontalDivider(color = MaterialTheme.colorScheme.secondaryContainer)
            Spacer(Modifier.height(8.dp))
            NavigationDrawerItem(
                label = { Text(localizedText(R.string.ui_sign_out)) },
                icon = { Icon(Icons.Filled.Logout, null, Modifier.size(24.dp).testTag("drawer-logout-icon")) },
                selected = false,
                onClick = onLogout,
                colors = flatDrawerItemColors(),
                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp).testTag("drawer-logout")
            )
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
        NoticeEffect(if (saveError) stringResource(R.string.language_save_failed) else "", { saveError = false })
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
