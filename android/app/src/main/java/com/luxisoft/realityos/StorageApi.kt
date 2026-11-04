package com.luxisoft.realityos

import org.json.JSONArray
import org.json.JSONObject

internal const val STORAGE_BASE = "me/storage-connections"
internal fun storageRows(array: JSONArray): List<JSONObject> = (0 until array.length()).map { array.getJSONObject(it) }

/** Snapshot authentication per operation; a new account must never inherit a remote download. */
internal fun storageDownload(path: String, session: Long): ByteArray = SocialSession.download(path, session, 64 * 1024 * 1024)

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
