package com.luxisoft.realityos

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp

/** Release builds never package or expose Mock Device Kit simulation controls. */
@Composable
fun DeveloperPreviewStage(
    viewModel: RealityViewModel,
    enabled: Boolean,
    modifier: Modifier = Modifier,
) = Unit

/** Release builds expose only physical-session guidance in the shared drawer. */
@Composable
fun PreviewControlPanel(
    state: RealityUiState,
    viewModel: RealityViewModel,
    onOpenGlasses: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(
            if (state.wearable.sessionActive) {
                stringResource(R.string.preview_live_title)
            } else {
                stringResource(R.string.preview_waiting_title)
            },
            style = MaterialTheme.typography.titleMedium,
        )
        Text(
            if (state.wearable.sessionActive) {
                stringResource(R.string.preview_live_body)
            } else {
                stringResource(R.string.preview_waiting_body)
            },
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        if (!state.wearable.sessionActive) {
            Button(onClick = onOpenGlasses, modifier = Modifier.fillMaxWidth()) {
                Text(stringResource(R.string.preview_open_glasses))
            }
        }
    }
}
