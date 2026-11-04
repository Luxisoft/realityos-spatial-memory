package com.luxisoft.realityos

import androidx.activity.compose.BackHandler
import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.Chat
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

private data class ExplorePage(
    @DrawableRes val art: Int,
    @StringRes val category: Int,
    @StringRes val title: Int,
    @StringRes val body: Int,
    @StringRes val example: Int,
    val icon: ImageVector
)

private val explorePages = listOf(
    ExplorePage(R.drawable.intro_overview, R.string.explore_overview_label, R.string.explore_overview_title, R.string.explore_overview_body, R.string.explore_overview_example, Icons.Outlined.Hub),
    ExplorePage(R.drawable.intro_case, R.string.explore_case_label, R.string.explore_case_title, R.string.explore_case_body, R.string.explore_case_example, Icons.Outlined.FolderOpen),
    ExplorePage(R.drawable.intro_social, R.string.explore_social_label, R.string.explore_social_title, R.string.explore_social_body, R.string.explore_social_example, Icons.Outlined.PeopleOutline),
    ExplorePage(R.drawable.intro_devices, R.string.explore_devices_label, R.string.explore_devices_title, R.string.explore_devices_body, R.string.explore_devices_example, Icons.Outlined.PhonelinkRing)
)

@Composable
fun RealityWelcome(replay: Boolean = false, onFinish: () -> Unit) {
    val pager = rememberPagerState { explorePages.size }
    val scope = rememberCoroutineScope()
    val last = pager.currentPage == explorePages.lastIndex
    val previous = {
        if (!pager.isScrollInProgress) scope.launch { pager.animateScrollToPage(pager.currentPage - 1) }
        Unit
    }
    BackHandler {
        if (pager.currentPage > 0) previous() else onFinish()
    }
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().safeDrawingPadding(), horizontalAlignment = Alignment.CenterHorizontally) {
            Column(Modifier.widthIn(max = 528.dp).fillMaxSize()) {
                EntryBrandHeader {
                    TextButton(onClick = onFinish, modifier = Modifier.testTag("explore-exit")) {
                        Text(stringResource(if (replay) R.string.intro_close else R.string.intro_skip))
                    }
                }
                HorizontalPager(state = pager, modifier = Modifier.weight(1f).testTag("explore-pager"), verticalAlignment = Alignment.Top) { index ->
                    ExplorePageContent(explorePages[index], index)
                }
                Column(Modifier.padding(horizontal = 24.dp).padding(top = 12.dp, bottom = 16.dp)) {
                    val pageLabel = stringResource(R.string.explore_page_position, pager.currentPage + 1, explorePages.size)
                    Row(
                        Modifier.fillMaxWidth().clearAndSetSemantics {
                            contentDescription = pageLabel
                            liveRegion = LiveRegionMode.Polite
                        },
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            explorePages.indices.forEach { index ->
                                Box(
                                    Modifier.height(5.dp).width(if (index == pager.currentPage) 24.dp else 6.dp)
                                        .background(if (index == pager.currentPage) AccountBlue else MaterialTheme.colorScheme.outlineVariant, CircleShape)
                                )
                            }
                        }
                        Text("${pager.currentPage + 1} / ${explorePages.size}", style = MaterialTheme.typography.bodySmall, color = AccountMuted)
                    }
                    Spacer(Modifier.height(14.dp))
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        OutlinedIconButton(
                            onClick = previous,
                            enabled = pager.currentPage > 0 && !pager.isScrollInProgress,
                            shape = MaterialTheme.shapes.medium,
                            modifier = Modifier.size(56.dp).testTag("explore-previous")
                        ) {
                            Icon(Icons.AutoMirrored.Outlined.ArrowBack, stringResource(R.string.explore_previous))
                        }
                        EntryPrimary(
                            stringResource(
                                if (last) {
                                    if (replay) R.string.explore_return else R.string.explore_begin
                                } else {
                                    R.string.explore_next
                                }
                            ),
                            modifier = Modifier.weight(1f).testTag("explore-next"),
                            enabled = !pager.isScrollInProgress
                        ) {
                            if (last) onFinish() else scope.launch { pager.animateScrollToPage(pager.currentPage + 1) }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ExplorePageContent(page: ExplorePage, index: Int) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 24.dp).padding(top = 8.dp, bottom = 12.dp).testTag("explore-page-$index")) {
        EntryScene(page.art)
        Spacer(Modifier.height(24.dp))
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Icon(page.icon, null, Modifier.size(18.dp), tint = AccountBlue)
            Text(stringResource(page.category), style = MaterialTheme.typography.labelMedium, color = AccountBlue)
        }
        Spacer(Modifier.height(10.dp))
        Text(
            stringResource(page.title),
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.testTag("explore-title-$index").semantics { heading() }
        )
        Spacer(Modifier.height(12.dp))
        Text(stringResource(page.body), style = MaterialTheme.typography.bodyMedium, color = AccountMuted)
        Spacer(Modifier.height(20.dp))
        Surface(color = AccountFieldSurface, shape = MaterialTheme.shapes.medium) {
            Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Icon(Icons.AutoMirrored.Outlined.Chat, null, Modifier.size(20.dp), tint = AccountBlue)
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(stringResource(R.string.explore_example), style = MaterialTheme.typography.labelMedium, color = AccountMuted)
                    Text(stringResource(page.example), style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
        if (index == explorePages.lastIndex) {
            Spacer(Modifier.height(20.dp))
            ExploreCredits()
        }
    }
}

@Composable
private fun ExploreCredits() {
    val uriHandler = LocalUriHandler.current
    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
    Column(Modifier.padding(top = 16.dp).testTag("explore-credits"), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(stringResource(R.string.about_developed_by), style = MaterialTheme.typography.labelMedium, color = AccountMuted)
        Text(stringResource(R.string.about_creator), style = MaterialTheme.typography.titleMedium)
        Text("Luximus · Meta AI Developer Hackathon 2026", style = MaterialTheme.typography.bodySmall, color = AccountMuted)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TextButton(onClick = { uriHandler.openUri("https://www.linkedin.com/in/jose-wilson-marin-giraldo-b1a881304/") }) {
                Text(stringResource(R.string.intro_contact_linkedin))
                Spacer(Modifier.width(6.dp))
                Icon(Icons.Outlined.OpenInNew, null, Modifier.size(16.dp))
            }
            TextButton(onClick = { uriHandler.openUri("https://github.com/Luxisoft/realityos-spatial-memory") }) {
                Text(stringResource(R.string.intro_contact_github))
                Spacer(Modifier.width(6.dp))
                Icon(Icons.Outlined.OpenInNew, null, Modifier.size(16.dp))
            }
        }
    }
}
