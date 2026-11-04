package com.luxisoft.realityos

import androidx.annotation.DrawableRes
import androidx.compose.foundation.Image
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowForward
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

@Composable
internal fun EntryBrandHeader(action: @Composable RowScope.() -> Unit = {}) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 8.dp).heightIn(min = 48.dp), verticalAlignment = Alignment.CenterVertically) {
        AppBrandIcon(Modifier.size(26.dp))
        Spacer(Modifier.width(9.dp))
        Text("RealityOS", style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.weight(1f))
        action()
    }
}

@Composable
internal fun EntryScene(@DrawableRes image: Int, compact: Boolean = false) {
    Column {
        Image(
            painterResource(image),
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxWidth().aspectRatio(if (compact) 1.8f else 1.5f)
                .clip(MaterialTheme.shapes.large).border(1.dp, MaterialTheme.colorScheme.outlineVariant, MaterialTheme.shapes.large)
        )
        Spacer(Modifier.height(6.dp))
        Text(
            stringResource(R.string.explore_illustration),
            style = MaterialTheme.typography.bodySmall,
            color = AccountMuted,
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.End
        )
    }
}

@Composable
internal fun EntryPrimary(label: String, modifier: Modifier = Modifier, enabled: Boolean = true, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        enabled = enabled,
        shape = MaterialTheme.shapes.medium,
        colors = ButtonDefaults.buttonColors(contentColor = Color(0xFF17211F)),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 16.dp),
        modifier = modifier.heightIn(min = 56.dp)
    ) {
        Text(label, style = MaterialTheme.typography.labelLarge, textAlign = TextAlign.Center, modifier = Modifier.weight(1f))
        Spacer(Modifier.width(8.dp))
        Icon(Icons.AutoMirrored.Outlined.ArrowForward, null, Modifier.size(20.dp))
    }
}
