package com.luxisoft.realityos

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BrokenImage
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp

/** Quiet, non-interactive placeholders. No artificial timer delays actual data. */
@Composable
internal fun SkeletonBlock(modifier: Modifier = Modifier) {
    Box(
        modifier.clip(RoundedCornerShape(8.dp))
            .background(MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f))
            .clearAndSetSemantics { }
    )
}

private fun Modifier.loadingSemantics() = semantics(mergeDescendants = true) {
    contentDescription = localizedText(R.string.ui_loading_content)
    progressBarRangeInfo = ProgressBarRangeInfo.Indeterminate
}

@Composable
internal fun SkeletonLines(modifier: Modifier = Modifier, rows: Int = 3) {
    Column(modifier.fillMaxWidth().loadingSemantics(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        repeat(rows) { index ->
            SkeletonBlock(Modifier.fillMaxWidth(if (index == rows - 1) 0.6f else 1f).height(14.dp))
        }
    }
}

@Composable
internal fun SkeletonList(modifier: Modifier = Modifier, rows: Int = 4) {
    Column(modifier.fillMaxWidth().loadingSemantics(), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        repeat(rows) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                SkeletonBlock(Modifier.size(40.dp).clip(CircleShape))
                SkeletonLines(Modifier.weight(1f), rows = 2)
            }
        }
    }
}

@Composable
internal fun SkeletonGrid(modifier: Modifier = Modifier, rows: Int = 2) {
    Column(modifier.fillMaxWidth().loadingSemantics(), verticalArrangement = Arrangement.spacedBy(3.dp)) {
        repeat(rows) {
            Row(horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                repeat(3) { SkeletonBlock(Modifier.weight(1f).aspectRatio(0.75f)) }
            }
        }
    }
}

@Composable
internal fun SkeletonProfile(modifier: Modifier = Modifier) {
    Column(modifier.fillMaxWidth().loadingSemantics(), verticalArrangement = Arrangement.spacedBy(22.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            SkeletonBlock(Modifier.size(82.dp).clip(CircleShape))
            SkeletonLines(Modifier.weight(1f))
        }
        SkeletonLines()
        SkeletonGrid()
    }
}

/** Media has its own loading lifecycle, independent of the JSON request. */
@Composable
internal fun DatabaseImage(
    model: Any?,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    contentScale: ContentScale = ContentScale.Fit
) {
    coil.compose.SubcomposeAsyncImage(
        model = model,
        contentDescription = contentDescription,
        modifier = modifier,
        contentScale = contentScale,
        loading = { SkeletonBlock(Modifier.fillMaxSize().loadingSemantics()) },
        error = {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Icon(Icons.Filled.BrokenImage, localizedText(R.string.ui_image_unavailable), tint = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    )
}
