package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Test

class GalleryViewerUrlTest {
    @Test
    fun `viewer preserves detection labels while requesting full dimensions`() {
        val item = GalleryThumb("preview", "original", boxedUrl = "/v1/gallery/id/boxed?labels=yellow%20drill")
        assertEquals("/v1/gallery/id/boxed?labels=yellow%20drill&full_size=true", item.viewerUrl)
        assertEquals("/v1/gallery/id/boxed?labels=yellow%20drill", item.boxedUrl)
    }

    @Test
    fun `boxed URLs without filters work and fragments remain at the end`() {
        assertEquals("/v1/gallery/id/boxed?full_size=true", GalleryThumb("p", "m", boxedUrl = "/v1/gallery/id/boxed").viewerUrl)
        assertEquals("/v1/gallery/id/boxed?full_size=true#photo", GalleryThumb("p", "m", boxedUrl = "/v1/gallery/id/boxed#photo").viewerUrl)
    }

    @Test
    fun `unannotated matches still open the original media`() {
        assertEquals("original", GalleryThumb("preview", "original").viewerUrl)
    }
}
