package com.luxisoft.realityos

import java.io.ByteArrayOutputStream
import org.json.JSONArray
import org.json.JSONObject

internal const val STORAGE_BASE = "me/storage-connections"
internal fun storageRows(array: JSONArray): List<JSONObject> = (0 until array.length()).map { array.getJSONObject(it) }

/** Snapshot authentication per operation; a new account must never inherit a remote download. */
internal fun storageDownload(path: String, session: String): ByteArray {
    val connection = SocialSession.openJsonConnection(path)
    connection.instanceFollowRedirects = false
    connection.connectTimeout = 15000
    connection.readTimeout = 90000
    connection.setRequestProperty("Authorization", "Bearer $session")
    return try {
        check(connection.responseCode == 200) { "HTTP ${connection.responseCode}" }
        val maximum = 64 * 1024 * 1024
        check(connection.contentLengthLong <= maximum) { "Resource exceeds 64 MiB" }
        connection.inputStream.use { input ->
            val output = ByteArrayOutputStream()
            val buffer = ByteArray(32768)
            while (true) {
                val count = input.read(buffer)
                if (count < 0) break
                check(output.size() + count <= maximum) { "Resource exceeds 64 MiB" }
                output.write(buffer, 0, count)
            }
            output.toByteArray()
        }
    } finally {
        connection.disconnect()
    }
}

internal fun storageSupportsMedia(mime: String): Boolean = mime in setOf("image/jpeg", "image/png", "image/webp", "video/mp4")
internal fun storageSupportsCv(mime: String): Boolean = mime in setOf("application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

internal fun storageStatusLabel(status: String): String = localizedText(
    when (status) {
        "pending" -> R.string.storage_pending
        "downloading" -> R.string.storage_downloading
        "analyzing", "processing" -> R.string.storage_analyzing
        "published" -> R.string.storage_published
        "duplicate" -> R.string.storage_duplicate
        "failed" -> R.string.storage_failed
        "cancelled" -> R.string.storage_cancelled
        else -> R.string.storage_analyzing
    }
)
