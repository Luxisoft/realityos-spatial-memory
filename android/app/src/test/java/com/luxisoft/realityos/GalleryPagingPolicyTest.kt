package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class GalleryPagingPolicyTest {
    @Test
    fun `idle grid with more content loads the next page`() {
        assertTrue(GalleryPagingPolicy.shouldLoadMore(loading = false, endReached = false))
    }

    @Test
    fun `no new request starts while one is already in flight`() {
        assertFalse(GalleryPagingPolicy.shouldLoadMore(loading = true, endReached = false))
    }

    @Test
    fun `no new request starts once the end of content is reached`() {
        assertFalse(GalleryPagingPolicy.shouldLoadMore(loading = false, endReached = true))
    }

    @Test
    fun `full page keeps paging open`() {
        assertFalse(GalleryPagingPolicy.isEndOfContent(GalleryPagingPolicy.pageSize))
    }

    @Test
    fun `short page ends paging`() {
        assertTrue(GalleryPagingPolicy.isEndOfContent(GalleryPagingPolicy.pageSize - 1))
    }

    @Test
    fun `empty first page ends paging instead of looping`() {
        assertTrue(GalleryPagingPolicy.isEndOfContent(0))
    }

    @Test
    fun `offsets advance one full page at a time`() {
        assertEquals(GalleryPagingPolicy.pageSize, GalleryPagingPolicy.nextOffset(0))
        assertEquals(
            2 * GalleryPagingPolicy.pageSize,
            GalleryPagingPolicy.nextOffset(GalleryPagingPolicy.pageSize),
        )
    }
}
