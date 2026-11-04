package com.luxisoft.realityos

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

/** Shared request states retain the screen's typography, spacing and theme. */
@Composable
internal fun RequestFeedback(busy: Boolean, error: String?, retryLabel: String, onRetry: () -> Unit) {
    if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
    if (!error.isNullOrBlank()) {
        Text(error, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.error)
        OutlinedButton(onClick = onRetry, enabled = !busy) { Text(retryLabel) }
    }
}
