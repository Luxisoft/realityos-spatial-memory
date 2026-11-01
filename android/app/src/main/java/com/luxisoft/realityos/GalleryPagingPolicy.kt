package com.luxisoft.realityos

/**
 * Decides when the gallery grid may request another page. Only one request
 * flies at a time, a short page permanently ends paging for the current
 * filter, and offsets always advance one full server page so the footer can
 * only fire again after new items arrive and the user scrolls back down.
 */
internal object GalleryPagingPolicy {
    const val pageSize = 30

    fun shouldLoadMore(loading: Boolean, endReached: Boolean): Boolean =
        !loading && !endReached

    fun isEndOfContent(loaded: Int): Boolean = loaded < pageSize

    fun nextOffset(offset: Int): Int = offset + pageSize
}
