package com.luxisoft.realityos

import androidx.activity.compose.BackHandler
import androidx.compose.animation.*
import androidx.compose.animation.core.MutableTransitionState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp

@Composable
internal fun RootPanel(onClose: () -> Unit, content: @Composable () -> Unit) {
    val transition = remember { MutableTransitionState(false).apply { targetState = true } }
    var closing by remember { mutableStateOf(false) }
    val close = {
        closing = true
        transition.targetState = false
    }
    BackHandler { close() }
    LaunchedEffect(transition.isIdle, transition.currentState, closing) {
        if (closing && transition.isIdle && !transition.currentState) onClose()
    }
    Box(Modifier.fillMaxSize().imePadding()) {
        AnimatedVisibility(visibleState = transition, enter = fadeIn(), exit = fadeOut()) {
            Box(Modifier.fillMaxSize().background(Color.Black.copy(alpha = .45f)).clickable(onClick = close))
        }
        AnimatedVisibility(visibleState = transition, enter = slideInVertically { it }, exit = slideOutVertically { it }, modifier = Modifier.align(Alignment.BottomCenter)) {
            Surface(Modifier.fillMaxSize().testTag("root-panel")) {
                Column(Modifier.fillMaxSize().safeDrawingPadding()) {
                    Row(
                        Modifier.fillMaxWidth().pointerInput(Unit) {
                            var distance = 0f
                            detectVerticalDragGestures(onDragStart = { distance = 0f }, onVerticalDrag = { change, amount ->
                                distance += amount
                                change.consume()
                            }, onDragEnd = { if (distance > 64.dp.toPx()) close() })
                        },
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Spacer(Modifier.weight(1f))
                        Box(Modifier.size(32.dp, 4.dp).background(MaterialTheme.colorScheme.outline, RoundedCornerShape(4.dp)))
                        Spacer(Modifier.weight(1f))
                        IconButton(onClick = close) { Icon(Icons.Default.Close, localizedText(R.string.ui_close)) }
                    }
                    Box(Modifier.weight(1f)) { content() }
                }
            }
        }
    }
}
