package com.luxisoft.realityos

/**
 * Decides when a touch opens the host drawer instead of paging: only drags
 * that start on the drawer's edge and travel toward the content. Anything
 * else belongs to the pager.
 */
internal object DrawerEdgePolicy {
    fun atEdge(x: Float, width: Float, edgePx: Float, isRtl: Boolean): Boolean =
        if (isRtl) x > width - edgePx else x < edgePx

    fun shouldOpen(totalDx: Float, slop: Float, isRtl: Boolean): Boolean =
        if (isRtl) totalDx < -slop else totalDx > slop
}
