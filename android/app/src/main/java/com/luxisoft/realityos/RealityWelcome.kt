package com.luxisoft.realityos

import androidx.annotation.StringRes
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

private data class WelcomePage(
    @param:StringRes val kicker: Int,
    @param:StringRes val title: Int,
    @param:StringRes val body: Int,
)

/** A short product prelude, intentionally informational rather than a splash delay. */
@Composable
fun RealityWelcome(replay: Boolean, onFinish: () -> Unit) {
    val pages = listOf(
        WelcomePage(R.string.intro_page_home_kicker, R.string.intro_page_home_title, R.string.intro_page_home_body),
        WelcomePage(R.string.intro_page_work_kicker, R.string.intro_page_work_title, R.string.intro_page_work_body),
        WelcomePage(R.string.intro_page_memory_kicker, R.string.intro_page_memory_title, R.string.intro_page_memory_body),
        WelcomePage(R.string.intro_page_shared_kicker, R.string.intro_page_shared_title, R.string.intro_page_shared_body),
        WelcomePage(R.string.intro_page_meta_kicker, R.string.intro_page_meta_title, R.string.intro_page_meta_body),
        WelcomePage(R.string.intro_page_future_kicker, R.string.intro_page_future_title, R.string.intro_page_future_body),
    )
    val pagerState = rememberPagerState(pageCount = { pages.size })
    val scope = rememberCoroutineScope()
    val isLast = pagerState.currentPage == pages.lastIndex

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background,
        contentColor = MaterialTheme.colorScheme.onBackground,
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .safeDrawingPadding()
                .padding(horizontal = 24.dp, vertical = 14.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Image(
                        painter = painterResource(R.drawable.luxisoft_brand_mark),
                        contentDescription = stringResource(R.string.content_luxisoft_mark),
                        modifier = Modifier
                            .size(34.dp)
                            .clip(RoundedCornerShape(10.dp)),
                    )
                    Spacer(Modifier.width(9.dp))
                    Column(verticalArrangement = Arrangement.spacedBy(0.dp)) {
                        Text("RealityOS", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Text(
                            stringResource(R.string.about_developed_by),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                Spacer(Modifier.weight(1f))
                TextButton(onClick = onFinish) {
                    Text(stringResource(if (replay) R.string.intro_close else R.string.intro_skip))
                }
            }
            HorizontalPager(
                state = pagerState,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                verticalAlignment = Alignment.CenterVertically,
            ) { page ->
                WelcomePageContent(
                    page = pages[page],
                    pageIndex = page,
                    finalPage = page == pages.lastIndex,
                )
            }
            WelcomePagerIndicator(
                selected = pagerState.currentPage,
                count = pages.size,
            )
            Spacer(Modifier.height(18.dp))
            Button(
                onClick = {
                    if (isLast) onFinish()
                    else scope.launch { pagerState.animateScrollToPage(pagerState.currentPage + 1) }
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(if (isLast) R.string.intro_enter else R.string.intro_continue))
            }
        }
    }
}

@Composable
private fun WelcomePageContent(page: WelcomePage, pageIndex: Int, finalPage: Boolean) {
    val uriHandler = LocalUriHandler.current
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .widthIn(max = 560.dp)
            .padding(vertical = 20.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        MemoryTrace(pageIndex = pageIndex)
        Spacer(Modifier.height(30.dp))
        AnimatedContent(
            targetState = pageIndex,
            transitionSpec = {
                fadeIn(animationSpec = tween(320)) togetherWith fadeOut(animationSpec = tween(140))
            },
            label = "welcome-copy",
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    stringResource(page.kicker),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(
                    stringResource(page.title),
                    style = MaterialTheme.typography.displaySmall,
                )
                Text(
                    stringResource(page.body),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                if (finalPage) {
                    Spacer(Modifier.height(8.dp))
                    CreditPlate(
                        onLinkedIn = {
                            uriHandler.openUri("https://www.linkedin.com/in/jose-wilson-marin-giraldo-b1a881304/")
                        },
                        onGitHub = {
                            uriHandler.openUri("https://github.com/Luxisoft/realityos-spatial-memory")
                        },
                    )
                }
            }
        }
    }
}

/** The visual signature: a luminous trail joining separate human observations. */
@Composable
private fun MemoryTrace(pageIndex: Int) {
    val emphasis by animateFloatAsState(
        targetValue = (pageIndex + 1) / 6f,
        animationSpec = tween(450),
        label = "memory-trace-progress",
    )
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(220.dp)
            .clip(RoundedCornerShape(30.dp))
            .background(MaterialTheme.colorScheme.surface),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val width = size.width
            val height = size.height
            val mint = Color(0xFF62E7BE)
            val muted = Color(0xFF7E97AD)
            val track = Path().apply {
                moveTo(width * 0.08f, height * 0.68f)
                cubicTo(width * 0.23f, height * 0.16f, width * 0.40f, height * 0.88f, width * 0.58f, height * 0.49f)
                cubicTo(width * 0.71f, height * 0.20f, width * 0.83f, height * 0.62f, width * 0.93f, height * 0.31f)
            }
            drawPath(track, muted.copy(alpha = 0.25f), style = Stroke(width = 2.dp.toPx()))
            drawPath(track, mint.copy(alpha = 0.32f + emphasis * 0.45f), style = Stroke(width = 4.dp.toPx()))
            listOf(
                Offset(width * 0.10f, height * 0.63f),
                Offset(width * 0.30f, height * 0.43f),
                Offset(width * 0.55f, height * 0.52f),
                Offset(width * 0.78f, height * 0.39f),
                Offset(width * 0.91f, height * 0.32f),
            ).forEachIndexed { index, center ->
                val selected = index <= pageIndex.coerceAtMost(4)
                drawCircle(
                    color = if (selected) mint.copy(alpha = 0.20f) else muted.copy(alpha = 0.12f),
                    radius = if (selected) 22.dp.toPx() else 14.dp.toPx(),
                    center = center,
                )
                drawCircle(
                    color = if (selected) mint else muted.copy(alpha = 0.62f),
                    radius = if (selected) 7.dp.toPx() else 4.dp.toPx(),
                    center = center,
                )
            }
        }
        Text(
            stringResource(R.string.intro_trace_label),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.72f),
        )
    }
}

@Composable
private fun WelcomePagerIndicator(selected: Int, count: Int) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.Center,
    ) {
        repeat(count) { index ->
            Box(
                modifier = Modifier
                    .padding(horizontal = 4.dp)
                    .height(6.dp)
                    .width(if (index == selected) 26.dp else 7.dp)
                    .clip(CircleShape)
                    .background(
                        if (index == selected) MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.outlineVariant,
                    ),
            )
        }
    }
}

@Composable
private fun CreditPlate(onLinkedIn: () -> Unit, onGitHub: () -> Unit) {
    Card(
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(5.dp),
        ) {
            Text(stringResource(R.string.about_developed_by), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
            Text(stringResource(R.string.about_creator), style = MaterialTheme.typography.titleMedium)
            Text(stringResource(R.string.about_location), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("Meta AI Developer Hackathon 2026 · Luximus", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                TextButton(onClick = onLinkedIn) { Text(stringResource(R.string.intro_contact_linkedin)) }
                TextButton(onClick = onGitHub) { Text(stringResource(R.string.intro_contact_github)) }
            }
        }
    }
}

@Composable
fun AboutDestination(onReplayWelcome: () -> Unit) {
    val uriHandler = LocalUriHandler.current
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    stringResource(R.string.about_eyebrow),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(stringResource(R.string.about_title), style = MaterialTheme.typography.headlineMedium)
            }
        }
        item { AboutSection(R.string.about_problem_title, R.string.about_problem_body) }
        item { AboutSection(R.string.about_solution_title, R.string.about_solution_body, featured = true) }
        item { AboutSection(R.string.about_difference_title, R.string.about_difference_body) }
        item { AboutSection(R.string.about_meta_title, R.string.about_meta_body) }
        item { AboutSection(R.string.about_privacy_title, R.string.about_privacy_body) }
        item {
            OutlinedButton(onClick = onReplayWelcome, modifier = Modifier.fillMaxWidth()) {
                Text(stringResource(R.string.about_replay))
            }
        }
        item {
            Card(shape = MaterialTheme.shapes.large) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(stringResource(R.string.about_team_title), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                    Text(stringResource(R.string.about_developed_by), style = MaterialTheme.typography.titleLarge)
                    Text(stringResource(R.string.about_creator), style = MaterialTheme.typography.bodyLarge)
                    Text("Luximus · ${stringResource(R.string.about_location)}", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    HorizontalDivider(modifier = Modifier.padding(vertical = 5.dp), color = MaterialTheme.colorScheme.outlineVariant)
                    LinkButton(stringResource(R.string.about_linkedin)) {
                        uriHandler.openUri("https://www.linkedin.com/in/jose-wilson-marin-giraldo-b1a881304/")
                    }
                    LinkButton(stringResource(R.string.about_email)) {
                        uriHandler.openUri("mailto:jmarin@luxisoft.com")
                    }
                    LinkButton(stringResource(R.string.about_github)) {
                        uriHandler.openUri("https://github.com/Luxisoft/realityos-spatial-memory")
                    }
                }
            }
        }
    }
}

@Composable
private fun AboutSection(@StringRes title: Int, @StringRes body: Int, featured: Boolean = false) {
    Card(
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = if (featured) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface,
            contentColor = if (featured) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface,
        ),
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(stringResource(title), style = MaterialTheme.typography.titleLarge)
            Text(
                stringResource(body),
                style = MaterialTheme.typography.bodyMedium,
                color = if (featured) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun LinkButton(label: String, onClick: () -> Unit) {
    TextButton(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Text(label, modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
        Text("↗", style = MaterialTheme.typography.titleMedium)
    }
}
