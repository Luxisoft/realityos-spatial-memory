package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Test

class WorkspaceSelectionTest {
    @Test
    fun `cold start selects sole work group before querying records`() {
        assertEquals("hospital", queryWorkspaceId(listOf("home" to "home:nurse", "hospital" to "Hospital"), null, "home"))
    }

    @Test
    fun `multiple groups preserve explicit membership and discard removed group`() {
        val spaces = listOf("home" to "home:nurse", "hospital" to "Hospital", "institute" to "Institute")
        assertEquals("institute", queryWorkspaceId(spaces, "institute", "home"))
        assertEquals("home", queryWorkspaceId(spaces, "removed", "home"))
    }
}
