package com.luxisoft.realityos

import java.net.URI

/** Both the local build and the local server must authorize password-only entry. */
object LocalAccessPolicy {
    fun canSkipFaceEntry(debug: Boolean, localBuild: Boolean, baseUrl: String, serverConfirmed: Boolean): Boolean {
        if (!debug || !localBuild || !serverConfirmed) return false
        val uri = runCatching { URI(baseUrl) }.getOrNull() ?: return false
        return uri.scheme == "http" && uri.host in setOf("localhost", "127.0.0.1", "10.0.2.2") &&
            uri.userInfo == null && uri.query == null && uri.fragment == null
    }
}
