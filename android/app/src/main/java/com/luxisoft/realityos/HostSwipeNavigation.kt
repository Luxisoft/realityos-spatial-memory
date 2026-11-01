package com.luxisoft.realityos

/**
 * Order of the swipeable host destinations. Profile and work gallery share
 * one horizontal pager; search opens as a bottom sheet instead.
 */
internal object HostSwipeNavigation {
    val pages = listOf(HostDestination.PROFILE, HostDestination.GALLERY)

    fun pageFor(destination: HostDestination): Int = pages.indexOf(destination)

    fun destinationFor(page: Int): HostDestination? = pages.getOrNull(page)
}
