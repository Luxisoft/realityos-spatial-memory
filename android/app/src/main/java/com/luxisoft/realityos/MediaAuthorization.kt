package com.luxisoft.realityos

import coil.request.ImageRequest
import java.net.URI

internal fun mediaAuthorization(url: String, token: String?, apiBaseUrl: String = BuildConfig.DEFAULT_REALITYOS_API_BASE_URL): Map<String, String> {
    if (token.isNullOrBlank()) return emptyMap()
    return runCatching {
        val target = URI(url)
        val api = URI(apiBaseUrl)
        fun port(uri: URI): Int = if (uri.port >= 0) uri.port else if (uri.scheme.equals("https", true)) 443 else 80
        if (target.host != null && target.scheme.equals(api.scheme, true) && target.host.equals(api.host, true) && port(target) == port(api)) {
            mapOf("Authorization" to "Bearer $token")
        } else emptyMap()
    }.getOrDefault(emptyMap())
}

internal fun ImageRequest.Builder.authorizeMedia(url: String, token: String? = SocialSession.token): ImageRequest.Builder = apply {
    mediaAuthorization(url, token).forEach { (key, value) -> addHeader(key, value) }
}
