package com.luxisoft.realityos

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.time.Instant
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

internal data class DisplayImageLink(val url: String, val expiresAt: Instant) {
    companion object {
        fun decode(value: JSONObject): DisplayImageLink = DisplayImageLink(
            value.getString("url").also { require(it.isNotBlank()) },
            Instant.parse(value.getString("expires_at"))
        )
    }
}

internal data class LoadedDisplayImage(val link: DisplayImageLink, val bitmap: Bitmap)

/** Resolve signed images on the host; DAT receives pixels and their dimensions. */
internal class DisplayResultImages(
    private val requestLink: (JSONObject) -> JSONObject = {
        JSONObject(SocialSession.request("display/media-links", it))
    },
    private val openConnection: (String) -> HttpURLConnection = {
        URL(it).openConnection() as HttpURLConnection
    },
    private val now: () -> Instant = Instant::now
) {
    suspend fun match(kind: String, resourceId: String, labels: List<String> = emptyList()): Bitmap {
        require(resourceId.isNotBlank()) { "Missing Display image resource" }
        val link = withContext(Dispatchers.IO) {
            DisplayImageLink.decode(
                requestLink(JSONObject().put("kind", kind).put("resource_id", resourceId).put("labels", JSONArray(labels)))
            )
        }
        return load(link)
    }

    fun valid(link: DisplayImageLink): Boolean = now().isBefore(link.expiresAt)

    fun valid(image: LoadedDisplayImage): Boolean = valid(image.link)

    suspend fun load(link: DisplayImageLink): Bitmap = withContext(Dispatchers.IO) {
        check(now().isBefore(link.expiresAt)) { "Display image link expired" }
        val url = URL(authorizedMediaUrl(link.url))
        require(
            url.protocol == "https" ||
                (BuildConfig.LOCAL_DEVELOPMENT && url.protocol == "http" && url.host in setOf("localhost", "127.0.0.1", "10.0.2.2"))
        )
        val connection = openConnection(url.toString())
        try {
            connection.connectTimeout = 5000
            connection.readTimeout = 10000
            connection.instanceFollowRedirects = false
            // Capability URL only: never forward the account token to image hosts.
            check(connection.responseCode == 200) { "Display image unavailable" }
            check(connection.contentType?.substringBefore(';') in setOf("image/jpeg", "image/png", "image/webp")) { "Invalid Display image type" }
            val bytes = connection.inputStream.use { input ->
                val output = ByteArrayOutputStream()
                val buffer = ByteArray(16384)
                while (true) {
                    currentCoroutineContext().ensureActive()
                    val count = input.read(buffer)
                    if (count < 0) break
                    check(output.size() + count <= MAX_BYTES) { "Invalid Display image size" }
                    output.write(buffer, 0, count)
                }
                output.toByteArray()
            }
            currentCoroutineContext().ensureActive()
            check(bytes.isNotEmpty() && bytes.size <= MAX_BYTES) { "Invalid Display image size" }
            val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
            check(bounds.outWidth in 1..600 && bounds.outHeight in 1..600) { "Invalid Display image dimensions" }
            checkNotNull(BitmapFactory.decodeByteArray(bytes, 0, bytes.size)) { "Invalid Display image" }
                .also { check(now().isBefore(link.expiresAt)) { "Display image link expired" } }
        } finally {
            connection.disconnect()
        }
    }

    private companion object {
        const val MAX_BYTES = 4 * 1024 * 1024
    }
}
