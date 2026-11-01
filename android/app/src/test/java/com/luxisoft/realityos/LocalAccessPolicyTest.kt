package com.luxisoft.realityos

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class LocalAccessPolicyTest {
    @Test fun localEntryRequiresDebugBuildAndServerConfirmation() {
        assertTrue(LocalAccessPolicy.canSkipFaceEntry(true, true, "http://localhost:8080/v1", true))
        assertFalse(LocalAccessPolicy.canSkipFaceEntry(false, true, "http://localhost:8080/v1", true))
        assertFalse(LocalAccessPolicy.canSkipFaceEntry(true, false, "http://localhost:8080/v1", true))
        assertFalse(LocalAccessPolicy.canSkipFaceEntry(true, true, "http://localhost:8080/v1", false))
    }

    @Test fun productionAndDisguisedRemoteHostsNeverBypassIdentity() {
        listOf(
            "https://realityos.luxisoft.com/v1",
            "http://server.example/v1",
            "http://localhost.example/v1",
            "http://localhost@server.example/v1",
            "http://localhost:8080/v1?remote=server",
            "not a URL"
        ).forEach { assertFalse(LocalAccessPolicy.canSkipFaceEntry(true, true, it, true)) }
    }

    @Test fun supportedLoopbackTransportsStayLocal() {
        listOf("localhost", "127.0.0.1", "10.0.2.2").forEach {
            assertTrue(LocalAccessPolicy.canSkipFaceEntry(true, true, "http://$it:8080/v1", true))
        }
    }
}
