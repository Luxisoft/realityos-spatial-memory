package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class HostSwipeNavigationTest {
    @Test
    fun `swipe order is profile then work`() {
        assertEquals(
            listOf(HostDestination.PROFILE, HostDestination.GALLERY),
            HostSwipeNavigation.pages,
        )
    }

    @Test
    fun `each swipe destination maps to its page`() {
        assertEquals(0, HostSwipeNavigation.pageFor(HostDestination.PROFILE))
        assertEquals(1, HostSwipeNavigation.pageFor(HostDestination.GALLERY))
    }

    @Test
    fun `destinations outside the pager have no page`() {
        assertEquals(-1, HostSwipeNavigation.pageFor(HostDestination.META_DISPLAY))
        assertEquals(-1, HostSwipeNavigation.pageFor(HostDestination.LANGUAGE))
    }

    @Test
    fun `pages map back to destinations with bounds`() {
        assertEquals(HostDestination.PROFILE, HostSwipeNavigation.destinationFor(0))
        assertEquals(HostDestination.GALLERY, HostSwipeNavigation.destinationFor(1))
        assertNull(HostSwipeNavigation.destinationFor(-1))
        assertNull(HostSwipeNavigation.destinationFor(2))
    }
}
