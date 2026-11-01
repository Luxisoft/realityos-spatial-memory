package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatPagingPolicyTest {
    @Test
    fun initialWindowIsLastTen() {
        assertEquals(10, ChatPagingPolicy.initialVisible(25))
        assertEquals(4, ChatPagingPolicy.initialVisible(4))
        assertEquals(0, ChatPagingPolicy.initialVisible(0))
    }

    @Test
    fun nextWindowGrowsByTenUpToTotal() {
        assertEquals(20, ChatPagingPolicy.nextVisible(10, 25))
        assertEquals(25, ChatPagingPolicy.nextVisible(20, 25))
        assertEquals(25, ChatPagingPolicy.nextVisible(25, 25))
    }

    @Test
    fun hasMoreOnlyBelowTotal() {
        assertTrue(ChatPagingPolicy.hasMore(10, 25))
        assertFalse(ChatPagingPolicy.hasMore(25, 25))
    }

    @Test
    fun displaySliceIsNewestFirst() {
        val history = (1..25).toList()
        assertEquals((25 downTo 16).toList(), ChatPagingPolicy.displaySlice(history, 10))
        assertEquals((25 downTo 1).toList(), ChatPagingPolicy.displaySlice(history, 40))
        assertEquals(emptyList<Int>(), ChatPagingPolicy.displaySlice(emptyList<Int>(), 10))
    }

    @Test
    fun nearBottomCoversFirstTwoPositions() {
        assertTrue(ChatPagingPolicy.isNearBottom(0))
        assertTrue(ChatPagingPolicy.isNearBottom(1))
        assertFalse(ChatPagingPolicy.isNearBottom(2))
    }
}
