package com.luxisoft.realityos

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class DrawerEdgePolicyTest {
    @Test
    fun `left edge engages in ltr`() {
        assertTrue(DrawerEdgePolicy.atEdge(x = 4f, width = 1080f, edgePx = 96f, isRtl = false))
        assertFalse(DrawerEdgePolicy.atEdge(x = 500f, width = 1080f, edgePx = 96f, isRtl = false))
    }

    @Test
    fun `right edge engages in rtl`() {
        assertTrue(DrawerEdgePolicy.atEdge(x = 1076f, width = 1080f, edgePx = 96f, isRtl = true))
        assertFalse(DrawerEdgePolicy.atEdge(x = 500f, width = 1080f, edgePx = 96f, isRtl = true))
    }

    @Test
    fun `opening needs slop toward content`() {
        assertTrue(DrawerEdgePolicy.shouldOpen(totalDx = 20f, slop = 16f, isRtl = false))
        assertFalse(DrawerEdgePolicy.shouldOpen(totalDx = 10f, slop = 16f, isRtl = false))
        assertFalse(DrawerEdgePolicy.shouldOpen(totalDx = -20f, slop = 16f, isRtl = false))
        assertTrue(DrawerEdgePolicy.shouldOpen(totalDx = -20f, slop = 16f, isRtl = true))
        assertFalse(DrawerEdgePolicy.shouldOpen(totalDx = 20f, slop = 16f, isRtl = true))
    }
}
