package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Test

class GalleryWorkspaceLabelsTest {
    private val options = listOf(
        WorkspaceOption("w1", "Equipo Demo", "query"),
        WorkspaceOption("w2", "Taller RealityOS", "admin"),
    )

    @Test
    fun `blank selection shows every space at once`() {
        assertEquals(GalleryWorkspaceLabels.ALL_SPACES, GalleryWorkspaceLabels.selectedName(options, null))
    }

    @Test
    fun `selection shows the workspace name`() {
        assertEquals("Taller RealityOS", GalleryWorkspaceLabels.selectedName(options, "w2"))
    }

    @Test
    fun `unknown selection falls back to every space`() {
        assertEquals(GalleryWorkspaceLabels.ALL_SPACES, GalleryWorkspaceLabels.selectedName(options, "missing"))
    }
}
