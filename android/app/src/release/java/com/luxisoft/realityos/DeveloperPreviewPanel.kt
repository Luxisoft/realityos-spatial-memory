package com.luxisoft.realityos

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

/** Release builds never package or expose Mock Device Kit simulation controls. */
@Composable
fun DeveloperPreviewStage(
    viewModel: RealityViewModel,
    enabled: Boolean,
    modifier: Modifier = Modifier,
) = Unit

@Composable
fun DeveloperLabControls(
    viewModel: RealityViewModel,
    modifier: Modifier = Modifier,
) = Unit
