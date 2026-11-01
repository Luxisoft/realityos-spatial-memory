package com.luxisoft.realityos

import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.runtime.*

/** Live turns force the newest bubble into view; loading history never does. */
internal class ChatScrollPolicy {
    var follow = true
        private set

    fun newTurn() {
        follow = true
    }
    fun manualDrag() {
        follow = false
    }
    fun settledAtBottom(atBottom: Boolean) {
        if (atBottom) follow = true
    }
}

@Composable
internal fun ChatAutoScroll(listState: LazyListState, newTurn: Long, working: Boolean) {
    val policy = remember(listState) { ChatScrollPolicy() }
    LaunchedEffect(listState) {
        listState.interactionSource.interactions.collect { interaction ->
            if (interaction is DragInteraction.Start) policy.manualDrag()
        }
    }
    LaunchedEffect(newTurn) {
        if (newTurn > 0) {
            policy.newTurn()
            // Wait for the new message and typing row to enter the lazy layout.
            withFrameNanos { }
            listState.scrollToItem(0)
        }
    }
    LaunchedEffect(listState, working) {
        snapshotFlow {
            val layout = listState.layoutInfo
            listOf(
                layout.viewportEndOffset - layout.viewportStartOffset,
                layout.totalItemsCount,
                layout.visibleItemsInfo.firstOrNull()?.size ?: 0,
                listState.isScrollInProgress,
                listState.firstVisibleItemIndex == 0 && listState.firstVisibleItemScrollOffset == 0
            )
        }.collect { layout ->
            if (!listState.isScrollInProgress) {
                policy.settledAtBottom(layout.last() == true)
                if (policy.follow && listState.layoutInfo.totalItemsCount > 0) listState.scrollToItem(0)
            }
        }
    }
}
