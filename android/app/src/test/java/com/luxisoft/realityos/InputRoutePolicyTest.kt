package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class InputRoutePolicyTest {
    @Test
    fun `automatic reconnection to a mock keeps capture and voice on the phone`() {
        val selected = select(listOf("mock-old"), null)
        assertEquals("mock-old", selected)
        assertEquals(InputRoute.PHONE, route(checkNotNull(selected)))
    }

    @Test
    fun `physical glasses win even when the simulator was explicitly requested`() {
        val selected = select(listOf("mock-old", "physical"), "mock-old")
        assertEquals("physical", selected)
        assertEquals(InputRoute.WEARABLE, route(checkNotNull(selected)))
    }

    @Test fun `explicit physical identifiers use wearable sensors too`() {
        assertEquals(InputRoute.WEARABLE, route(checkNotNull(select(listOf("physical"), "physical"))))
    }

    @Test fun `stale or disconnected physical identifiers cannot select wearable sensors`() {
        assertNull(select(emptyList(), "physical"))
        val selected = checkNotNull(select(listOf("mock-new"), "physical"))
        assertEquals("mock-new", selected)
        assertEquals(InputRoute.PHONE, route(selected))
    }

    @Test fun `renderer restarts prefer the requested eligible mock`() {
        assertEquals("mock-new", select(listOf("mock-old", "mock-new"), "mock-new"))
        assertEquals("mock-new", select(listOf("mock-new"), "mock-old"))
    }

    private fun select(eligible: List<String>, requested: String?): String? = InputRoutePolicy.selectDevice(eligible, requested) { it.startsWith("mock-") }

    private fun route(identifier: String) = InputRoutePolicy.forConnectedDevice(identifier.startsWith("mock-"))
}
