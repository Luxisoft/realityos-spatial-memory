package com.luxisoft.realityos

/** Paging window for AI chat: newest messages stay at the bottom, older ones load scrolling up. */
internal object ChatPagingPolicy {
    const val PAGE_SIZE = 10

    fun initialVisible(total: Int): Int = minOf(PAGE_SIZE, total)

    fun nextVisible(visible: Int, total: Int): Int = minOf(visible + PAGE_SIZE, total)

    fun hasMore(visible: Int, total: Int): Boolean = visible < total

    fun displayCount(visible: Int, total: Int): Int = minOf(visible, total)

    /** Newest-first slice for a reverse-layout list from a chronological history. */
    fun <T> displaySlice(chronological: List<T>, visible: Int): List<T> =
        chronological.takeLast(displayCount(visible, chronological.size)).asReversed()

    /** Near the bottom (newest) of a reverse-layout list: index 0 is the bottom. */
    fun isNearBottom(firstVisibleIndex: Int): Boolean = firstVisibleIndex <= 1
}
