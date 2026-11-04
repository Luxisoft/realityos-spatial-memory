package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Test

class WorkspaceSelectionTest {
    @Test
    fun `cold start selects sole work group before querying records`() {
        assertEquals("police", queryWorkspaceId(listOf("home" to "home:alex", "police" to "Police"), null, "home"))
    }

    @Test
    fun `multiple groups preserve explicit membership and discard removed group`() {
        val spaces = listOf("home" to "home:alex", "police" to "Police", "meta" to "Meta")
        assertEquals("meta", queryWorkspaceId(spaces, "meta", "home"))
        assertEquals("home", queryWorkspaceId(spaces, "removed", "home"))
    }
}
