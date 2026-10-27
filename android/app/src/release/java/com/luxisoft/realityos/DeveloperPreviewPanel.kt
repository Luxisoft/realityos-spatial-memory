package com.luxisoft.realityos

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

/** Release builds never expose developer-only simulation controls. */
@Composable
fun DeveloperPreviewPanel(
    viewModel: RealityViewModel,
    enabled: Boolean,
    modifier: Modifier = Modifier,
) = Unit
