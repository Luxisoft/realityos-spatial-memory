package com.luxisoft.realityos.host

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.luxisoft.realityos.*
import com.luxisoft.realityos.R
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import kotlinx.coroutines.launch

@Composable
internal fun PreviewDestination(
    state: RealityUiState,
    viewModel: RealityViewModel
) {
    if (BuildConfig.DEBUG) {
        DeveloperPreviewStage(
            viewModel = viewModel,
            enabled = !state.wearable.sessionActive,
            modifier = Modifier.fillMaxSize()
        )
    } else {
        LiveDisplayStage(state = state, modifier = Modifier.fillMaxSize())
    }
}

@Composable
internal fun LiveDisplayStage(
    state: RealityUiState,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .background(Color(0xFF070B12))
            .background(
                Brush.radialGradient(
                    colors = listOf(Color(0x1A62A9F8), Color(0x0C62A9F8), Color.Transparent)
                )
            ),
        contentAlignment = Alignment.Center
    ) {
        MemoryField(active = state.wearable.sessionActive)
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(32.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(
                if (state.wearable.sessionActive) {
                    stringResource(R.string.preview_live_title)
                } else {
                    stringResource(R.string.preview_waiting_title)
                },
                style = MaterialTheme.typography.headlineSmall,
                textAlign = TextAlign.Center
            )
            Text(
                if (state.wearable.sessionActive) {
                    stringResource(R.string.preview_live_body)
                } else {
                    stringResource(R.string.preview_waiting_body)
                },
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )
        }
    }
}

@Composable
internal fun PreviewControlsOverlay(
    visible: Boolean,
    onDismiss: () -> Unit,
    content: @Composable ColumnScope.() -> Unit
) {
    Box(Modifier.fillMaxSize()) {
        AnimatedVisibility(visible = visible, enter = fadeIn(tween(140)), exit = fadeOut(tween(100))) {
            Box(Modifier.fillMaxSize().background(Color.Black.copy(alpha = .52f)).clickable(onClick = onDismiss))
        }
        AnimatedVisibility(
            visible = visible,
            modifier = Modifier.align(Alignment.CenterEnd),
            enter = slideInHorizontally(initialOffsetX = { it }, animationSpec = tween(220)),
            exit = slideOutHorizontally(targetOffsetX = { it }, animationSpec = tween(180))
        ) {
            Surface(
                modifier = Modifier
                    .fillMaxHeight()
                    .fillMaxWidth(.9f)
                    .widthIn(max = 344.dp)
                    .testTag("preview-controls-drawer"),
                color = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.onSurface,
                shape = MaterialTheme.shapes.large
            ) {
                Column(
                    modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(stringResource(R.string.preview_controls_title), style = MaterialTheme.typography.titleLarge)
                            Text(stringResource(R.string.preview_controls_body), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        IconButton(onClick = onDismiss) { Icon(Icons.Outlined.Close, stringResource(R.string.content_close_preview_controls)) }
                    }
                    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                    content()
                }
            }
        }
    }
}

@Composable
internal fun MemoryField(active: Boolean) {
    val trace = if (active) MaterialTheme.colorScheme.tertiary else MaterialTheme.colorScheme.outline
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
internal fun GlassesDestination(
    state: RealityUiState,
    viewModel: RealityViewModel,
    onRegisterWithMeta: () -> Unit,
    onConnectDisplay: () -> Unit,
    onDisconnectDisplay: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        SectionHeading(
            title = stringResource(R.string.glasses_title),
            body = stringResource(R.string.glasses_body)
        )
        Card(shape = MaterialTheme.shapes.large) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Text(stringResource(if (state.wearable.inputRoute == InputRoute.PHONE) R.string.meta_preview_device else R.string.meta_physical_device), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.tertiary)
                StatusRow(
                    stringResource(R.string.glasses_registration),
                    state.wearable.registration.lowercase().replace('_', ' ')
                )
                StatusRow(
                    stringResource(R.string.glasses_device),
                    stringResource(if (state.wearable.deviceAvailable) R.string.glasses_available else R.string.glasses_not_detected)
                )
                StatusRow(
                    stringResource(R.string.glasses_display),
                    stringResource(if (state.wearable.sessionActive) R.string.glasses_active else R.string.glasses_not_connected)
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
        MetaExperiencePanel(state, viewModel)
        Surface(
            color = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
            shape = MaterialTheme.shapes.medium
        ) {
            Text(
                stringResource(R.string.glasses_capture_note),
                modifier = Modifier.padding(16.dp),
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Composable
internal fun LanguageDestination(experienceStore: RealityExperienceStore) {
    val selected by experienceStore.language.collectAsState()
    val scope = rememberCoroutineScope()
    var saving by remember { mutableStateOf(false) }
    var saveError by remember { mutableStateOf(false) }
    fun save(language: RealityLanguage) {
        if (saving) return
        scope.launch {
            saving = true
            saveError = false
            try {
                experienceStore.saveAccountLanguage(language)
            } catch (_: Exception) {
                saveError = true
            } finally {
                saving = false
            }
        }
    }
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        SectionHeading(
            title = stringResource(R.string.language_title),
            body = stringResource(R.string.language_body)
        )
        if (saving) com.luxisoft.realityos.SkeletonLines(rows = 1)
        if (saveError) Text(stringResource(R.string.language_save_failed), color = MaterialTheme.colorScheme.error)
        LanguageOption(
            label = stringResource(R.string.language_english),
            selected = selected == RealityLanguage.ENGLISH,
            onClick = { save(RealityLanguage.ENGLISH) }
        )
        LanguageOption(
            label = stringResource(R.string.language_spanish),
            selected = selected == RealityLanguage.SPANISH,
            onClick = { save(RealityLanguage.SPANISH) }
        )
    }
}

@Composable
internal fun LanguageOption(label: String, selected: Boolean, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = if (selected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface,
            contentColor = if (selected) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface
        ),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(label, modifier = Modifier.weight(1f), style = MaterialTheme.typography.titleLarge)
            if (selected) {
                Text(
                    stringResource(R.string.language_selected),
                    style = MaterialTheme.typography.labelMedium
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
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
internal fun StatusRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(14.dp),
        verticalAlignment = Alignment.Top
    ) {
        Text(
            label,
            modifier = Modifier.weight(0.40f),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            style = MaterialTheme.typography.bodySmall
        )
        Text(
            value,
            modifier = Modifier.weight(0.60f),
            textAlign = TextAlign.End,
            style = MaterialTheme.typography.labelLarge
        )
    }
}

@Composable
internal fun ImageMark(size: androidx.compose.ui.unit.Dp) {
    androidx.compose.foundation.Image(
        painter = painterResource(R.drawable.luxisoft_brand_mark),
        contentDescription = stringResource(R.string.content_luxisoft_mark),
        modifier = Modifier
            .width(size)
            .height(size * 0.56f)
    )
}

internal fun formatExpiry(value: Instant): String = value
    .atZone(ZoneId.systemDefault())
    .format(DateTimeFormatter.ofPattern("MMM d, HH:mm"))
